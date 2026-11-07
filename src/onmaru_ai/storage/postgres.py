from __future__ import annotations

import json
import math
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from typing import Any
from uuid import UUID, uuid4

import psycopg
from psycopg import Connection, sql
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from onmaru_ai.contracts.models import Versions
from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision, text_hash

# All sync/activation/rollback/GC writers must use this lock before control row locks.
CORPUS_WRITE_LOCK = 731849203
Database = Connection[dict[str, Any]]


class CorpusStorageError(ValueError):
    """A revision or its expected activation authority failed validation."""


@dataclass(frozen=True)
class CorpusSnapshot:
    versions: Versions
    embedding_profile_id: str
    revoked_places: frozenset[UUID]
    revoked_sources: frozenset[tuple[str, str, str]]
    connection: Database


class PostgresCorpusStore:
    """Each write owns one transaction; callers must use a dedicated AI sync role.

    snapshot() holds a repeatable, read-only transaction until the context exits.
    Retrieval adapters must execute via snapshot.connection and filter both blocklists.
    No method wires this boundary into the legacy in-memory runtime.
    """

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def stage(
        self,
        revision: Revision,
        documents: tuple[Document, ...],
        chunks: tuple[Chunk, ...],
        embeddings: tuple[Embedding, ...],
    ) -> bool:
        """Persist a complete BUILDING bundle. Duplicate manifests never move a pointer."""
        _validate(revision, documents, chunks, embeddings)
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            _lock(connection)
            existing = connection.execute(
                "SELECT manifest_hash FROM ai.corpus_revisions WHERE revision_id=%s",
                (revision.revision_id,),
            ).fetchone()
            if existing is not None:
                if existing["manifest_hash"] != revision.manifest_hash:
                    raise CorpusStorageError("REVISION_CONFLICT")
                return False
            _insert(
                connection,
                "corpus_revisions",
                {
                    "revision_id": revision.revision_id,
                    "manifest_hash": revision.manifest_hash,
                    "manifest": Jsonb(json.loads(revision.canonical_manifest())),
                    "source_revision": revision.source_revision,
                    "state": "BUILDING",
                    "embedding_profile_id": revision.embedding_profile_id,
                    "chunker_version": revision.chunker_version,
                    "dictionary_version": revision.dictionary_version,
                    "config_hash": revision.config_hash,
                    "document_count": len(documents),
                    "chunk_count": revision.chunk_count,
                    "embedding_count": revision.embedding_count,
                },
            )
            for document in documents:
                _insert(
                    connection,
                    "documents",
                    {"revision_id": revision.revision_id, **asdict(document)},
                )
            for chunk in chunks:
                _insert(
                    connection, "chunks", {"revision_id": revision.revision_id, **asdict(chunk)}
                )
            for embedding in embeddings:
                _insert(
                    connection,
                    "embeddings",
                    {
                        "revision_id": revision.revision_id,
                        "chunk_id": embedding.chunk_id,
                        "embedding_profile_id": embedding.embedding_profile_id,
                        "embedding": json.dumps(embedding.values, allow_nan=False),
                        "normalized": True,
                    },
                )
            _insert(
                connection,
                "corpus_sync_runs",
                {
                    "run_id": uuid4(),
                    "revision_id": revision.revision_id,
                    "manifest_hash": revision.manifest_hash,
                    "state": "SUCCEEDED",
                    "document_count": len(documents),
                    "chunk_count": len(chunks),
                    "embedding_count": len(embeddings),
                },
            )
        return True

    def activate(
        self,
        revision_id: str,
        *,
        manifest_hash: str,
        expected_active: str | None,
        expected_revocation_sequence: int,
    ) -> None:
        self._switch(
            revision_id,
            manifest_hash,
            expected_active,
            expected_revocation_sequence,
            rollback=False,
        )

    def rollback(
        self,
        revision_id: str,
        *,
        manifest_hash: str,
        expected_active: str | None,
        expected_revocation_sequence: int,
    ) -> None:
        self._switch(
            revision_id, manifest_hash, expected_active, expected_revocation_sequence, rollback=True
        )

    def _switch(
        self,
        revision_id: str,
        manifest_hash: str,
        expected_active: str | None,
        expected_sequence: int,
        *,
        rollback: bool,
    ) -> None:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            _lock(connection)
            revocations = connection.execute(
                "SELECT sequence FROM ai.revocation_state WHERE id=1 FOR UPDATE"
            ).fetchone()
            active = connection.execute(
                "SELECT * FROM ai.active_corpus WHERE id=1 FOR UPDATE"
            ).fetchone()
            if active is None or revocations is None:
                raise CorpusStorageError("CONTROL_STATE_MISSING")
            if (
                revocations["sequence"] != expected_sequence
                or active["revocation_sequence"] != expected_sequence
            ):
                raise CorpusStorageError("REVOCATION_MISMATCH")
            if active["revision_id"] != expected_active:
                raise CorpusStorageError("ACTIVE_POINTER_CONFLICT")
            row = connection.execute(
                "SELECT * FROM ai.corpus_revisions WHERE revision_id=%s FOR UPDATE",
                (revision_id,),
            ).fetchone()
            if row is None or row["manifest_hash"] != manifest_hash:
                raise CorpusStorageError("MANIFEST_MISMATCH")
            if row["gc_state"] != "LIVE":
                raise CorpusStorageError("REVISION_UNAVAILABLE")
            if rollback:
                candidate = connection.execute(
                    "SELECT 1 FROM ai.rollback_corpus WHERE revision_id=%s AND expires_at>now()",
                    (revision_id,),
                ).fetchone()
                if row["state"] != "RETIRED" or candidate is None:
                    raise CorpusStorageError("ROLLBACK_UNAVAILABLE")
            elif row["state"] not in ("BUILDING", "VALIDATED"):
                raise CorpusStorageError("REVISION_NOT_STAGED")
            revision, documents, chunks, embeddings = _read_bundle(connection, row)
            if revision.manifest_hash != manifest_hash:
                raise CorpusStorageError("MANIFEST_MISMATCH")
            _validate(revision, documents, chunks, embeddings)
            if connection.execute(
                """SELECT 1 FROM ai.documents d WHERE d.revision_id=%s AND (
                    EXISTS (SELECT 1 FROM ai.place_revocations p WHERE p.place_id=d.place_id)
                    OR EXISTS (SELECT 1 FROM ai.source_revocations s
                        WHERE (s.source_type,s.source_id,s.source_revision)=
                              (d.source_type,d.source_id,d.source_revision))) LIMIT 1""",
                (revision_id,),
            ).fetchone():
                raise CorpusStorageError("REVOKED_DOCUMENT")
            connection.execute(
                "UPDATE ai.corpus_revisions SET state='VALIDATED' WHERE revision_id=%s",
                (revision_id,),
            )
            # Select survivors first, then replace the two bounded slots within this transaction.
            retained = connection.execute(
                """SELECT revision_id, retired_at,
                          LEAST(expires_at, retired_at + interval '14 days')
                          AS expires_at FROM ai.rollback_corpus
                   WHERE revision_id<>%s AND expires_at>now()
                     AND retired_at + interval '14 days'>now() ORDER BY slot LIMIT 1""",
                (revision_id,),
            ).fetchone()
            connection.execute("DELETE FROM ai.rollback_corpus")
            if expected_active is not None:
                connection.execute(
                    "UPDATE ai.corpus_revisions SET state='RETIRED', retired_at=now(), "
                    "expires_at=now()+interval '30 days' "
                    "WHERE revision_id=%s",
                    (expected_active,),
                )
                connection.execute(
                    "INSERT INTO ai.rollback_corpus "
                    "VALUES (1, %s, now(), now()+interval '30 days')",
                    (expected_active,),
                )
                if retained is not None:
                    _insert(connection, "rollback_corpus", {"slot": 2, **retained})
                    connection.execute(
                        "UPDATE ai.corpus_revisions SET expires_at=%s WHERE revision_id=%s",
                        (retained["expires_at"], retained["revision_id"]),
                    )
            connection.execute(
                "UPDATE ai.corpus_revisions "
                "SET state='ACTIVE', activated_at=now(), retired_at=NULL, expires_at=NULL "
                "WHERE revision_id=%s",
                (revision_id,),
            )
            connection.execute(
                "UPDATE ai.active_corpus SET revision_id=%s, revocation_sequence=%s, "
                "activated_at=now() WHERE id=1",
                (revision_id, expected_sequence),
            )

    @contextmanager
    def snapshot(self) -> Iterator[CorpusSnapshot]:
        with psycopg.connect(self._dsn, row_factory=dict_row) as connection:
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            row = connection.execute(
                """SELECT r.revision_id, r.config_hash, r.dictionary_version,
                          r.embedding_profile_id, a.revocation_sequence
                   FROM ai.active_corpus a JOIN ai.corpus_revisions r USING (revision_id)
                   JOIN ai.revocation_state s ON s.id=a.id
                   WHERE a.id=1 AND a.revocation_sequence=s.sequence
                     AND s.heartbeat_at IS NOT NULL
                     AND s.heartbeat_at >= clock_timestamp() - interval '60 seconds'
                     AND r.state='ACTIVE' AND r.gc_state='LIVE' """,
            ).fetchone()
            if row is None:
                control = connection.execute(
                    "SELECT a.revision_id, a.revocation_sequence AS active_sequence, "
                    "s.sequence, s.heartbeat_at, "
                    "s.heartbeat_at >= clock_timestamp()-interval '60 seconds' AS healthy "
                    "FROM ai.active_corpus a JOIN ai.revocation_state s ON s.id=a.id WHERE a.id=1"
                ).fetchone()
                if control is not None and (
                    control["heartbeat_at"] is None or not control["healthy"]
                ):
                    raise CorpusStorageError("REVOCATION_UNHEALTHY")
                if control is not None and control["active_sequence"] != control["sequence"]:
                    raise CorpusStorageError("REVOCATION_MISMATCH")
                raise CorpusStorageError("NO_ACTIVE_CORPUS_OR_REVOCATION_MISMATCH")
            places = frozenset(
                item["place_id"]
                for item in connection.execute("SELECT place_id FROM ai.place_revocations")
            )
            sources = frozenset(
                (item["source_type"], item["source_id"], item["source_revision"])
                for item in connection.execute("SELECT * FROM ai.source_revocations")
            )
            yield CorpusSnapshot(
                versions=Versions.model_validate(
                    {
                        "corpusRevision": row["revision_id"],
                        "configHash": row["config_hash"],
                        "questionDictionaryVersion": row["dictionary_version"],
                        "sourceRevocationSequence": row["revocation_sequence"],
                    }
                ),
                embedding_profile_id=row["embedding_profile_id"],
                revoked_places=places,
                revoked_sources=sources,
                connection=connection,
            )


