"""Pure checks for an issued plan and a Spring-approved execution."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta

from onmaru_ai.contracts import ApprovedQueryPlan, ContractViolation, PlanProposal, Versions
from onmaru_ai.contracts.models import CanonicalField, HardFilters, RetrievalMode, Route


def semantic_digest(query: str | None) -> str | None:
    return hashlib.sha256(query.encode()).hexdigest() if query is not None else None


@dataclass(frozen=True)
class PlanBinding:
    """Transient authority metadata; never retain safeQuery or semanticQuery text."""

    run_id: str
    plan_hash: str
    route: Route
    mode: RetrievalMode
    filters: HardFilters
    fields: tuple[CanonicalField, ...]
    semantic_hash: str | None
    versions: Versions
    trace_id: str
    expires_at: datetime

    @classmethod
    def from_plan(cls, plan: PlanProposal, trace_id: str, expires_at: datetime) -> PlanBinding:
        return cls(
            plan.run_id,
            plan.plan_hash,
            plan.route,
            plan.retrieval_mode,
            plan.proposed_filters,
            plan.requested_canonical_fields,
            semantic_digest(plan.semantic_query),
            plan.versions,
            trace_id,
            expires_at,
        )


def validate_execution(
    binding: PlanBinding,
    approved: ApprovedQueryPlan,
    current_versions: Versions,
) -> None:
    if approved.run_id != binding.run_id:
        raise ContractViolation("RUN_MISMATCH")
    if approved.versions != binding.versions or approved.versions != current_versions:
        raise ContractViolation("VERSION_MISMATCH")
    if approved.approved_plan_hash != binding.plan_hash:
        raise ContractViolation("PLAN_HASH_MISMATCH")
    if approved.approved_filters != binding.filters:
        raise ContractViolation("FILTER_MISMATCH")
    if (
        approved.approved_route != binding.route
        or approved.approved_retrieval_mode != binding.mode
        or approved.approved_canonical_fields != binding.fields
        or semantic_digest(approved.semantic_query) != binding.semantic_hash
    ):
        raise ContractViolation("INVALID_PLAN")


@dataclass(frozen=True)
class QueryGrant:
    """Trusted verifier result, never populated from execute JSON.

    The verifier resolves Spring's opaque reference. Spring remains responsible
    for authorization, grant consumption, and lookup idempotency.
    """

    grant_id: str
    run_id: str
    plan_hash: str
    filter_hash: str
    versions: Versions
    issued_at: datetime
    expires_at: datetime


def valid_grant(grant: QueryGrant | None, approved: ApprovedQueryPlan, now: datetime) -> bool:
    return bool(
        grant is not None
        and grant.issued_at.tzinfo is not None
        and grant.expires_at.tzinfo is not None
        and grant.grant_id == approved.query_grant_id
        and grant.run_id == approved.run_id
        and grant.plan_hash == approved.approved_plan_hash
        and grant.filter_hash == approved.approved_filters.filter_hash
        and grant.versions == approved.versions
        and grant.issued_at <= now < grant.expires_at
        and grant.expires_at - grant.issued_at <= timedelta(seconds=30)
    )
