from datetime import UTC, datetime, timedelta
from uuid import UUID

import psycopg
import pytest

from onmaru_ai.corpus.revocation import RevocationEvent, RevocationLedger
from onmaru_ai.storage.postgres import CorpusStorageError, PostgresCorpusStore

from .helpers import PLACE, activate, bundle

NOW = datetime.now(UTC)


def test_revocation_blocks_every_revision_before_content_purge(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)

    ledger = RevocationLedger(dsn)
    ledger.apply(
        (RevocationEvent.place(1, PLACE, "PRIVATE", NOW),),
        heartbeat_sequence=1,
        heartbeat_at=NOW,
    )

    with store.snapshot() as snapshot:
        assert snapshot.revoked_places == frozenset({PLACE})
        assert snapshot.versions.source_revocation_sequence == 1
    assert db.execute("SELECT count(*) FROM ai.documents").fetchone() == (2,)
    with pytest.raises(CorpusStorageError, match="REVOKED_DOCUMENT"):
        store.activate(
            "r2",
            manifest_hash=second[0].manifest_hash,
            expected_active="r1",
            expected_revocation_sequence=1,
        )

    result = ledger.purge_revoked(batch_size=10)
    assert result.deleted_documents == 2
    assert db.execute("SELECT count(*) FROM ai.documents").fetchone() == (0,)
    assert db.execute("SELECT count(*) FROM ai.chunks").fetchone() == (0,)
    assert db.execute("SELECT count(*) FROM ai.embeddings").fetchone() == (0,)


@pytest.mark.parametrize("fault", ["gap", "reverse", "stale", "missing"])
def test_sequence_or_heartbeat_fault_fails_closed(
    dsn: str,
    db: psycopg.Connection[tuple[object, ...]],
    fault: str,
) -> None:
    store = PostgresCorpusStore(dsn)
    revision = bundle("r1")
    store.stage(*revision)
    activate(store, revision[0], None)
    ledger = RevocationLedger(dsn)

    if fault == "gap":
        with pytest.raises(CorpusStorageError, match="REVOCATION_SEQUENCE_GAP"):
            ledger.apply(
                (RevocationEvent.place(2, PLACE, "PRIVATE", NOW),),
                heartbeat_sequence=2,
                heartbeat_at=NOW,
            )
    elif fault == "reverse":
        ledger.apply(
            (RevocationEvent.place(1, PLACE, "PRIVATE", NOW),),
            heartbeat_sequence=1,
            heartbeat_at=NOW,
        )
        with pytest.raises(CorpusStorageError, match="REVOCATION_SEQUENCE_CONFLICT"):
            ledger.apply(
                (
                    RevocationEvent.source_revision(
                        1, "TOUR", "different", "v1", "RIGHTS", NOW
                    ),
                ),
                heartbeat_sequence=1,
                heartbeat_at=NOW,
            )
    elif fault == "stale":
        ledger.heartbeat(0, NOW - timedelta(seconds=61))
    else:
        db.execute("UPDATE ai.revocation_state SET heartbeat_at=NULL")

    with pytest.raises(
        CorpusStorageError, match="REVOCATION_(UNHEALTHY|SEQUENCE|MISMATCH)"
    ), store.snapshot():
        pass


def test_restore_reapplies_authoritative_ledger_and_rejects_incomplete_history(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    revision = bundle("r1")
    store.stage(*revision)
    activate(store, revision[0], None)
    ledger = RevocationLedger(dsn)
    events = (
        RevocationEvent.source_revision(1, "TOUR", "source-1", "source-v1", "RIGHTS", NOW),
        RevocationEvent.place(2, UUID(int=99), "PRIVATE", NOW),
    )

    ledger.reapply_after_restore(events, heartbeat_sequence=2, heartbeat_at=NOW)
    assert db.execute("SELECT sequence FROM ai.revocation_state").fetchone() == (2,)
    assert db.execute("SELECT count(*) FROM ai.source_revocations").fetchone() == (1,)
    with store.snapshot() as snapshot:
        assert snapshot.versions.source_revocation_sequence == 2

    with pytest.raises(CorpusStorageError, match="RESTORE_LEDGER_INCOMPLETE"):
        ledger.reapply_after_restore(events[:1], heartbeat_sequence=2, heartbeat_at=NOW)
    with pytest.raises(CorpusStorageError, match="REVOCATION_UNHEALTHY"), store.snapshot():
        pass
