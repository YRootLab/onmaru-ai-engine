#!/usr/bin/env python3
"""Stage a previously generated local corpus spool; writes require explicit --apply."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from onmaru_ai.corpus.staging_spool import CorpusStagingSpool
from onmaru_ai.storage.postgres import PostgresCorpusStore


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision-id", required=True)
    parser.add_argument("--spool-path", type=Path, required=True)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Write the validated spool to PostgreSQL.",
    )
    args = parser.parse_args(argv)
    if not args.spool_path.is_file():
        print("Spool file does not exist", file=sys.stderr)
        return 2
    with CorpusStagingSpool(args.spool_path, args.revision_id) as spool:
        revision = spool.revision()
        documents, chunks, embeddings = spool.counts()
        if not documents or documents != chunks or chunks != embeddings:
            print("Spool counts are empty or inconsistent", file=sys.stderr)
            return 2
        if revision.embedding_profile_id != "multilingual-e5-small-384-onnx-int8@614241f622f5":
            print("Spool embedding profile is not the pinned ONNX INT8 profile", file=sys.stderr)
            return 2
        print(
            f"revision={revision.revision_id} profile={revision.embedding_profile_id} "
            f"documents={documents} chunks={chunks} embeddings={embeddings} "
            f"manifest_hash={revision.manifest_hash}"
        )
        if not args.apply:
            print("Read-only validation only; pass --apply to stage this revision")
            return 0
        dsn = os.environ.get("ONMARU_AI_DB_DSN", "").strip()
        if not dsn:
            print("Set ONMARU_AI_DB_DSN to the AI corpus-writer DSN", file=sys.stderr)
            return 2
        inserted = PostgresCorpusStore(dsn).stage_spool(spool)
        print(f"stage_inserted={inserted}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
