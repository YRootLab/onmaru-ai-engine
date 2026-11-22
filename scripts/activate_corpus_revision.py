#!/usr/bin/env python3
"""Validate a staged corpus revision and explicitly activate it after operator confirmation."""

from __future__ import annotations

import argparse
import logging
import os
import sys
from collections.abc import Callable, Sequence
from typing import Any

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.embedding import E5_SMALL_ONNX_INT8_384
from onmaru_ai.storage.postgres import PostgresCorpusStore

logger = logging.getLogger("activate_corpus_revision")


def activate_candidate_revision(
    connection: Any,
    store: Any,
    revision_id: str,
    *,
    confirm_revision: str,
    apply: bool,
) -> dict[str, Any]:
    if confirm_revision != revision_id:
        raise ValueError("confirmation must exactly match the revision ID")
    row = connection.execute(
        """SELECT r.revision_id, r.manifest_hash, r.state, r.gc_state,
                  r.embedding_profile_id, r.document_count, r.chunk_count, r.embedding_count,
                  a.revision_id AS active_revision, a.revocation_sequence AS active_sequence,
                  s.sequence AS current_sequence,
                  (s.heartbeat_at IS NOT NULL AND s.heartbeat_at >=
                   clock_timestamp() - interval '60 seconds') AS heartbeat_healthy,
                  (SELECT count(*) FROM ai.documents d WHERE d.revision_id=r.revision_id)
                    AS actual_document_count,
                  (SELECT count(*) FROM ai.chunks c WHERE c.revision_id=r.revision_id)
                    AS actual_chunk_count,
                  (SELECT count(*) FROM ai.embeddings e WHERE e.revision_id=r.revision_id
                    AND e.embedding_profile_id=r.embedding_profile_id) AS actual_embedding_count
             FROM ai.corpus_revisions r
             JOIN ai.active_corpus a ON a.id=1
             JOIN ai.revocation_state s ON s.id=1
            WHERE r.revision_id=%s""",
        (revision_id,),
    ).fetchone()
    if row is None:
        raise ValueError("staged corpus revision was not found")
    if (
        row["revision_id"] != revision_id
        or row["state"] not in {"BUILDING", "VALIDATED"}
        or row["gc_state"] != "LIVE"
        or row["embedding_profile_id"] != E5_SMALL_ONNX_INT8_384.profile_id
        or not row["heartbeat_healthy"]
        or row["active_sequence"] != row["current_sequence"]
        or row["document_count"] <= 0
        or row["chunk_count"] <= 0
        or row["embedding_count"] != row["chunk_count"]
        or row["actual_document_count"] != row["document_count"]
        or row["actual_chunk_count"] != row["chunk_count"]
        or row["actual_embedding_count"] != row["embedding_count"]
    ):
        raise ValueError("staged corpus revision failed profile, count, or revocation checks")
    if apply:
        store.activate(
            revision_id,
            manifest_hash=row["manifest_hash"],
            expected_active=row["active_revision"],
            expected_revocation_sequence=row["current_sequence"],
        )
    return dict(row)


def main(
    argv: Sequence[str] | None = None,
    *,
    connection_factory: Callable[..., Any] = psycopg.connect,
    store_factory: Callable[[str], Any] = PostgresCorpusStore,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision-id", required=True, help="Staged corpus revision to validate.")
    parser.add_argument(
        "--confirm-revision",
        required=True,
        help="Repeat the exact revision ID to confirm the requested target.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Activate after validation (default: read-only validation).",
    )
    args = parser.parse_args(argv)
    dsn = os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn or not dsn.strip():
        logger.error("Set ONMARU_AI_DB_DSN; no changes were made")
        return 2

    try:
        with connection_factory(dsn, row_factory=dict_row) as connection:
            if not args.apply:
                connection.execute("SET TRANSACTION READ ONLY")
            metadata = activate_candidate_revision(
                connection,
                store_factory(dsn),
                args.revision_id,
                confirm_revision=args.confirm_revision,
                apply=args.apply,
            )
    except Exception as exc:
        logger.error(
            "Corpus activation check failed (%s); no activation completed",
            type(exc).__name__,
        )
        return 1

    action = "activated" if args.apply else "validated (read-only)"
    logger.info(
        "Revision %s %s: profile=%s documents=%s chunks=%s embeddings=%s",
        args.revision_id,
        action,
        metadata["embedding_profile_id"],
        metadata["actual_document_count"],
        metadata["actual_chunk_count"],
        metadata["actual_embedding_count"],
    )
    return 0


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
    sys.exit(main())
