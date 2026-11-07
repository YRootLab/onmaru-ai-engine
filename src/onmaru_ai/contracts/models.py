"""W0 private DTOs. These describe proposals, never public SSE or publication authority."""

from __future__ import annotations

from collections import Counter
from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator
from pydantic.alias_generators import to_camel
from pydantic.config import JsonDict

from .vocabulary import (
    CLARIFICATION_QUESTIONS,
    ClaimKind,
    ClarificationQuestionCode,
    ConceptCode,
    FailureStage,
    PlanReasonCode,
)

Identifier = Annotated[
    str, Field(min_length=1, max_length=128, pattern=r"^[A-Za-z0-9][A-Za-z0-9._:-]*$")
]
Digest = Annotated[str, Field(pattern=r"^sha256:[a-f0-9]{64}$")]
RunId = Annotated[
    str, Field(pattern=r"^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$")
]
PositiveInt = Annotated[int, Field(ge=1, strict=True)]
NonnegativeInt = Annotated[int, Field(ge=0, strict=True)]
Ids = Annotated[
    tuple[Identifier, ...], Field(max_length=1000, json_schema_extra={"uniqueItems": True})
]
ReasonCodes = Annotated[
    tuple[PlanReasonCode, ...], Field(max_length=32, json_schema_extra={"uniqueItems": True})
]
PlaceIds = Annotated[
    tuple[Identifier, ...], Field(max_length=5, json_schema_extra={"uniqueItems": True})
]
EntityIds = Annotated[
    tuple[Identifier, ...], Field(max_length=2, json_schema_extra={"uniqueItems": True})
]
Concepts = Annotated[
    tuple[ConceptCode, ...], Field(max_length=4, json_schema_extra={"uniqueItems": True})
]
NegativeConcepts = Annotated[
    tuple[ConceptCode, ...], Field(max_length=2, json_schema_extra={"uniqueItems": True})
]
SemanticQuery = Annotated[str, Field(min_length=1, max_length=240)]
CanonicalField = Literal["PUBLIC_ADDRESS", "REGION_CODE", "CATEGORY_CODE", "PUBLIC_STATUS"]
CanonicalFields = Annotated[
    tuple[CanonicalField, ...], Field(max_length=4, json_schema_extra={"uniqueItems": True})
]
Route = Literal[
    "SQL_ONLY", "LEXICAL_ONLY", "DENSE_ONLY", "HYBRID", "SQL_PLUS_RETRIEVAL", "CLARIFY_OR_SCOPE"
]
RetrievalMode = Literal["NONE", "LEXICAL_ONLY", "DENSE_ONLY", "HYBRID"]
Stage = Literal[
    "PREPARING_INPUT", "RETRIEVING", "SELECTING_EVIDENCE", "GENERATING", "CHECKING_OUTPUT"
]
RetrievalStatus = Literal["NOT_RUN", "COMPLETE", "DEGRADED", "NO_EVIDENCE", "FAILED"]


class ClosedModel(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, alias_generator=to_camel, allow_inf_nan=False
    )

    @field_validator("*")
    @classmethod
    def unique_scalar_arrays(cls, value: object) -> object:
        if (
            isinstance(value, tuple)
            and all(isinstance(item, str) for item in value)
            and len(value) != len(set(value))
        ):
            raise ValueError("array values must be unique")
        return value


class Versions(ClosedModel):
    corpus_revision: Identifier
    config_hash: Digest
    question_dictionary_version: Identifier
    source_revocation_sequence: NonnegativeInt


class RetrievalLimits(ClosedModel):
    bm25_k: Literal[20] = Field(alias="bm25K")
    vector_k: Literal[20] = Field(alias="vectorK")
    rerank_k: Literal[30] = Field(alias="rerankK")
    evidence_k: Literal[12] = Field(alias="evidenceK")
    max_places: Literal[5]


