#!/usr/bin/env python3
"""Print the active corpus versions and health needed by Spring configuration."""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections.abc import Callable, Sequence
from typing import Any, cast

import psycopg
from psycopg.rows import dict_row


def read_active_versions(connection: Any) -> dict[str, object]:
    connection.execute("SET TRANSACTION READ ONLY")
    row = connection.execute(
        """SELECT r.revision_id, r.config_hash, r.dictionary_version,
                  a.revocation_sequence, s.sequence AS current_sequence,
                  s.source_snapshot_watermark,
                  s.heartbeat_at,
                  s.heartbeat_at IS NOT NULL AND s.heartbeat_at >=
                    clock_timestamp()-interval '60 seconds' AND
                    s.heartbeat_at <= clock_timestamp() AS heartbeat_healthy,
                  (SELECT count(*) FROM ai.reviewed_facts f
                    WHERE f.revision_id=r.revision_id AND f.review_status='APPROVED')
                    AS approved_fact_count
             FROM ai.active_corpus a
             JOIN ai.corpus_revisions r USING (revision_id)
             JOIN ai.revocation_state s ON s.id=a.id
            WHERE a.id=1 AND r.state='ACTIVE' AND r.gc_state='LIVE'"""
    ).fetchone()
    if row is None:
        raise ValueError("no active corpus revision")
    if row["source_snapshot_watermark"] is None:
        raise ValueError("source revocation snapshot is not installed")
    if row["revocation_sequence"] != row["current_sequence"]:
        raise ValueError("active corpus revocation sequence is stale")
    return dict(row)


def main(
    argv: Sequence[str] | None = None,
    *,
    connection_factory: Callable[..., Any] = psycopg.connect,
) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of shell values.")
    args = parser.parse_args(argv)
    dsn = os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn or not dsn.strip():
        print("Set ONMARU_AI_DB_DSN; no output was generated", file=sys.stderr)
        return 2
    try:
        with connection_factory(dsn, row_factory=dict_row) as connection:
            values = read_active_versions(connection)
    except Exception as exc:
        print(f"Version check failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(values, default=str, ensure_ascii=False))
        return 0
    heartbeat_healthy = cast(bool, values["heartbeat_healthy"])
    approved_fact_count = int(cast(str, values["approved_fact_count"]))
    if not heartbeat_healthy or approved_fact_count == 0:
        print("Active corpus is not ready: heartbeat stale or no reviewed facts", file=sys.stderr)
        return 1
    print(f"CORPUS_REVISION={values['revision_id']}")
    print(f"CONFIG_HASH={values['config_hash']}")
    print(f"QUESTION_DICTIONARY_VERSION={values['dictionary_version']}")
    print(f"SOURCE_REVOCATION_SEQUENCE={values['revocation_sequence']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
