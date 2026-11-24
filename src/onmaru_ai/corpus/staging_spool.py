"""Disk-backed checkpoint spool for bounded corpus embedding and database staging."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

from onmaru_ai.storage.models import Chunk, Document, Embedding, Revision


class CorpusStagingSpool:
    """Persist one validated per-place bundle at a time for safe restart/resume."""

    def __init__(
        self,
        path: str | Path,
        revision_id: str,
        *,
        run_timestamp: datetime | None = None,
    ) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.execute("PRAGMA journal_mode=WAL")
        self.connection.execute("PRAGMA synchronous=FULL")
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS revision_meta (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS ingestion_meta (
                singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                run_timestamp TEXT NOT NULL,
                catalog_revision TEXT
            );
            CREATE TABLE IF NOT EXISTS documents (
                document_id TEXT PRIMARY KEY,
                digest TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS chunks (
                chunk_id TEXT PRIMARY KEY,
                document_id TEXT NOT NULL,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS embeddings (
                chunk_id TEXT PRIMARY KEY,
                payload TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS checkpoints (
                place_id TEXT PRIMARY KEY,
                completed_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        row = self.connection.execute(
            "SELECT payload FROM revision_meta WHERE singleton=1"
        ).fetchone()
        if row is not None and json.loads(row[0])["revision_id"] != revision_id:
            self.connection.close()
            raise ValueError("spool revision ID does not match the requested revision")
        timestamp_row = self.connection.execute(
            "SELECT run_timestamp FROM ingestion_meta WHERE singleton=1"
        ).fetchone()
        requested_timestamp = run_timestamp or datetime.now(UTC)
        if timestamp_row is None:
            with self.connection:
                self.connection.execute(
                    "INSERT INTO ingestion_meta(singleton,run_timestamp) VALUES(1,?)",
                    (requested_timestamp.isoformat(),),
                )
            self.run_timestamp = requested_timestamp
        else:
            self.run_timestamp = datetime.fromisoformat(str(timestamp_row[0]))
            if run_timestamp is not None and self.run_timestamp != run_timestamp:
                self.connection.close()
                raise ValueError("spool timestamp does not match the requested timestamp")
        self.revision_id = revision_id

    def has_place(self, place_id: str) -> bool:
        return (
            self.connection.execute(
                "SELECT 1 FROM checkpoints WHERE place_id=?", (place_id,)
            ).fetchone()
            is not None
        )

    def bind_catalog_revision(self, source_revision: str) -> None:
        if not source_revision.strip():
            raise ValueError("catalog source revision must not be blank")
        row = self.connection.execute(
            "SELECT catalog_revision FROM ingestion_meta WHERE singleton=1"
        ).fetchone()
        current = None if row is None else row[0]
        if current is not None and current != source_revision:
            raise ValueError("catalog source revision changed; use a new staging spool")
        if current == source_revision:
            return
        with self.connection:
            self.connection.execute(
                "UPDATE ingestion_meta SET catalog_revision=? WHERE singleton=1",
                (source_revision,),
            )

    def last_place_id(self) -> str | None:
        row = self.connection.execute(
            "SELECT place_id FROM checkpoints ORDER BY place_id DESC LIMIT 1"
        ).fetchone()
        return None if row is None else str(row[0])

    def append(
        self,
        place_id: str,
        revision: Revision,
        documents: tuple[Document, ...],
        chunks: tuple[Chunk, ...],
        embeddings: tuple[Embedding, ...],
    ) -> None:
        if revision.revision_id != self.revision_id:
            raise ValueError("bundle revision does not match spool revision")
        if self.has_place(place_id):
            raise ValueError("place already exists in corpus spool")
        meta = {
            "revision_id": revision.revision_id,
            "source_revision": revision.source_revision,
            "embedding_profile_id": revision.embedding_profile_id,
            "chunker_version": revision.chunker_version,
            "dictionary_version": revision.dictionary_version,
            "config_hash": revision.config_hash,
        }
        current = self.connection.execute(
            "SELECT payload FROM revision_meta WHERE singleton=1"
        ).fetchone()
        if current is not None and json.loads(current[0]) != meta:
            raise ValueError("spool revision metadata changed during ingestion")

        with self.connection:
            if current is None:
                self.connection.execute(
                    "INSERT INTO revision_meta(singleton,payload) VALUES(1,?)",
                    (json.dumps(meta, sort_keys=True),),
                )
            self.connection.executemany(
                "INSERT INTO documents(document_id,digest,payload) VALUES(?,?,?)",
                [
                    (str(item.document_id), item.digest(), _encode(item))
                    for item in documents
                ],
            )
            self.connection.executemany(
                "INSERT INTO chunks(chunk_id,document_id,payload) VALUES(?,?,?)",
                [
                    (str(item.chunk_id), str(item.document_id), _encode(item))
                    for item in chunks
                ],
            )
            self.connection.executemany(
                "INSERT INTO embeddings(chunk_id,payload) VALUES(?,?)",
                [(str(item.chunk_id), _encode(item)) for item in embeddings],
            )
            self.connection.execute(
                "INSERT INTO checkpoints(place_id) VALUES(?)", (place_id,)
            )

    def revision(self) -> Revision:
        row = self.connection.execute(
            "SELECT payload FROM revision_meta WHERE singleton=1"
        ).fetchone()
        if row is None:
            raise ValueError("corpus spool is empty")
        meta = json.loads(row[0])
        document_hashes = tuple(
            (UUID(document_id), str(digest))
            for document_id, digest in self.connection.execute(
                "SELECT document_id,digest FROM documents ORDER BY document_id"
            )
        )
        chunk_count = int(self.connection.execute("SELECT count(*) FROM chunks").fetchone()[0])
        embedding_count = int(
            self.connection.execute("SELECT count(*) FROM embeddings").fetchone()[0]
        )
        return Revision(
            **meta,
            document_hashes=document_hashes,
            chunk_count=chunk_count,
            embedding_count=embedding_count,
        )

    def documents(self, batch_size: int = 500) -> Iterator[Document]:
        yield from self._read(
            "SELECT payload FROM documents ORDER BY document_id", Document, batch_size
        )

    def get_document(self, document_id: UUID) -> Document | None:
        row = self.connection.execute(
            "SELECT payload FROM documents WHERE document_id=?", (str(document_id),)
        ).fetchone()
        return None if row is None else _decode(row[0], Document)

    def chunks(self, batch_size: int = 500) -> Iterator[Chunk]:
        yield from self._read("SELECT payload FROM chunks ORDER BY chunk_id", Chunk, batch_size)

    def embeddings(self, batch_size: int = 500) -> Iterator[Embedding]:
        yield from self._read(
            "SELECT payload FROM embeddings ORDER BY chunk_id", Embedding, batch_size
        )

    def counts(self) -> tuple[int, int, int]:
        return tuple(
            int(self.connection.execute(f"SELECT count(*) FROM {table}").fetchone()[0])
            for table in ("documents", "chunks", "embeddings")
        )  # type: ignore[return-value]

    def close(self) -> None:
        self.connection.close()

    def _read(self, query: str, model: type[Any], batch_size: int) -> Iterator[Any]:
        cursor = self.connection.execute(query)
        while rows := cursor.fetchmany(batch_size):
            for (payload,) in rows:
                yield _decode(payload, model)

    def __enter__(self) -> CorpusStagingSpool:
        return self

    def __exit__(self, *_exc: object) -> None:
        self.close()


def _encode(value: Document | Chunk | Embedding) -> str:
    return json.dumps(asdict(value), default=_json_default, ensure_ascii=False)


def _json_default(value: object) -> str:
    if isinstance(value, (UUID, datetime)):
        return value.isoformat() if isinstance(value, datetime) else str(value)
    raise TypeError(f"unsupported spool value: {type(value).__name__}")


def _decode(payload: str, model: type[Any]) -> Any:
    data = json.loads(payload)
    for key, value in tuple(data.items()):
        if (
            key.endswith("_id")
            and isinstance(value, str)
            and key in {"document_id", "place_id", "chunk_id"}
        ):
            data[key] = UUID(value)
    if model is Document:
        data["published_at"] = datetime.fromisoformat(data["published_at"])
        data["collected_at"] = datetime.fromisoformat(data["collected_at"])
    elif model is Embedding:
        data["values"] = tuple(data["values"])
    return model(**data)
