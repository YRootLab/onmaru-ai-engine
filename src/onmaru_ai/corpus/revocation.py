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


@dataclass(frozen=True)
class RevocationLedgerState:
    sequence: int
    source_snapshot_watermark: int | None
    heartbeat_at: datetime | None


class RevocationLedger:
    """Durable, ordered revocation projection used before any corpus content cleanup."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def state(self) -> RevocationLedgerState:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            row = connection.execute(
                "SELECT sequence, source_snapshot_watermark, heartbeat_at "
                "FROM ai.revocation_state WHERE id=1"
            ).fetchone()
        if row is None:
            raise CorpusStorageError("CONTROL_STATE_MISSING")
        return RevocationLedgerState(
            int(row["sequence"]), row["source_snapshot_watermark"], row["heartbeat_at"]
        )

    def mark_unhealthy(self) -> None:
        self._mark_unhealthy()

    def begin_snapshot(
        self, snapshot_id: UUID, watermark: int, active_revision_id: UUID, public_place_count: int
    ) -> None:
        if watermark < 0 or public_place_count < 0:
            raise CorpusStorageError("REVOCATION_SNAPSHOT_INVALID")
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            connection.execute(
                """INSERT INTO ai.revocation_snapshot_staging_state
                   (snapshot_id,watermark,active_revision_id,public_place_count)
                   VALUES (%s,%s,%s,%s) ON CONFLICT (snapshot_id) DO NOTHING""",
                (snapshot_id, watermark, str(active_revision_id), public_place_count),
            )
            row = connection.execute(
                "SELECT watermark,active_revision_id,public_place_count "
                "FROM ai.revocation_snapshot_staging_state WHERE snapshot_id=%s FOR UPDATE",
                (snapshot_id,),
            ).fetchone()
            if row is None or (int(row["watermark"]), str(row["active_revision_id"]),
                               int(row["public_place_count"])) != (
                    watermark, str(active_revision_id), public_place_count):
                raise CorpusStorageError("REVOCATION_SNAPSHOT_CONFLICT")

    def stage_snapshot_events(
        self,
        snapshot_id: UUID,
        *,
        watermark: int,
        after_sequence: int,
        events: tuple[RevocationEvent, ...],
        has_more: bool,
    ) -> None:
        expected = tuple(range(after_sequence + 1, after_sequence + 1 + len(events)))
        if tuple(event.sequence for event in events) != expected:
            raise CorpusStorageError("REVOCATION_SNAPSHOT_GAP")
        cursor = events[-1].sequence if events else after_sequence
        if cursor > watermark or (has_more and cursor >= watermark):
            raise CorpusStorageError("REVOCATION_SNAPSHOT_INVALID")
        if not has_more and cursor != watermark:
            raise CorpusStorageError("REVOCATION_SNAPSHOT_INCOMPLETE")
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            state = connection.execute(
                "SELECT watermark,event_cursor FROM ai.revocation_snapshot_staging_state "
                "WHERE snapshot_id=%s FOR UPDATE", (snapshot_id,)
            ).fetchone()
            if state is None or int(state["watermark"]) != watermark:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_CONFLICT")
            if int(state["event_cursor"]) != after_sequence:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_CURSOR_MISMATCH")
            for event in events:
                self._stage_event(connection, snapshot_id, event)
            connection.execute(
                "UPDATE ai.revocation_snapshot_staging_state "
                "SET event_cursor=%s,events_complete=%s WHERE snapshot_id=%s",
                (cursor, not has_more, snapshot_id),
            )

    def stage_snapshot_places(
        self,
        snapshot_id: UUID,
        *,
        after_public_id: str | None,
        public_place_ids: tuple[str, ...],
        has_more: bool,
    ) -> None:
        cursor_value = after_public_id or ""
        if tuple(sorted(set(public_place_ids))) != public_place_ids or any(
            not item or item <= cursor_value for item in public_place_ids
        ) or (has_more and not public_place_ids):
            raise CorpusStorageError("REVOCATION_SNAPSHOT_PLACES_INVALID")
        next_cursor = public_place_ids[-1] if public_place_ids else cursor_value
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            state = connection.execute(
                "SELECT place_cursor FROM ai.revocation_snapshot_staging_state "
                "WHERE snapshot_id=%s FOR UPDATE", (snapshot_id,)
            ).fetchone()
            if state is None or state["place_cursor"] != cursor_value:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_CURSOR_MISMATCH")
            if public_place_ids:
                with connection.cursor() as cursor:
                    cursor.executemany(
                        "INSERT INTO ai.revocation_snapshot_staging_places(snapshot_id,public_id) "
                        "VALUES (%s,%s) ON CONFLICT DO NOTHING",
                        [(snapshot_id, public_id) for public_id in public_place_ids],
                    )
            connection.execute(
                "UPDATE ai.revocation_snapshot_staging_state "
                "SET place_cursor=%s,places_complete=%s WHERE snapshot_id=%s",
                (next_cursor, not has_more, snapshot_id),
            )

    def install_snapshot(self, snapshot_id: UUID, *, heartbeat_at: datetime) -> None:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))
            snapshot = connection.execute(
                "SELECT * FROM ai.revocation_snapshot_staging_state "
                "WHERE snapshot_id=%s FOR UPDATE",
                (snapshot_id,),
            ).fetchone()
            if (
                snapshot is None
                or not snapshot["events_complete"]
                or not snapshot["places_complete"]
            ):
                raise CorpusStorageError("REVOCATION_SNAPSHOT_INCOMPLETE")
            watermark = int(snapshot["watermark"])
            events = connection.execute(
                "SELECT count(*) AS count,min(sequence) AS first,max(sequence) AS last "
                "FROM ai.revocation_snapshot_staging_events WHERE snapshot_id=%s", (snapshot_id,)
            ).fetchone()
            if events is None:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_GAP")
            event_count = int(events["count"])
            if event_count != watermark or (watermark and (
                int(events["first"]) != 1 or int(events["last"]) != watermark
            )):
                raise CorpusStorageError("REVOCATION_SNAPSHOT_GAP")
            place_count = connection.execute(
                "SELECT count(*) AS count FROM ai.revocation_snapshot_staging_places "
                "WHERE snapshot_id=%s",
                (snapshot_id,),
            ).fetchone()
            if place_count is None:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_PLACES_INCOMPLETE")
            if int(place_count["count"]) != int(snapshot["public_place_count"]):
                raise CorpusStorageError("REVOCATION_SNAPSHOT_PLACES_INCOMPLETE")

            uncovered = connection.execute(
                """SELECT 1
                   FROM ai.documents d JOIN ai.corpus_revisions r USING (revision_id)
                   WHERE r.gc_state='LIVE'
                     AND NOT EXISTS (
                         SELECT 1 FROM ai.revocation_snapshot_staging_places p
                         WHERE p.snapshot_id=%s AND p.public_id=d.source_id
                     )
                     AND NOT EXISTS (
                         SELECT 1 FROM ai.revocation_snapshot_staging_events e
                         WHERE e.snapshot_id=%s AND (
                           (e.scope='SOURCE_REVISION' AND
                            (e.source_type,e.source_id,e.source_revision)=
                            (d.source_type,d.source_id,d.source_revision))
                           OR (e.scope='PLACE' AND e.place_id=d.place_id)
                         )
                     ) LIMIT 1""", (snapshot_id, snapshot_id)
            ).fetchone()
            if uncovered is not None:
                raise CorpusStorageError("REVOCATION_SNAPSHOT_HISTORY_INCOMPLETE")

            connection.execute("DELETE FROM ai.place_revocations")
            connection.execute("DELETE FROM ai.source_revocations")
            connection.execute("DELETE FROM ai.revocation_events")
            staged = connection.execute(
                "SELECT * FROM ai.revocation_snapshot_staging_events "
                "WHERE snapshot_id=%s ORDER BY sequence", (snapshot_id,)
            ).fetchall()
            for row in staged:
                event = RevocationEvent(
                    int(row["sequence"]), RevocationScope(row["scope"]), row["reason_code"],
                    row["revoked_at"], row["source_type"], row["source_id"],
                    row["source_revision"], row["place_id"],
                )
                self._insert(connection, event)
            connection.execute(
                "UPDATE ai.revocation_state SET sequence=%s,heartbeat_at=%s,"
                "source_snapshot_watermark=%s WHERE id=1",
                (watermark, heartbeat_at, watermark),
            )
            connection.execute(
                "UPDATE ai.active_corpus SET revocation_sequence=%s WHERE id=1", (watermark,)
            )
            connection.execute(
                "DELETE FROM ai.revocation_snapshot_staging_state WHERE snapshot_id=%s",
                (snapshot_id,),
            )

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
        heartbeat_at: datetime | None,
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
    def _stage_event(
        connection: psycopg.Connection[dict[str, object]], snapshot_id: UUID,
        event: RevocationEvent,
    ) -> None:
        connection.execute(
            """INSERT INTO ai.revocation_snapshot_staging_events
               (snapshot_id,sequence,scope,source_type,source_id,source_revision,place_id,revoked_at,reason_code)
               VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s) ON CONFLICT DO NOTHING""",
            (snapshot_id, event.sequence, event.scope.value, event.source_type, event.source_id,
             event.source_revision_id, event.place_id, event.revoked_at, event.reason_code),
        )

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