def _lock(connection: Database) -> None:
    connection.execute("SELECT pg_advisory_xact_lock(%s)", (CORPUS_WRITE_LOCK,))


def _insert(connection: Database, table: str, values: Mapping[str, object]) -> None:
    connection.execute(
        sql.SQL("INSERT INTO ai.{} ({}) VALUES ({})").format(
            sql.Identifier(table),
            sql.SQL(",").join(map(sql.Identifier, values)),
            sql.SQL(",").join(sql.Placeholder() for _ in values),
        ),
        tuple(values.values()),
    )


def _read_bundle(
    connection: Database, row: dict[str, Any]
) -> tuple[
    Revision,
    tuple[Document, ...],
    tuple[Chunk, ...],
    tuple[Embedding, ...],
]:
    manifest = dict(row["manifest"])
    manifest["document_hashes"] = tuple(
        (UUID(key), value) for key, value in manifest["document_hashes"]
    )
    revision = Revision(**manifest)
    # Metadata is duplicated for efficient SQL filters; it must agree with the manifest.
    for key in (
        "source_revision",
        "embedding_profile_id",
        "chunker_version",
        "dictionary_version",
        "config_hash",
        "chunk_count",
        "embedding_count",
    ):
        if row[key] != getattr(revision, key):
            raise CorpusStorageError("REVISION_METADATA_MISMATCH")
    if row["document_count"] != len(revision.document_hashes):
        raise CorpusStorageError("REVISION_METADATA_MISMATCH")
    documents = tuple(
        Document(**{key: value for key, value in item.items() if key != "revision_id"})
        for item in connection.execute(
            "SELECT * FROM ai.documents WHERE revision_id=%s", (revision.revision_id,)
        )
    )
    chunks = tuple(
        Chunk(
            **{
                key: value
                for key, value in item.items()
                if key not in ("revision_id", "search_tsv")
            }
        )
        for item in connection.execute(
            "SELECT * FROM ai.chunks WHERE revision_id=%s", (revision.revision_id,)
        )
    )
    embeddings = tuple(
        Embedding(
            chunk_id=item["chunk_id"],
            embedding_profile_id=item["embedding_profile_id"],
            values=tuple(json.loads(item["embedding"])),
        )
        for item in connection.execute(
            "SELECT chunk_id, embedding_profile_id, embedding::text "
            "FROM ai.embeddings WHERE revision_id=%s",
            (revision.revision_id,),
        )
    )
    return revision, documents, chunks, embeddings


