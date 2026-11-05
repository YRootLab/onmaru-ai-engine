from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID, uuid4

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.storage.postgres import CORPUS_WRITE_LOCK, CorpusStorageError


@dataclass(frozen=True)
class GcResult:
    run_id: UUID
    deleted_revisions: tuple[str, ...]
    deleted_rows: int


class CorpusGarbageCollector:
    """Bounded revision collector with durable per-stage checkpoints."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def run(self, *, actor: str, max_revisions: int = 2, batch_size: int = 500) -> GcResult:
        if max_revisions < 1 or batch_size < 1:
            raise ValueError("GC bounds must be positive")
        run_id = uuid4()
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute(
                "INSERT INTO ai.gc_runs (run_id,state,actor) VALUES (%s,'RUNNING',%s)",
                (run_id, actor),
            )
            candidates = tuple(
                row["revision_id"]
                for row in connection.execute(
                    """SELECT r.revision_id FROM ai.corpus_revisions r
                    WHERE r.state IN ('REJECTED','VALIDATED','BUILDING','RETIRED')
                      AND r.expires_at IS NOT NULL AND r.expires_at <= now()
                      AND NOT EXISTS (SELECT 1 FROM ai.active_corpus a
                                      WHERE a.revision_id=r.revision_id)
                      AND NOT EXISTS (SELECT 1 FROM ai.rollback_corpus b
                                      WHERE b.revision_id=r.revision_id AND b.expires_at>now())
                      AND NOT EXISTS (SELECT 1 FROM ai.revision_holds h
                                      WHERE h.revision_id=r.revision_id AND h.expires_at>now())
                      AND NOT EXISTS (SELECT 1 FROM ai.corpus_sync_runs s
                                      WHERE s.revision_id=r.revision_id AND s.state='RUNNING'
                                        AND s.lease_expires_at>now())
                      AND NOT EXISTS (SELECT 1 FROM ai.revision_read_leases l
                                      WHERE l.revision_id=r.revision_id AND l.expires_at>now())
                    ORDER BY r.expires_at, r.revision_id LIMIT %s""",
                    (max_revisions,),
                )
            )
        deleted: list[str] = []
        total = 0
        try:
            for revision_id in candidates:
                total += self._delete_revision(run_id, revision_id, batch_size)
                deleted.append(revision_id)
            with psycopg.connect(self._dsn) as connection:
                connection.execute(
                    "UPDATE ai.gc_runs SET state='SUCCEEDED', finished_at=now() WHERE run_id=%s",
                    (run_id,),
                )
        except Exception:
            with psycopg.connect(self._dsn) as connection:
                connection.execute(
                    "UPDATE ai.gc_runs SET state='FAILED', finished_at=now() WHERE run_id=%s",
                    (run_id,),
                )
            raise
        return GcResult(run_id, tuple(deleted), total)

    def _delete_revision(self, run_id: UUID, revision_id: str, batch_size: int) -> int:
        deleted = 0
        deleted_bytes = 0
        manifest_hash = ""
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            row = connection.execute(
                "SELECT manifest_hash FROM ai.corpus_revisions WHERE revision_id=%s FOR UPDATE",
                (revision_id,),
            ).fetchone()
            if row is None:
                return 0
            manifest_hash = str(row["manifest_hash"])
            for table in ("embeddings", "chunks", "documents"):
                size = connection.execute(
                    f"SELECT COALESCE(sum(pg_column_size(t)),0) AS bytes "
                    f"FROM ai.{table} t WHERE revision_id=%s",
                    (revision_id,),
                ).fetchone()
                if size is None:
                    raise CorpusStorageError("GC_SIZE_ESTIMATE_FAILED")
                deleted_bytes += int(size["bytes"])
            if self._is_protected(connection, revision_id):
                raise CorpusStorageError("GC_REVISION_BECAME_PROTECTED")
            connection.execute(
                "UPDATE ai.corpus_revisions SET gc_state='DELETING' WHERE revision_id=%s",
                (revision_id,),
            )
            self._checkpoint(connection, run_id, revision_id, "EMBEDDINGS", deleted)
        for table, stage in (
            ("embeddings", "CHUNKS"),
            ("chunks", "DOCUMENTS"),
            ("documents", "REVISION"),
        ):
            while True:
                with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
                    connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
                    if self._is_protected(connection, revision_id):
                        raise CorpusStorageError("GC_REVISION_BECAME_PROTECTED")
                    cursor = connection.execute(
                        f"DELETE FROM ai.{table} WHERE ctid IN (SELECT ctid FROM ai.{table} "
                        "WHERE revision_id=%s LIMIT %s)",
                        (revision_id, batch_size),
                    )
                    deleted += cursor.rowcount
                    self._checkpoint(connection, run_id, revision_id, stage, deleted)
                    if cursor.rowcount == 0:
                        break
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            if self._is_protected(connection, revision_id):
                raise CorpusStorageError("GC_REVISION_BECAME_PROTECTED")
            connection.execute("DELETE FROM ai.revision_holds WHERE revision_id=%s", (revision_id,))
            connection.execute(
                "DELETE FROM ai.revision_read_leases WHERE revision_id=%s", (revision_id,)
            )
            connection.execute(
                "DELETE FROM ai.rollback_corpus WHERE revision_id=%s", (revision_id,)
            )
            connection.execute(
                "DELETE FROM ai.corpus_sync_runs WHERE revision_id=%s", (revision_id,)
            )
            connection.execute(
                "DELETE FROM ai.corpus_revisions WHERE revision_id=%s", (revision_id,)
            )
            connection.execute(
                """INSERT INTO ai.gc_audit
                (audit_id,run_id,revision_id,manifest_hash,reason_code,deleted_count,deleted_bytes)
                VALUES (%s,%s,%s,%s,'RETENTION_EXPIRED',%s,%s)""",
                (uuid4(), run_id, revision_id, manifest_hash, deleted, deleted_bytes),
            )
            self._checkpoint(connection, run_id, revision_id, "DONE", deleted)
        return deleted

    @staticmethod
    def _is_protected(
        connection: psycopg.Connection[dict[str, object]], revision_id: str
    ) -> bool:
        row = connection.execute(
            """SELECT EXISTS (
              SELECT 1 FROM ai.active_corpus WHERE revision_id=%s
              UNION ALL SELECT 1 FROM ai.rollback_corpus WHERE revision_id=%s AND expires_at>now()
              UNION ALL SELECT 1 FROM ai.revision_holds WHERE revision_id=%s AND expires_at>now()
              UNION ALL SELECT 1 FROM ai.corpus_sync_runs WHERE revision_id=%s
                AND state='RUNNING' AND lease_expires_at>now()
              UNION ALL SELECT 1 FROM ai.revision_read_leases WHERE revision_id=%s
                AND expires_at>now()) AS protected""",
            (revision_id,) * 5,
        ).fetchone()
        if row is None:
            raise CorpusStorageError("GC_PROTECTION_CHECK_FAILED")
        return row["protected"] is True

    @staticmethod
    def _checkpoint(
        connection: psycopg.Connection[dict[str, object]],
        run_id: UUID,
        revision_id: str,
        stage: str,
        deleted: int,
    ) -> None:
        connection.execute(
            """INSERT INTO ai.gc_checkpoints (run_id,revision_id,stage,deleted_count)
            VALUES (%s,%s,%s,%s) ON CONFLICT (run_id,revision_id) DO UPDATE SET
            stage=excluded.stage, deleted_count=excluded.deleted_count""",
            (run_id, revision_id, stage, deleted),
        )
