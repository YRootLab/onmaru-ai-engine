"""W1 manifest intake, independent of legacy REST activation and online requests.

This in-memory receiver returns preparation inputs only. It does not publish a corpus,
fetch bodies, or provide W6's durable revocation/runtime freshness enforcement.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Annotated, Literal, Self

from pydantic import AwareDatetime, Field, ValidationError, model_validator

from .source_policy import (
    Digest,
    ProjectionModel,
    PublicSourceProjection,
    SourceIdentifier,
    SourceKey,
    SourcePolicy,
)

Sequence = Annotated[int, Field(ge=0, strict=True)]


class SourceTombstone(ProjectionModel):
    sequence: Annotated[int, Field(ge=1, strict=True)]
    scope: Literal["SOURCE_REVISION", "PLACE"]
    source_type: SourceIdentifier | None
    source_id: SourceIdentifier | None
    source_revision: SourceIdentifier | None
    place_id: SourceIdentifier | None
    revoked_at: AwareDatetime
    reason_code: SourceIdentifier

    @model_validator(mode="after")
    def validate_target(self) -> Self:
        source_target = (self.source_type, self.source_id, self.source_revision)
        if self.scope == "SOURCE_REVISION":
            if any(value is None for value in source_target) or self.place_id is not None:
                raise ValueError("SOURCE_REVISION tombstone requires only a complete source key")
        elif self.place_id is None or any(value is not None for value in source_target):
            raise ValueError("PLACE tombstone requires only placeId")
        return self


class PublicProjectionManifest(ProjectionModel):
    contract_version: Literal["1.0"]
    revision_id: SourceIdentifier
    source_revision: SourceIdentifier
    published_at: AwareDatetime
    manifest_hash: Digest
    document_count: Sequence
    revocation_sequence: Sequence
    documents: tuple[PublicSourceProjection, ...]
    tombstones: tuple[SourceTombstone, ...]


@dataclass(frozen=True)
class SourceSyncResult:
    status: Literal["PREPARED", "DUPLICATE", "REJECTED"]
    revision_id: str | None = None
    source_revision: str | None = None
    manifest_hash: str | None = None
    prepared_documents: tuple[PublicSourceProjection, ...] = ()
    excluded_document_ids: tuple[str, ...] = ()
    error_code: str | None = None


class SourceManifestReceiver:
    """Serial, process-local intake. Reuse one instance across manifest deliveries.

    All validation happens before committing intake state. Replays never requeue
    preparation or move latest_revision_id backwards. Opaque source revisions are
    identified by equality; publishedAt orders manifest revisions.
    """

    def __init__(self) -> None:
        self._manifests: dict[str, PublicProjectionManifest] = {}
        self._latest: PublicProjectionManifest | None = None
        self._events: dict[int, SourceTombstone] = {}
        self._source_revocations: set[SourceKey] = set()
        self._place_revocations: set[str] = set()
        self._source_hashes: dict[tuple[SourceKey, str], str] = {}
        self._watermark = 0

    @property
    def watermark(self) -> int:
        return self._watermark

    @property
    def latest_revision_id(self) -> str | None:
        return self._latest.revision_id if self._latest is not None else None

    def receive(self, payload: Mapping[str, object]) -> SourceSyncResult:
        try:
            manifest = PublicProjectionManifest.model_validate(payload)
            canonical = json.dumps(
                {key: value for key, value in payload.items() if key != "manifestHash"},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8")
        except (ValidationError, TypeError, ValueError):
            return SourceSyncResult(status="REJECTED", error_code="MANIFEST_INVALID")

        def result(
            status: Literal["PREPARED", "DUPLICATE", "REJECTED"],
            *,
            error_code: str | None = None,
            prepared: tuple[PublicSourceProjection, ...] = (),
            excluded: tuple[str, ...] = (),
        ) -> SourceSyncResult:
            return SourceSyncResult(
                status=status,
                revision_id=manifest.revision_id,
                source_revision=manifest.source_revision,
                manifest_hash=manifest.manifest_hash,
                prepared_documents=prepared,
                excluded_document_ids=excluded,
                error_code=error_code,
            )

        if manifest.manifest_hash != f"sha256:{hashlib.sha256(canonical).hexdigest()}":
            return result("REJECTED", error_code="MANIFEST_HASH_MISMATCH")
        error = self._validate(manifest)
        if error is not None:
            return result("REJECTED", error_code=error)
        if manifest.revision_id in self._manifests:
            return result("DUPLICATE")

        source_revocations = self._source_revocations.copy()
        place_revocations = self._place_revocations.copy()
        for event in manifest.tombstones:
            if event.scope == "PLACE":
                assert event.place_id is not None  # validated by SourceTombstone
                place_revocations.add(event.place_id)
            else:
                assert event.source_type is not None
                assert event.source_id is not None
                assert event.source_revision is not None
                source_revocations.add((event.source_type, event.source_id, event.source_revision))
        prepared = tuple(
            source
            for source in manifest.documents
            if SourcePolicy.permits(source)
            and source.source_key not in source_revocations
            and source.place_id not in place_revocations
        )
        prepared_ids = {source.document_id for source in prepared}
        excluded = tuple(
            source.document_id
            for source in manifest.documents
            if source.document_id not in prepared_ids
        )

        self._source_revocations = source_revocations
        self._place_revocations = place_revocations
        self._events.update((event.sequence, event) for event in manifest.tombstones)
        self._watermark = manifest.revocation_sequence
        self._source_hashes.update(
            ((source.source_key, source.place_id), source.document_hash)
            for source in manifest.documents
        )
        self._manifests[manifest.revision_id] = manifest
        self._latest = manifest
        return result("PREPARED", prepared=prepared, excluded=excluded)

    def _validate(self, manifest: PublicProjectionManifest) -> str | None:
        if manifest.document_count != len(manifest.documents):
            return "MANIFEST_DOCUMENT_COUNT_MISMATCH"
        if len({doc.document_id for doc in manifest.documents}) != len(manifest.documents):
            return "MANIFEST_DUPLICATE_DOCUMENT"
        identities = {(doc.source_key, doc.place_id) for doc in manifest.documents}
        if len(identities) != len(manifest.documents):
            return "MANIFEST_DUPLICATE_SOURCE"
        existing = self._manifests.get(manifest.revision_id)
        if existing is not None:
            return (
                None
                if existing.manifest_hash == manifest.manifest_hash
                else "MANIFEST_REVISION_CONFLICT"
            )
        if self._latest is not None and manifest.published_at <= self._latest.published_at:
            return "MANIFEST_OUT_OF_ORDER"
        if manifest.revocation_sequence < self._watermark:
            return "TOMBSTONE_SEQUENCE_REVERSED"
        sequences = [event.sequence for event in manifest.tombstones]
        if sequences != sorted(set(sequences)):
            return "TOMBSTONE_SEQUENCE_OUT_OF_ORDER"
        expected = self._watermark + 1
        for event in manifest.tombstones:
            if event.sequence <= self._watermark:
                if self._events.get(event.sequence) != event:
                    return "TOMBSTONE_SEQUENCE_CONFLICT"
            elif event.sequence != expected:
                return "TOMBSTONE_SEQUENCE_GAP"
            else:
                expected += 1
        if expected - 1 != manifest.revocation_sequence:
            return "TOMBSTONE_SEQUENCE_GAP"
        for source in manifest.documents:
            previous = self._source_hashes.get((source.source_key, source.place_id))
            if previous is not None and previous != source.document_hash:
                return "SOURCE_REVISION_CONFLICT"
        return None
