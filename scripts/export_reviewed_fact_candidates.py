#!/usr/bin/env python3
"""Export exact source spans for human review; this never creates approved facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from collections.abc import Callable, Iterator, Sequence
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

_SENTENCE = re.compile(r"[^.!?。！？]+(?:[.!?。！？]+|$)")


def iter_candidate_rows(connection: Any, revision_id: str) -> Iterator[dict[str, object]]:
    with connection.cursor(name="onmaru_fact_review_queue") as cursor:
        cursor.execute(
            """SELECT c.chunk_id, c.start_offset, c.chunk_text,
                      d.source_id AS place_id, d.normalized_text
                 FROM ai.chunks c
                 JOIN ai.documents d USING (revision_id,document_id)
                 JOIN ai.corpus_revisions r USING (revision_id)
                WHERE c.revision_id=%s AND r.state='ACTIVE'
                  AND d.eligibility_status='PUBLIC'
                  AND NOT EXISTS (
                      SELECT 1 FROM ai.place_revocations p WHERE p.place_id=d.place_id
                  )
                  AND NOT EXISTS (
                      SELECT 1 FROM ai.source_revocations s
                       WHERE (s.source_type,s.source_id,s.source_revision)=
                             (d.source_type,d.source_id,d.source_revision)
                  )
                ORDER BY d.source_id,c.ordinal""",
            (revision_id,),
        )
        while chunks := cursor.fetchmany(200):
            for chunk in chunks:
                chunk_start = int(chunk["start_offset"])
                text = str(chunk["chunk_text"])
                document_text = str(chunk["normalized_text"])
                if document_text[chunk_start : chunk_start + len(text)] != text:
                    raise ValueError("source chunk offset failed exact-text validation")
                for match in _SENTENCE.finditer(text):
                    raw_candidate = match.group(0)
                    candidate = raw_candidate.strip()
                    if not candidate:
                        continue
                    start = chunk_start + match.start() + len(raw_candidate) - len(
                        raw_candidate.lstrip()
                    )
                    end = start + len(candidate)
                    if document_text[start:end] != candidate:
                        raise ValueError("candidate span failed exact-text validation")
                    candidate_id = hashlib.sha256(
                        f"{revision_id}:{chunk['chunk_id']}:{start}:{end}".encode()
                    ).hexdigest()[:24]
                    yield {
                        "revisionId": revision_id,
                        "candidateId": f"fc-{candidate_id}",
                        "chunkId": str(chunk["chunk_id"]),
                        "placeId": str(chunk["place_id"]),
                        "startOffset": start,
                        "endOffset": end,
                        "candidateText": candidate,
                        "reviewStatus": "NEEDS_HUMAN_REVIEW",
                    }


def export_candidates(
    dsn: str,
    revision_id: str,
    output: Path,
    *,
    connection_factory: Callable[..., Any] = psycopg.connect,
) -> int:
    count = 0
    with connection_factory(dsn, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        with output.open("w", encoding="utf-8") as stream:
            for row in iter_candidate_rows(connection, revision_id):
                stream.write(json.dumps(row, ensure_ascii=False) + "\n")
                count += 1
    return count


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision-id", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args(argv)
    dsn = os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn or not dsn.strip():
        print("Set ONMARU_AI_DB_DSN; no output was generated", file=sys.stderr)
        return 2
    try:
        count = export_candidates(dsn, args.revision_id, args.output)
    except Exception as exc:
        print(f"Candidate export failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    print(f"Exported {count} human-review candidates to {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
