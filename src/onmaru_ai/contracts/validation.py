"""Context checks required after DTO/schema validation at the Spring/AI boundary."""

from __future__ import annotations

import hashlib
import json
from typing import Literal

from .models import (
    ApprovedQueryPlan,
    Candidate,
    CandidateSet,
    Evidence,
    EvidenceSet,
    HardFilters,
    PlanProposal,
    ProgressEvent,
    SafeQueryRequest,
    SourceRevision,
    ValidatedProposal,
    Versions,
)

ViolationCode = Literal[
    "RUN_MISMATCH",
    "VERSION_MISMATCH",
    "PLAN_HASH_MISMATCH",
    "FILTER_EXPANSION",
    "FILTER_MISMATCH",
    "INVALID_PLAN",
    "SOURCE_REVOKED",
    "EVIDENCE_MISMATCH",
]


class ContractViolation(ValueError):
    """A safe machine-readable failure; never includes request or document text."""

    def __init__(self, code: ViolationCode) -> None:
        self.code = code
        super().__init__(code)


def compute_plan_hash(plan: PlanProposal) -> str:
    """Canonical UTF-8 JSON hash. See README for the cross-language wire algorithm."""
    body = plan.model_dump(mode="json", by_alias=True, exclude={"plan_hash", "semantic_query"})
    body["semanticQueryHash"] = (
        "sha256:" + hashlib.sha256(plan.semantic_query.encode("utf-8")).hexdigest()
        if plan.semantic_query is not None
        else None
    )
    canonical = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return "sha256:" + hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _versions_match(actual: Versions, expected: Versions, current: Versions | None) -> None:
    if actual != expected or (current is not None and actual != current):
        raise ContractViolation("VERSION_MISMATCH")


def _filter_subset(proposed: HardFilters, bounds: HardFilters) -> None:
    if proposed.filter_hash != bounds.filter_hash:
        raise ContractViolation("FILTER_MISMATCH")
    for field in ("place_ids", "region_codes", "category_codes"):
        upper = getattr(bounds, field)
        selected = getattr(proposed, field)
        if upper is not None and (selected is None or not set(selected) <= set(upper)):
            raise ContractViolation("FILTER_EXPANSION")
    if not set(bounds.pinned_place_ids) <= set(proposed.pinned_place_ids) or not set(
        bounds.excluded_place_ids
    ) <= set(proposed.excluded_place_ids):
        raise ContractViolation("FILTER_EXPANSION")


def validate_plan(
    request: SafeQueryRequest,
    plan: PlanProposal,
    *,
    current_versions: Versions | None = None,
) -> None:
    """Validate echoes and authority before Spring approves a plan (no side effects)."""
    if plan.run_id != request.run_id:
        raise ContractViolation("RUN_MISMATCH")
    _versions_match(plan.versions, request.versions, current_versions)
    _filter_subset(plan.proposed_filters, request.authority_bounds.filters)
    if plan.limits != request.limits or not set(plan.requested_canonical_fields) <= set(
        request.authority_bounds.allowed_canonical_fields
    ):
        raise ContractViolation("INVALID_PLAN")
    targets = set(plan.question_frame.target_place_ids)
    entities = set(plan.retrieval_expression.public_entity_ids)
    included = plan.proposed_filters.place_ids
    if (
        targets != entities
        or targets & set(plan.proposed_filters.excluded_place_ids)
        or (included is not None and not targets <= set(included))
        or set(plan.question_frame.subject_concept_codes)
        != set(plan.retrieval_expression.positive_concept_codes)
    ):
        raise ContractViolation("INVALID_PLAN")
    if compute_plan_hash(plan) != plan.plan_hash:
        raise ContractViolation("PLAN_HASH_MISMATCH")


def validate_approval(
    request: SafeQueryRequest,
    plan: PlanProposal,
    approved: ApprovedQueryPlan,
    *,
    current_versions: Versions | None = None,
) -> None:
    """An approval must echo the exact immutable proposal, including narrowed filters."""
    validate_plan(request, plan, current_versions=current_versions)
    if approved.run_id != plan.run_id:
        raise ContractViolation("RUN_MISMATCH")
    _versions_match(approved.versions, plan.versions, current_versions)
    if approved.approved_plan_hash != plan.plan_hash:
        raise ContractViolation("PLAN_HASH_MISMATCH")
    if approved.approved_filters != plan.proposed_filters:
        raise ContractViolation("FILTER_MISMATCH")
    if (
        approved.plan_version != plan.plan_version
        or approved.approved_route != plan.route
        or approved.approved_retrieval_mode != plan.retrieval_mode
        or approved.approved_canonical_fields != plan.requested_canonical_fields
        or approved.semantic_query != plan.semantic_query
    ):
        raise ContractViolation("INVALID_PLAN")


def _place_allowed(place_id: str, approved: ApprovedQueryPlan) -> bool:
    filters = approved.approved_filters
    return place_id not in filters.excluded_place_ids and (
        filters.place_ids is None or place_id in filters.place_ids
    )


def validate_artifact(
    artifact: CandidateSet | EvidenceSet | ValidatedProposal | ProgressEvent,
    approved: ApprovedQueryPlan,
    *,
    current_versions: Versions,
    revoked_sources: tuple[SourceRevision, ...] = (),
    evidence_set: EvidenceSet | None = None,
) -> None:
    """Reject stale/revoked or unapproved artifacts; this does not publish any result.

    Caller must provide the current Spring authority watermark. A stale sequence fails
    closed; re-fetching current eligibility is a later execution/final-validation concern.
    """
    if artifact.run_id != approved.run_id:
        raise ContractViolation("RUN_MISMATCH")
    if artifact.plan_hash != approved.approved_plan_hash:
        raise ContractViolation("PLAN_HASH_MISMATCH")
    if isinstance(artifact, ProgressEvent):
        return
    _versions_match(artifact.versions, approved.versions, current_versions)
    revoked = {(source.source_id, source.source_revision) for source in revoked_sources}
    sources: tuple[Candidate, ...] | tuple[Evidence, ...]
    if isinstance(artifact, CandidateSet):
        sources = artifact.candidates
    elif isinstance(artifact, EvidenceSet):
        sources = artifact.evidence
    else:
        if evidence_set is None:
            raise ContractViolation("EVIDENCE_MISMATCH")
        validate_artifact(
            evidence_set,
            approved,
            current_versions=current_versions,
            revoked_sources=revoked_sources,
        )
        registry = {item.evidence_id: item for item in evidence_set.evidence}
        for place in artifact.places:
            if not _place_allowed(place.place_id, approved):
                raise ContractViolation("FILTER_MISMATCH")
            for claim in place.reason_claims:
                if any(
                    ref not in registry or registry[ref].place_id != place.place_id
                    for ref in claim.evidence_ids
                ):
                    raise ContractViolation("EVIDENCE_MISMATCH")
        if any(
            ref not in registry for claim in artifact.summary_claims for ref in claim.evidence_ids
        ):
            raise ContractViolation("EVIDENCE_MISMATCH")
        return
    for source in sources:
        if (source.source_id, source.source_revision) in revoked:
            raise ContractViolation("SOURCE_REVOKED")
        if not _place_allowed(source.place_id, approved):
            raise ContractViolation("FILTER_MISMATCH")
