"""Fail-closed eligibility for Spring's public projection metadata (W1)."""

from __future__ import annotations

from typing import Annotated

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StrictBool
from pydantic.alias_generators import to_camel

SourceIdentifier = Annotated[str, Field(min_length=1, strict=True, pattern=r"^\S+$")]
SourceKey = tuple[str, str, str]
Digest = Annotated[str, Field(strict=True, pattern=r"^sha256:[a-f0-9]{64}$")]


class ProjectionModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, alias_generator=to_camel)


class PublicSourceProjection(ProjectionModel):
    """One immutable source revision and its current publication assertions.

    content_url is a reference for the later preparation stage; W1 never fetches it.
    Unknown source types are parsed but excluded by SourcePolicy.
    """

    document_id: SourceIdentifier
    place_id: SourceIdentifier
    source_type: SourceIdentifier
    source_id: SourceIdentifier
    source_revision: SourceIdentifier
    published_at: AwareDatetime
    document_hash: Digest
    content_url: Annotated[str, Field(min_length=1, strict=True)]
    license_code: str | None
    license_verified: StrictBool
    publication_eligible: StrictBool
    public: StrictBool
    revoked: StrictBool
    snapshot_status: str | None
    review_status: str | None

    @property
    def source_key(self) -> SourceKey:
        return self.source_type, self.source_id, self.source_revision


class SourcePolicy:
    """Only explicit rights and source-specific public verification permit preparation."""

    @staticmethod
    def permits(source: PublicSourceProjection) -> bool:
        if (
            not source.public
            or not source.publication_eligible
            or source.revoked
            or not source.license_verified
            or not source.license_code
            or not source.license_code.strip()
        ):
            return False
        if source.source_type == "TOUR_API":
            return source.snapshot_status == "OK"
        if source.source_type == "K_CONTENTS":
            return source.review_status == "VERIFIED"
        return source.source_type == "PLACE_CANONICAL"
