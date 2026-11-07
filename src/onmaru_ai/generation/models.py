"""Private generation inputs; reviewed facts come from a trusted registry, never the LLM."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field

from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    ClaimKind,
    EvidenceSet,
    SourceRevision,
    ValidatedProposal,
    Versions,
)
from onmaru_ai.contracts.models import Claim, ClosedModel, Identifier


class SourceDocument(SourceRevision):
    corpus_revision: Identifier
    text: Annotated[str, Field(min_length=1, max_length=200_000)]


class VerifiedRelation(ClosedModel):
    relation_id: Identifier
    subject_id: Identifier
    predicate: Literal["FILMING_LOCATION", "SETTING", "CREATED_BY", "ASSOCIATED_WITH"]
    object_id: Identifier
    polarity: Literal["AFFIRMED", "NEGATED"]


class VerifiedFact(ClosedModel):
    """A registry-reviewed atomic assertion, including all qualifiers in its exact text.

    factId is stable within this generation input.
    Natural-language support is a caller trust boundary, not inferred by this model.
    """

    text: Annotated[str, Field(min_length=1, max_length=1000)]
    kind: ClaimKind
    evidence_ids: Annotated[tuple[Identifier, ...], Field(min_length=1, max_length=3)]
    fact_id: Identifier
    place_id: Identifier
    support_type: Literal[
        "CANONICAL_VALUE",
        "HISTORICAL_FACT",
        "VERIFIED_RELATION",
        "CONDITIONAL_PREFERENCE",
        "INTERPRETATION",
    ]
    time_scope: Annotated[str, Field(min_length=1, max_length=100)]
    relation: VerifiedRelation | None


class GenerationInput(ClosedModel):
    operation: Literal["RECOMMEND", "EXPLAIN", "COMPARE", "REFINE", "CONTENT_CONNECTION"]
    approved_plan: ApprovedQueryPlan
    evidence_set: EvidenceSet
    current_versions: Versions
    revoked_sources: Annotated[tuple[SourceRevision, ...], Field(max_length=1000)]
    documents: Annotated[tuple[SourceDocument, ...], Field(max_length=12)]
    verified_facts: Annotated[tuple[VerifiedFact, ...], Field(max_length=24)]


class ProposedClaim(Claim):
    fact_id: Identifier


class ProposedPlace(ClosedModel):
    place_id: Identifier
    reason_claims: Annotated[tuple[ProposedClaim, ...], Field(min_length=1, max_length=12)]


class ModelProposal(ClosedModel):
    places: Annotated[tuple[ProposedPlace, ...], Field(max_length=5)]
    summary_claims: Annotated[tuple[ProposedClaim, ...], Field(max_length=12)]


class GenerationFallback(StrEnum):
    NO_EVIDENCE = "NO_EVIDENCE"
    NO_SUPPORTED_FACTS = "NO_SUPPORTED_FACTS"
    INVALID_EVIDENCE = "INVALID_EVIDENCE"
    INVALID_OUTPUT = "INVALID_OUTPUT"
    PROVIDER_TIMEOUT = "PROVIDER_TIMEOUT"
    PROVIDER_RATE_LIMITED = "PROVIDER_RATE_LIMITED"
    PROVIDER_UNAVAILABLE = "PROVIDER_UNAVAILABLE"
    CANCELLED = "CANCELLED"


@dataclass(frozen=True)
class GenerationResult:
    proposal: ValidatedProposal
    fallback: GenerationFallback | None
    held_claim_count: int = 0
