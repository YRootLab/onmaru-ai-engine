from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.storage.postgres import CORPUS_WRITE_LOCK, CorpusStorageError


class RevocationScope(StrEnum):
    SOURCE_REVISION = "SOURCE_REVISION"
    PLACE = "PLACE"


@dataclass(frozen=True)
class RevocationEvent:
    sequence: int
    scope: RevocationScope
    reason_code: str
    revoked_at: datetime
    source_type: str | None = None
    source_id: str | None = None
    source_revision_id: str | None = None
    place_id: UUID | None = None

    @classmethod
    def place(
        cls, sequence: int, place_id: UUID, reason_code: str, revoked_at: datetime
    ) -> RevocationEvent:
        return cls(sequence, RevocationScope.PLACE, reason_code, revoked_at, place_id=place_id)

    @classmethod
    def source_revision(
        cls,
        sequence: int,
        source_type: str,
        source_id: str,
        source_revision: str,
        reason_code: str,
        revoked_at: datetime,
    ) -> RevocationEvent:
        return cls(
            sequence,
            RevocationScope.SOURCE_REVISION,
            reason_code,
            revoked_at,
            source_type,
            source_id,
            source_revision,
        )


@dataclass(frozen=True)
class PurgeResult:
    deleted_embeddings: int
    deleted_chunks: int
    deleted_documents: int