def _validate(
    revision: Revision,
    documents: tuple[Document, ...],
    chunks: tuple[Chunk, ...],
    embeddings: tuple[Embedding, ...],
) -> None:
    expected = dict(revision.document_hashes)
    by_id = {document.document_id: document for document in documents}
    if (
        len(expected) != len(revision.document_hashes)
        or len(by_id) != len(documents)
        or set(expected) != set(by_id)
        or len(chunks) != revision.chunk_count
        or len(embeddings) != revision.embedding_count
        or len(chunks) != len(embeddings)
    ):
        raise CorpusStorageError("PARTIAL_LOAD_OR_DUPLICATE")
    # Also enforce W0's identifier/hash contract before storing an unpublishable version.
    Versions.model_validate(
        {
            "corpusRevision": revision.revision_id,
            "configHash": revision.config_hash,
            "questionDictionaryVersion": revision.dictionary_version,
            "sourceRevocationSequence": 0,
        }
    )
    for document in documents:
        if (
            not document.normalized_text.strip()
            or document.eligibility_status != "PUBLIC"
            or document.content_hash != text_hash(document.normalized_text)
            or expected[document.document_id] != document.digest()
        ):
            raise CorpusStorageError("DOCUMENT_HASH_OR_ELIGIBILITY_MISMATCH")
    chunk_ids: set[UUID] = set()
    ordinals: set[tuple[UUID, int]] = set()
    for chunk in chunks:
        chunk_document = by_id.get(chunk.document_id)
        if chunk_document is None:
            raise CorpusStorageError("DOCUMENT_FK_MISMATCH")
        if (
            chunk.chunk_id in chunk_ids
            or (chunk.document_id, chunk.ordinal) in ordinals
            or chunk.ordinal < 0
            or not 0 <= chunk.start_offset < chunk.end_offset
            or chunk.end_offset > len(chunk_document.normalized_text)
            or chunk_document.normalized_text[chunk.start_offset : chunk.end_offset]
            != chunk.chunk_text
            or not chunk.chunk_text.strip()
            or not chunk.search_text.strip()
            or chunk.content_hash != text_hash(chunk.chunk_text)
        ):
            raise CorpusStorageError("CHUNK_HASH_OFFSET_OR_DUPLICATE")
        chunk_ids.add(chunk.chunk_id)
        ordinals.add((chunk.document_id, chunk.ordinal))
    if set(by_id) != {chunk.document_id for chunk in chunks}:
        raise CorpusStorageError("DOCUMENT_WITHOUT_CHUNKS")
    if len({item.chunk_id for item in embeddings}) != len(embeddings):
        raise CorpusStorageError("DUPLICATE_EMBEDDING")
    for embedding in embeddings:
        if (
            embedding.chunk_id not in chunk_ids
            or embedding.embedding_profile_id != revision.embedding_profile_id
            or len(embedding.values) != 384
            or not all(math.isfinite(value) for value in embedding.values)
            or abs(math.sqrt(sum(value * value for value in embedding.values)) - 1) > 0.0001
        ):
            raise CorpusStorageError("INVALID_EMBEDDING")
