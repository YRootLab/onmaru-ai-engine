from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from uuid import UUID


def text_hash(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def _canonical(value: object) -> str:
    def encode(item: object) -> str:
        if isinstance(item, UUID):
            return str(item)
        if isinstance(item, datetime) and item.tzinfo is not None:
            return item.astimezone(UTC).isoformat().replace("+00:00", "Z")
        raise ValueError("unsupported value or naive timestamp")

    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
        default=encode,
    )


@dataclass(frozen=True)
class Document:
    document_id: UUID
    place_id: UUID
    source_type: str
    source_id: str
    source_revision: str
    title: str
    published_at: datetime
    collected_at: datetime
    license_code: str
    region_code: str
    category_code: str
    normalized_text: str
    content_hash: str
    eligibility_status: str = "PUBLIC"

    def digest(self) -> str:
        """Storage manifest digest binds provenance as well as text (not the export wire hash)."""
        return text_hash(_canonical(asdict(self)))


@dataclass(frozen=True)
class Chunk:
    chunk_id: UUID
    document_id: UUID
    ordinal: int
    start_offset: int
    end_offset: int
    chunk_text: str
    content_hash: str
    search_text: str


@dataclass(frozen=True)
class Embedding:
    chunk_id: UUID
    embedding_profile_id: str
    values: tuple[float, ...]


@dataclass(frozen=True)
class Revision:
    revision_id: str
    source_revision: str
    embedding_profile_id: str
    chunker_version: str
    dictionary_version: str
    config_hash: str
    document_hashes: tuple[tuple[UUID, str], ...]
    chunk_count: int
    embedding_count: int

    def canonical_manifest(self) -> str:
        values = asdict(self)
        values["document_hashes"] = sorted(self.document_hashes, key=lambda item: str(item[0]))
        return _canonical(values)

    @property
    def manifest_hash(self) -> str:
        return text_hash(self.canonical_manifest())