class HardFilters(ClosedModel):
    filter_hash: Digest
    public_only: Literal[True]
    place_ids: Ids | None
    region_codes: Ids | None
    category_codes: Ids | None
    pinned_place_ids: PlaceIds
    excluded_place_ids: Ids

    @field_validator("public_only", mode="before")
    @classmethod
    def actual_public_boolean(cls, value: object) -> object:
        if value is not True:
            raise ValueError("publicOnly must be the boolean true")
        return value

    @model_validator(mode="after")
    def consistent_places(self) -> Self:
        if set(self.pinned_place_ids) & set(self.excluded_place_ids):
            raise ValueError("pinned places cannot be excluded")
        if self.place_ids is not None and not set(self.pinned_place_ids) <= set(self.place_ids):
            raise ValueError("pinned places must be included")
        return self


class ConfirmedContext(ClosedModel):
    region_code: Identifier | None
    pinned_place_ids: PlaceIds
    excluded_place_ids: Ids
    last_confirmed_place_ids: PlaceIds


class AuthorityBounds(ClosedModel):
    filters: HardFilters
    allowed_canonical_fields: CanonicalFields


class SafeQueryRequest(ClosedModel):
    schema_version: Literal["ai-safe-query.v1"]
    run_id: RunId
    safe_query: SemanticQuery
    confirmed_context: ConfirmedContext
    authority_bounds: AuthorityBounds
    versions: Versions
    limits: RetrievalLimits


class QuestionFrame(ClosedModel):
    operation: Literal["RECOMMEND", "EXPLAIN", "COMPARE", "REFINE"]
    target_place_ids: EntityIds
    subject_concept_codes: Concepts


class RetrievalExpression(ClosedModel):
    positive_concept_codes: Concepts
    negative_concept_codes: NegativeConcepts
    public_entity_ids: EntityIds

    @model_validator(mode="after")
    def noncontradictory(self) -> Self:
        if set(self.positive_concept_codes) & set(self.negative_concept_codes):
            raise ValueError("positive and negative concepts must not overlap")
        return self


class Clarification(ClosedModel):
    model_config = ConfigDict(
        json_schema_extra={
            "allOf": [
                {
                    "if": {"properties": {"reason": {"const": reason}}},
                    "then": {"properties": {"questionCode": {"const": question.value}}},
                }
                for reason, question in CLARIFICATION_QUESTIONS.items()
            ]
        }
    )
    reason: Literal[
        "AMBIGUOUS_TARGET", "CONFLICTING_CONDITIONS", "UNSUPPORTED_SCOPE", "SEMANTIC_LOSS"
    ]
    question_code: ClarificationQuestionCode

    @model_validator(mode="after")
    def matching_question_code(self) -> Self:
        if self.question_code != CLARIFICATION_QUESTIONS[self.reason]:
            raise ValueError("clarification reason and questionCode must match")
        return self


def route_schema() -> JsonDict:
    """Express route/mode and non-executable clarification in shared JSON Schema too."""
    specifications: list[tuple[str, JsonDict]] = [
        (
            "SQL_ONLY",
            {
                "retrievalMode": {"const": "NONE"},
                "semanticQuery": {"type": "null"},
                "clarification": {"type": "null"},
                "requestedCanonicalFields": {"minItems": 1},
            },
        ),
        (
            "LEXICAL_ONLY",
            {
                "retrievalMode": {"const": "LEXICAL_ONLY"},
                "semanticQuery": {"type": "string"},
                "clarification": {"type": "null"},
                "requestedCanonicalFields": {"maxItems": 0},
            },
        ),
        (
            "DENSE_ONLY",
            {
                "retrievalMode": {"const": "DENSE_ONLY"},
                "semanticQuery": {"type": "string"},
                "clarification": {"type": "null"},
                "requestedCanonicalFields": {"maxItems": 0},
            },
        ),
        (
            "HYBRID",
            {
                "retrievalMode": {"const": "HYBRID"},
                "semanticQuery": {"type": "string"},
                "clarification": {"type": "null"},
                "requestedCanonicalFields": {"maxItems": 0},
            },
        ),
        (
            "SQL_PLUS_RETRIEVAL",
            {
                "retrievalMode": {"enum": ["LEXICAL_ONLY", "DENSE_ONLY", "HYBRID"]},
                "semanticQuery": {"type": "string"},
                "clarification": {"type": "null"},
                "requestedCanonicalFields": {"minItems": 1},
            },
        ),
        (
            "CLARIFY_OR_SCOPE",
            {
                "retrievalMode": {"const": "NONE"},
                "semanticQuery": {"type": "null"},
                "clarification": {"type": "object"},
                "requestedCanonicalFields": {"maxItems": 0},
            },
        ),
    ]
    return {
        "allOf": [
            {"if": {"properties": {"route": {"const": route}}}, "then": {"properties": props}}
            for route, props in specifications
        ]
    }


