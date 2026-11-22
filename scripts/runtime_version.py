"""Print the active AI Engine runtime versions for Spring configuration sync."""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict, dataclass

import psycopg
from psycopg.rows import dict_row


@dataclass(frozen=True)
class RuntimeVersions:
    corpus_revision: str
    config_hash: str
    question_dictionary_version: str
    source_revocation_sequence: int

    def as_environment(self) -> dict[str, str]:
        return {
            "CORPUS_REVISION": self.corpus_revision,
            "CONFIG_HASH": self.config_hash,
            "QUESTION_DICTIONARY_VERSION": self.question_dictionary_version,
            "SOURCE_REVOCATION_SEQUENCE": str(self.source_revocation_sequence),
        }


class RuntimeVersionUnavailable(RuntimeError):
    """Raised when the active corpus or revocation gate is not ready to sync."""


def read_runtime_versions(dsn: str) -> RuntimeVersions:
    with psycopg.connect(dsn, row_factory=dict_row) as connection:
        connection.execute("SET TRANSACTION READ ONLY")
        row = connection.execute(
            """SELECT r.revision_id, r.config_hash, r.dictionary_version,
                      s.sequence, a.revocation_sequence,
                      s.source_snapshot_watermark,
                      s.heartbeat_at >= clock_timestamp() - interval '60 seconds'
                        AND s.heartbeat_at <= clock_timestamp() AS heartbeat_fresh
               FROM ai.active_corpus a
               JOIN ai.corpus_revisions r ON r.revision_id=a.revision_id
               JOIN ai.revocation_state s ON s.id=1
               WHERE a.id=1 AND r.state='ACTIVE'"""
        ).fetchone()
    if row is None:
        raise RuntimeVersionUnavailable("active_corpus_missing")
    if row["source_snapshot_watermark"] is None:
        raise RuntimeVersionUnavailable("source_snapshot_not_installed")
    if not row["heartbeat_fresh"]:
        raise RuntimeVersionUnavailable("source_revocation_heartbeat_stale")
    if int(row["sequence"]) != int(row["revocation_sequence"]):
        raise RuntimeVersionUnavailable("source_revocation_sequence_mismatch")
    return RuntimeVersions(
        corpus_revision=str(row["revision_id"]),
        config_hash=str(row["config_hash"]),
        question_dictionary_version=str(row["dictionary_version"]),
        source_revocation_sequence=int(row["sequence"]),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dsn", help="read-only AI database DSN; defaults to ONMARU_AI_DB_DSN")
    parser.add_argument("--format", choices=("dotenv", "json"), default="dotenv")
    args = parser.parse_args()
    dsn = (
        args.dsn or os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL") or ""
    ).strip()
    if not dsn:
        print("runtime version unavailable: database DSN is required", file=sys.stderr)
        return 2
    try:
        versions = read_runtime_versions(dsn)
    except (psycopg.Error, RuntimeVersionUnavailable) as error:
        reason = (
            str(error) if isinstance(error, RuntimeVersionUnavailable) else "database_query_failed"
        )
        print(f"runtime version unavailable: {reason}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(asdict(versions), ensure_ascii=False, sort_keys=True))
    else:
        for key, value in versions.as_environment().items():
            print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
