from datetime import UTC, datetime, timedelta
from uuid import uuid4

import psycopg

from onmaru_ai.corpus.gc import CorpusGarbageCollector
from onmaru_ai.storage.postgres import PostgresCorpusStore

from .helpers import activate, bundle


def _stage(store: PostgresCorpusStore, revision_id: str) -> None:
    store.stage(*bundle(revision_id))


def test_gc_preserves_active_two_rollbacks_holds_and_leases(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    previous = None
    for revision_id in ("r1", "r2", "r3"):
        revision = bundle(revision_id)
        store.stage(*revision)
        activate(store, revision[0], previous)
        previous = revision_id
    for revision_id in ("held", "syncing", "reading", "delete-me"):
        _stage(store, revision_id)
    db.execute(
        "UPDATE ai.corpus_revisions SET state='REJECTED', expires_at=now()-interval '1 day' "
        "WHERE revision_id IN ('held','syncing','reading','delete-me')"
    )
    db.execute(
        "INSERT INTO ai.revision_holds VALUES (%s,'held','operator','INVESTIGATION',now(),"
        "now()+interval '1 day')",
        (uuid4(),),
    )
    db.execute(
        "UPDATE ai.corpus_sync_runs SET state='RUNNING', lease_expires_at=now()+interval '1 min' "
        "WHERE revision_id='syncing'"
    )
    db.execute(
        "INSERT INTO ai.revision_read_leases VALUES (%s,'reading',now()+interval '1 min')",
        (uuid4(),),
    )

    result = CorpusGarbageCollector(dsn).run(actor="test", max_revisions=10, batch_size=1)

    assert result.deleted_revisions == ("delete-me",)
    assert set(
        row[0] for row in db.execute("SELECT revision_id FROM ai.corpus_revisions").fetchall()
    ) == {"r1", "r2", "r3", "held", "syncing", "reading"}
    assert db.execute("SELECT count(*) FROM ai.gc_audit").fetchone() == (1,)
    assert db.execute("SELECT stage FROM ai.gc_checkpoints").fetchone() == ("DONE",)
    assert db.execute("SELECT count(*) FROM ai.chunks c LEFT JOIN ai.documents d "
                      "ON (c.revision_id,c.document_id)=(d.revision_id,d.document_id) "
                      "WHERE d.document_id IS NULL").fetchone() == (0,)


def test_gc_is_bounded_resumable_and_rechecks_active_pointer(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    for revision_id in ("one", "two"):
        _stage(store, revision_id)
    db.execute(
        "UPDATE ai.corpus_revisions SET state='REJECTED', expires_at=now()-interval '1 day'"
    )

    first = CorpusGarbageCollector(dsn).run(actor="test", max_revisions=1, batch_size=1)
    second = CorpusGarbageCollector(dsn).run(actor="test", max_revisions=1, batch_size=1)

    assert len(first.deleted_revisions) == len(second.deleted_revisions) == 1
    assert set(first.deleted_revisions + second.deleted_revisions) == {"one", "two"}
    assert db.execute("SELECT count(*) FROM ai.gc_runs WHERE state='SUCCEEDED'").fetchone() == (2,)


def test_expired_read_lease_and_hold_no_longer_block_gc(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    _stage(store, "old")
    db.execute(
        "UPDATE ai.corpus_revisions SET state='REJECTED', expires_at=now()-interval '1 day'"
    )
    past = datetime.now(UTC) - timedelta(minutes=1)
    db.execute(
        "INSERT INTO ai.revision_read_leases VALUES (%s,'old',%s)", (uuid4(), past)
    )
    db.execute(
        "INSERT INTO ai.revision_holds "
        "(hold_id,revision_id,approved_by,reason_code,created_at,expires_at) "
        "VALUES (%s,'old','operator','DONE',%s,%s)",
        (uuid4(), past - timedelta(days=1), past),
    )
    assert CorpusGarbageCollector(dsn).run(
        actor="test", max_revisions=1, batch_size=1
    ).deleted_revisions == ("old",)


def test_expired_rollback_becomes_collectable(
    dsn: str, db: psycopg.Connection[tuple[object, ...]]
) -> None:
    store = PostgresCorpusStore(dsn)
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)
    activate(store, second[0], "r1")
    db.execute(
        "UPDATE ai.rollback_corpus SET expires_at=now()-interval '1 second', "
        "retired_at=now()-interval '31 days' WHERE revision_id='r1'"
    )
    db.execute(
        "UPDATE ai.corpus_revisions SET expires_at=now()-interval '1 second' "
        "WHERE revision_id='r1'"
    )

    result = CorpusGarbageCollector(dsn).run(actor="test", max_revisions=1, batch_size=1)

    assert result.deleted_revisions == ("r1",)
    assert db.execute("SELECT revision_id FROM ai.active_corpus").fetchone() == ("r2",)