class PlanProposal(ClosedModel):
    model_config = ConfigDict(json_schema_extra=route_schema())
    schema_version: Literal["ai-plan-proposal.v1"]
    plan_version: Literal["ai-query-plan.v1"]
    run_id: RunId
    route: Route
    retrieval_mode: RetrievalMode
    reason_codes: Annotated[ReasonCodes, Field(min_length=1)]
    question_frame: QuestionFrame
    retrieval_expression: RetrievalExpression
    requested_canonical_fields: CanonicalFields
    proposed_filters: HardFilters
    semantic_query: SemanticQuery | None
    versions: Versions
    limits: RetrievalLimits
    clarification: Clarification | None
    plan_hash: Digest

    @model_validator(mode="after")
    def consistent_route(self) -> Self:
        expected = {
            "SQL_ONLY": "NONE",
            "CLARIFY_OR_SCOPE": "NONE",
            "LEXICAL_ONLY": "LEXICAL_ONLY",
            "DENSE_ONLY": "DENSE_ONLY",
            "HYBRID": "HYBRID",
        }
        if self.route == "SQL_PLUS_RETRIEVAL":
            valid_mode = self.retrieval_mode != "NONE"
        else:
            valid_mode = self.retrieval_mode == expected[self.route]
        sql = self.route in ("SQL_ONLY", "SQL_PLUS_RETRIEVAL")
        clarify = self.route == "CLARIFY_OR_SCOPE"
        if (
            not valid_mode
            or bool(self.requested_canonical_fields) != sql
            or (self.semantic_query is not None) != (self.retrieval_mode != "NONE")
            or (self.clarification is not None) != clarify
        ):
            raise ValueError("route, mode, fields, semantic query and clarification must agree")
        return self


class ApprovedQueryPlan(ClosedModel):
    schema_version: Literal["ai-approved-plan.v1"]
    plan_version: Literal["ai-query-plan.v1"]
    run_id: RunId
    approved_plan_hash: Digest
    approved_route: Route
    approved_retrieval_mode: RetrievalMode
    approved_filters: HardFilters
    approved_canonical_fields: CanonicalFields
    semantic_query: SemanticQuery | None
    versions: Versions
    query_grant_id: Identifier | None

    @model_validator(mode="after")
    def grant_only_for_sql(self) -> Self:
        if (self.query_grant_id is not None) != (
            self.approved_route in ("SQL_ONLY", "SQL_PLUS_RETRIEVAL")
        ):
            raise ValueError("SQL routes require a grant; other routes forbid one")
        return self


class RunArtifact(ClosedModel):
    run_id: RunId
    plan_hash: Digest
    versions: Versions


class SourceRevision(ClosedModel):
    source_id: Identifier
    source_revision: Identifier


class Candidate(SourceRevision):
    chunk_id: Identifier
    place_id: Identifier
    rank: PositiveInt
    score: Annotated[float, Field(strict=True)]
    exclusion_reason: (
        Literal["NOT_PUBLIC", "EXCLUDED", "FILTER_MISMATCH", "SOURCE_REVOKED", "REVISION_MISMATCH"]
        | None
    )


