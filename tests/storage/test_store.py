from dataclasses import replace
from datetime import UTC, datetime
from uuid import UUID

import psycopg
import pytest

from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash
from onmaru_ai.storage.postgres import CorpusStorageError, PostgresCorpusStore

DOCUMENT = UUID("00000000-0000-0000-0000-000000000001")
CHUNK = UUID("00000000-0000-0000-0000-000000000002")
PLACE = UUID("00000000-0000-0000-0000-000000000003")
NOW = datetime(2026, 11, 5, tzinfo=UTC)


def bundle(
    revision_id: str,
) -> tuple[Revision, tuple[Document, ...], tuple[Chunk, ...], tuple[Embedding, ...]]:
    document = Document(
        document_id=DOCUMENT,
        place_id=PLACE,
        source_type="TOUR",
        source_id="source-1",
        source_revision="source-v1",
        title="한옥",
        published_at=NOW,
        collected_at=NOW,
        license_code="PUBLIC",
        region_code="KR-11",
        category_code="HANOK",
        normalized_text="한옥 이야기",
        content_hash=text_hash("한옥 이야기"),
    )
    chunk = Chunk(
        chunk_id=CHUNK,
        document_id=DOCUMENT,
        ordinal=0,
        start_offset=0,
        end_offset=6,
        chunk_text="한옥 이야기",
        content_hash=text_hash("한옥 이야기"),
        search_text="한옥 이야기",
    )
    embedding = Embedding(
        chunk_id=CHUNK, embedding_profile_id="e5-small-384", values=(1.0,) + (0.0,) * 383
    )
    revision = Revision(
        revision_id=revision_id,
        source_revision="export-v1",
        embedding_profile_id="e5-small-384",
        chunker_version="paragraph-1",
        dictionary_version="questions-1",
        config_hash=text_hash(revision_id),
        document_hashes=((DOCUMENT, document.digest()),),
        chunk_count=1,
        embedding_count=1,
    )
    return revision, (document,), (chunk,), (embedding,)


def activate(store: PostgresCorpusStore, revision: Revision, previous: str | None) -> None:
    store.activate(
        revision.revision_id,
        manifest_hash=revision.manifest_hash,
        expected_active=previous,
        expected_revocation_sequence=0,
    )


@pytest.fixture
def store(db: psycopg.Connection[tuple[object, ...]], dsn: str) -> PostgresCorpusStore:
    return PostgresCorpusStore(dsn)


def test_stage_is_invisible_until_atomic_activation(store: PostgresCorpusStore) -> None:
    revision, documents, chunks, embeddings = bundle("r1")
    assert store.stage(revision, documents, chunks, embeddings)
    with pytest.raises(CorpusStorageError, match="NO_ACTIVE_CORPUS"), store.snapshot():
        pass
    activate(store, revision, None)
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r1"
        assert snapshot.versions.config_hash == text_hash("r1")
        assert snapshot.versions.source_revocation_sequence == 0
        assert snapshot.embedding_profile_id == "e5-small-384"
        count = snapshot.connection.execute("SELECT count(*) AS n FROM ai.chunks").fetchone()
        assert count is not None and count["n"] == 1


@pytest.mark.parametrize(
    "fault", ["partial", "document_hash", "chunk_hash", "offset", "profile", "fk", "vector"]
)
def test_bad_stage_keeps_active_pointer(store: PostgresCorpusStore, fault: str) -> None:
    old = bundle("r1")
    store.stage(*old)
    activate(store, old[0], None)
    revision, documents, chunks, embeddings = bundle("r2")
    if fault == "partial":
        documents = ()
    elif fault == "document_hash":
        documents = (replace(documents[0], normalized_text="변조"),)
    elif fault == "chunk_hash":
        chunks = (replace(chunks[0], content_hash=text_hash("wrong")),)
    elif fault == "offset":
        chunks = (replace(chunks[0], end_offset=99),)
    elif fault == "profile":
        embeddings = (replace(embeddings[0], embedding_profile_id="wrong"),)
    elif fault == "fk":
        chunks = (replace(chunks[0], document_id=UUID(int=99)),)
    else:
        embeddings = (replace(embeddings[0], values=(float("nan"),) + (0.0,) * 383),)
    with pytest.raises((CorpusStorageError, psycopg.IntegrityError)):
        store.stage(revision, documents, chunks, embeddings)
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r1"
        count = snapshot.connection.execute(
            "SELECT count(*) AS n FROM ai.corpus_revisions WHERE revision_id='r2'"
        ).fetchone()
        assert count is not None and count["n"] == 0