class RevocationLedger:
    """Durable, ordered revocation projection used before any corpus content cleanup."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def heartbeat(self, sequence: int, heartbeat_at: datetime) -> None:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            row = connection.execute(
                "SELECT sequence FROM ai.revocation_state WHERE id=1 FOR UPDATE"
            ).fetchone()
            if row is None or row["sequence"] != sequence:
                raise CorpusStorageError("REVOCATION_SEQUENCE_MISMATCH")
            connection.execute(
                "UPDATE ai.revocation_state SET heartbeat_at=%s WHERE id=1", (heartbeat_at,)
            )

    def apply(
        self,
        events: tuple[RevocationEvent, ...],
        *,
        heartbeat_sequence: int,
        heartbeat_at: datetime,
    ) -> None:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            state = connection.execute(
                "SELECT sequence FROM ai.revocation_state WHERE id=1 FOR UPDATE"
            ).fetchone()
            if state is None:
                raise CorpusStorageError("CONTROL_STATE_MISSING")
            current = int(state["sequence"])
            for event in events:
                if event.sequence <= current:
                    try:
                        self._verify_duplicate(connection, event)
                    except CorpusStorageError:
                        connection.execute(
                            "UPDATE ai.revocation_state SET heartbeat_at=NULL WHERE id=1"
                        )
                        connection.commit()
                        raise
                    continue
                if event.sequence != current + 1:
                    connection.execute(
                        "UPDATE ai.revocation_state SET heartbeat_at=NULL WHERE id=1"
                    )
                    connection.commit()
                    raise CorpusStorageError("REVOCATION_SEQUENCE_GAP")
                self._insert(connection, event)
                current = event.sequence
            if heartbeat_sequence != current:
                connection.execute("UPDATE ai.revocation_state SET heartbeat_at=NULL WHERE id=1")
                connection.commit()
                raise CorpusStorageError("REVOCATION_SEQUENCE_GAP")
            # The blocklists and both watermarks become visible atomically. Content purge follows.
            connection.execute(
                "UPDATE ai.revocation_state SET sequence=%s, heartbeat_at=%s WHERE id=1",
                (current, heartbeat_at),
            )
            connection.execute(
                "UPDATE ai.active_corpus SET revocation_sequence=%s WHERE id=1", (current,)
            )

    def reapply_after_restore(
        self,
        authoritative_events: tuple[RevocationEvent, ...],
        *,
        heartbeat_sequence: int,
        heartbeat_at: datetime,
    ) -> None:
        if (
            len(authoritative_events) != heartbeat_sequence
            or tuple(event.sequence for event in authoritative_events)
            != tuple(range(1, heartbeat_sequence + 1))
        ):
            self._mark_unhealthy()
            raise CorpusStorageError("RESTORE_LEDGER_INCOMPLETE")
        self.apply(
            authoritative_events,
            heartbeat_sequence=heartbeat_sequence,
            heartbeat_at=heartbeat_at,
        )

    def purge_revoked(self, *, batch_size: int = 500) -> PurgeResult:
        if batch_size < 1:
            raise ValueError("batch_size must be positive")
        totals = [0, 0, 0]
        predicates = """EXISTS (SELECT 1 FROM ai.documents d
            WHERE d.revision_id=c.revision_id AND d.document_id=c.document_id AND (
              EXISTS (SELECT 1 FROM ai.place_revocations p WHERE p.place_id=d.place_id)
              OR EXISTS (SELECT 1 FROM ai.source_revocations s WHERE
                (s.source_type,s.source_id,s.source_revision)=
                (d.source_type,d.source_id,d.source_revision))))"""
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            while True:
                cursor = connection.execute(
                    f"""DELETE FROM ai.embeddings e WHERE ctid IN (
                    SELECT e.ctid FROM ai.embeddings e JOIN ai.chunks c USING (revision_id,chunk_id)
                    WHERE {predicates} LIMIT %s)""",
                    (batch_size,),
                )
                totals[0] += cursor.rowcount
                if cursor.rowcount == 0:
                    break
            while True:
                cursor = connection.execute(
                    f"DELETE FROM ai.chunks c WHERE ctid IN (SELECT c.ctid FROM ai.chunks c "
                    f"WHERE {predicates} LIMIT %s)",
                    (batch_size,),
                )
                totals[1] += cursor.rowcount
                if cursor.rowcount == 0:
                    break
            while True:
                cursor = connection.execute(
                    """DELETE FROM ai.documents d WHERE ctid IN (SELECT d.ctid FROM ai.documents d
                    WHERE EXISTS (SELECT 1 FROM ai.place_revocations p WHERE p.place_id=d.place_id)
                       OR EXISTS (SELECT 1 FROM ai.source_revocations s WHERE
                         (s.source_type,s.source_id,s.source_revision)=
                         (d.source_type,d.source_id,d.source_revision)) LIMIT %s)""",
                    (batch_size,),
                )
                totals[2] += cursor.rowcount
                if cursor.rowcount == 0:
                    break
            connection.execute(
                """UPDATE ai.corpus_revisions r SET
                document_count=(SELECT count(*) FROM ai.documents d
                                WHERE d.revision_id=r.revision_id),
                chunk_count=(SELECT count(*) FROM ai.chunks c WHERE c.revision_id=r.revision_id),
                embedding_count=(SELECT count(*) FROM ai.embeddings e
                                 WHERE e.revision_id=r.revision_id)"""
            )
        return PurgeResult(*totals)

    def _mark_unhealthy(self) -> None:
        with psycopg.connect(self._dsn) as connection:
            connection.execute("UPDATE ai.revocation_state SET heartbeat_at=NULL WHERE id=1")

    @staticmethod
    def _verify_duplicate(
        connection: psycopg.Connection[dict[str, object]], event: RevocationEvent
    ) -> None:
        row = connection.execute(
            "SELECT * FROM ai.revocation_events WHERE sequence=%s", (event.sequence,)
        ).fetchone()
        expected = (
            event.scope.value,
            event.source_type,
            event.source_id,
            event.source_revision_id,
            event.place_id,
            event.reason_code,
        )
        actual = None if row is None else (
            row["scope"], row["source_type"], row["source_id"], row["source_revision"],
            row["place_id"], row["reason_code"],
        )
        if actual != expected:
            raise CorpusStorageError("REVOCATION_SEQUENCE_CONFLICT")

    @staticmethod
    def _insert(connection: psycopg.Connection[dict[str, object]], event: RevocationEvent) -> None:
        connection.execute(
            """INSERT INTO ai.revocation_events
            (sequence,scope,source_type,source_id,source_revision,place_id,revoked_at,reason_code)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s)""",
            (
                event.sequence, event.scope.value, event.source_type, event.source_id,
                event.source_revision_id, event.place_id, event.revoked_at, event.reason_code,
            ),
        )
        if event.scope is RevocationScope.PLACE:
            connection.execute(
                """INSERT INTO ai.place_revocations VALUES (%s,%s,%s)
                ON CONFLICT (place_id) DO UPDATE SET last_sequence=excluded.last_sequence,
                revoked_at=excluded.revoked_at""",
                (event.place_id, event.sequence, event.revoked_at),
            )
        else:
            connection.execute(
                """INSERT INTO ai.source_revocations VALUES (%s,%s,%s,%s,%s)
                ON CONFLICT (source_type,source_id,source_revision) DO UPDATE SET
                last_sequence=excluded.last_sequence, revoked_at=excluded.revoked_at""",
                (
                    event.source_type, event.source_id, event.source_revision_id,
                    event.sequence, event.revoked_at,
                ),
            )