class CandidateSet(RunArtifact):
    schema_version: Literal["ai-candidate-set.v1"]
    stage: Literal["LEXICAL", "DENSE", "FUSION", "RERANK"]
    candidates: Annotated[tuple[Candidate, ...], Field(max_length=40)]
    retrieval_status: RetrievalStatus
    latency_ms: NonnegativeInt

    @model_validator(mode="after")
    def unique_candidates(self) -> Self:
        if len({item.chunk_id for item in self.candidates}) != len(self.candidates):
            raise ValueError("candidate chunk IDs must be unique")
        cap = 20 if self.stage in ("LEXICAL", "DENSE") else 30
        if len(self.candidates) > cap:
            raise ValueError("candidate stage limit exceeded")
        return self


class Evidence(SourceRevision):
    evidence_id: Identifier
    chunk_id: Identifier
    place_id: Identifier
    start_offset: NonnegativeInt
    end_offset: PositiveInt

    @model_validator(mode="after")
    def ordered_offsets(self) -> Self:
        if self.end_offset <= self.start_offset:
            raise ValueError("source span must be nonempty")
        return self


class EvidenceSet(RunArtifact):
    schema_version: Literal["ai-evidence-set.v1"]
    allowed_place_ids: PlaceIds
    evidence: Annotated[tuple[Evidence, ...], Field(max_length=12)]

    @model_validator(mode="after")
    def bounded_unique_evidence(self) -> Self:
        if len({item.evidence_id for item in self.evidence}) != len(self.evidence):
            raise ValueError("evidence IDs must be unique")
        if len({item.chunk_id for item in self.evidence}) != len(self.evidence):
            raise ValueError("evidence chunk IDs must be unique")
        if any(count > 2 for count in Counter(item.place_id for item in self.evidence).values()):
            raise ValueError("at most two evidence chunks per place")
        if {item.place_id for item in self.evidence} != set(self.allowed_place_ids):
            raise ValueError("evidence places must equal allowed places")
        return self


class Claim(ClosedModel):
    claim_id: Identifier
    text: Annotated[str, Field(min_length=1, max_length=1000)]
    kind: ClaimKind
    evidence_ids: Annotated[
        tuple[Identifier, ...],
        Field(min_length=1, max_length=3, json_schema_extra={"uniqueItems": True}),
    ]


class PlaceClaims(ClosedModel):
    place_id: Identifier
    reason_claims: Annotated[tuple[Claim, ...], Field(min_length=1, max_length=12)]


class ValidatedProposal(RunArtifact):
    schema_version: Literal["ai-validated-proposal.v1"]
    candidate_place_ids: PlaceIds
    places: Annotated[tuple[PlaceClaims, ...], Field(max_length=5)]
    summary_claims: Annotated[tuple[Claim, ...], Field(max_length=12)]
    retrieval_status: RetrievalStatus
    generation_status: Literal["NOT_RUN", "GENERATED", "REJECTED", "FAILED"]
    failure_stage: FailureStage | None

    @model_validator(mode="after")
    def unique_claims_and_places(self) -> Self:
        ids = [place.place_id for place in self.places]
        if len(set(ids)) != len(ids) or tuple(ids) != self.candidate_place_ids:
            raise ValueError("place IDs must uniquely match the candidate order")
        claims = [claim.claim_id for place in self.places for claim in place.reason_claims]
        claims.extend(claim.claim_id for claim in self.summary_claims)
        if len(set(claims)) != len(claims):
            raise ValueError("claim IDs must be unique")
        return self


class ProgressEvent(ClosedModel):
    schema_version: Literal["internal.ai.progress.v1", "ai-progress.v1"]
    run_id: RunId
    plan_hash: Digest
    ordinal: PositiveInt
    stage: Stage