@pytest.mark.parametrize("fault", ["manifest", "sequence", "stale_pointer", "partial"])
def test_activation_rechecks_preconditions(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
    fault: str,
) -> None:
    old, new = bundle("r1"), bundle("r2")
    store.stage(*old)
    activate(store, old[0], None)
    store.stage(*new)
    if fault == "partial":
        db.execute("DELETE FROM ai.embeddings WHERE revision_id='r2'")
    with pytest.raises(CorpusStorageError):
        store.activate(
            "r2",
            manifest_hash="bad" if fault == "manifest" else new[0].manifest_hash,
            expected_active="other" if fault == "stale_pointer" else "r1",
            expected_revocation_sequence=1 if fault == "sequence" else 0,
        )
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r1"
    assert db.execute(
        "SELECT state FROM ai.corpus_revisions WHERE revision_id='r2'"
    ).fetchone() == ("BUILDING",)


def test_duplicate_manifest_does_not_reactivate_old_revision(store: PostgresCorpusStore) -> None:
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)
    activate(store, second[0], "r1")
    assert store.stage(*first) is False
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r2"


def test_only_two_recent_revisions_can_rollback(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
) -> None:
    previous = None
    for number in range(1, 5):
        current = bundle(f"r{number}")
        store.stage(*current)
        activate(store, current[0], previous)
        previous = current[0].revision_id
    assert db.execute("SELECT revision_id FROM ai.rollback_corpus ORDER BY slot").fetchall() == [
        ("r3",),
        ("r2",),
    ]
    with pytest.raises(CorpusStorageError, match="ROLLBACK_UNAVAILABLE"):
        store.rollback(
            "r1",
            manifest_hash=bundle("r1")[0].manifest_hash,
            expected_active="r4",
            expected_revocation_sequence=0,
        )
    store.rollback(
        "r2",
        manifest_hash=bundle("r2")[0].manifest_hash,
        expected_active="r4",
        expected_revocation_sequence=0,
    )
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r2"
    assert db.execute("SELECT revision_id FROM ai.rollback_corpus ORDER BY slot").fetchall() == [
        ("r4",),
        ("r3",),
    ]


def test_snapshot_stays_consistent_during_concurrent_activation(store: PostgresCorpusStore) -> None:
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)
    with store.snapshot() as snapshot:
        activate(store, second[0], "r1")  # A second connection commits while the reader is open.
        row = snapshot.connection.execute(
            "SELECT revision_id, revocation_sequence FROM ai.active_corpus"
        ).fetchone()
        assert row == {"revision_id": "r1", "revocation_sequence": 0}
        assert snapshot.versions.config_hash == text_hash("r1")
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r2"
        assert snapshot.versions.config_hash == text_hash("r2")


def test_revoked_place_blocks_rollback_and_keeps_current_watermark(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
) -> None:
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)
    activate(store, second[0], "r1")
    with db.transaction():
        db.execute(
            "INSERT INTO ai.revocation_events (sequence, scope, place_id, reason_code) "
            "VALUES (1, 'PLACE', %s, 'PRIVATE')",
            (PLACE,),
        )
        db.execute("INSERT INTO ai.place_revocations VALUES (%s, 1, now())", (PLACE,))
        db.execute("UPDATE ai.revocation_state SET sequence=1")
        db.execute("UPDATE ai.active_corpus SET revocation_sequence=1")
    with pytest.raises(CorpusStorageError, match="REVOKED_DOCUMENT"):
        store.rollback(
            "r1",
            manifest_hash=first[0].manifest_hash,
            expected_active="r2",
            expected_revocation_sequence=1,
        )
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r2"
        assert snapshot.versions.source_revocation_sequence == 1
        assert PLACE in snapshot.revoked_places


@pytest.mark.parametrize(
    "fault",
    [
        "cross_revision_document",
        "cross_revision_embedding",
        "rollback_slot",
        "vector_dimension",
        "vector_norm",
        "vector_nan",
    ],
)
def test_database_constraints_reject_invalid_rows(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
    fault: str,
) -> None:
    first = bundle("r1")
    store.stage(*first)
    activate(store, first[0], None)
    second = replace(bundle("r2")[0], document_hashes=(), chunk_count=0, embedding_count=0)
    store.stage(second, (), (), ())
    statements: dict[str, tuple[str, tuple[object, ...]]] = {
        "cross_revision_document": (
            "INSERT INTO ai.chunks SELECT 'r2', chunk_id, document_id, ordinal, "
            "start_offset, end_offset, chunk_text, content_hash, search_text "
            "FROM ai.chunks WHERE revision_id='r1'",
            (),
        ),
        "cross_revision_embedding": (
            "INSERT INTO ai.embeddings SELECT 'r2', chunk_id, embedding_profile_id, "
            "embedding, normalized FROM ai.embeddings WHERE revision_id='r1'",
            (),
        ),
        "rollback_slot": (
            "INSERT INTO ai.rollback_corpus VALUES (3, 'r2', now(), now()+interval '1 day')",
            (),
        ),
        "vector_dimension": ("UPDATE ai.embeddings SET embedding='[1,0]'", ()),
        "vector_norm": (
            "UPDATE ai.embeddings SET embedding=%s",
            ("[" + ",".join(["0"] * 384) + "]",),
        ),
        "vector_nan": (
            "UPDATE ai.embeddings SET embedding=%s",
            ("[" + ",".join(["NaN"] + ["0"] * 383) + "]",),
        ),
    }
    with pytest.raises((psycopg.IntegrityError, psycopg.DataError)), db.transaction():
        db.execute(*statements[fault])
    with store.snapshot() as snapshot:
        assert snapshot.versions.corpus_revision == "r1"


def test_expired_rollback_and_revocation_mismatch_fail_closed(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
) -> None:
    first, second = bundle("r1"), bundle("r2")
    store.stage(*first)
    activate(store, first[0], None)
    store.stage(*second)
    activate(store, second[0], "r1")
    db.execute(
        "UPDATE ai.rollback_corpus SET retired_at=now()-interval '31 days', "
        "expires_at=now()-interval '1 day'"
    )
    with pytest.raises(CorpusStorageError, match="ROLLBACK_UNAVAILABLE"):
        store.rollback(
            "r1",
            manifest_hash=first[0].manifest_hash,
            expected_active="r2",
            expected_revocation_sequence=0,
        )
    db.execute("UPDATE ai.revocation_state SET sequence=1")
    with pytest.raises(CorpusStorageError, match="REVOCATION_MISMATCH"), store.snapshot():
        pass


def test_snapshot_includes_old_revocations_while_writer_advances(
    store: PostgresCorpusStore,
    db: psycopg.Connection[tuple[object, ...]],
) -> None:
    first = bundle("r1")
    store.stage(*first)
    activate(store, first[0], None)
    with store.snapshot() as snapshot:
        with db.transaction():
            db.execute(
                "INSERT INTO ai.revocation_events "
                "(sequence, scope, source_type, source_id, source_revision, reason_code) "
                "VALUES (1, 'SOURCE_REVISION', 'TOUR', 'source-1', 'source-v1', 'RIGHTS')"
            )
            db.execute(
                "INSERT INTO ai.source_revocations "
                "VALUES ('TOUR', 'source-1', 'source-v1', 1, now())"
            )
            db.execute("UPDATE ai.revocation_state SET sequence=1")
            db.execute("UPDATE ai.active_corpus SET revocation_sequence=1")
        assert not snapshot.revoked_sources
        assert snapshot.versions.source_revocation_sequence == 0
        assert snapshot.connection.execute("SELECT * FROM ai.source_revocations").fetchall() == []
    with store.snapshot() as snapshot:
        assert snapshot.revoked_sources == frozenset({("TOUR", "source-1", "source-v1")})
        assert snapshot.versions.source_revocation_sequence == 1
    second = bundle("r2")
    store.stage(*second)
    with pytest.raises(CorpusStorageError, match="REVOKED_DOCUMENT"):
        store.activate(
            "r2",
            manifest_hash=second[0].manifest_hash,
            expected_active="r1",
            expected_revocation_sequence=1,
        )
