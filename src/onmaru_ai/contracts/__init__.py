"""Versioned AI↔Spring contracts. No public endpoint or SSE implementation."""

from pydantic import BaseModel

from .models import (
    ApprovedQueryPlan,
    CandidateSet,
    EvidenceSet,
    PlanProposal,
    ProgressEvent,
    SafeQueryRequest,
    SourceRevision,
    ValidatedProposal,
    Versions,
)
from .validation import (
    ContractViolation,
    compute_plan_hash,
    validate_approval,
    validate_artifact,
    validate_plan,
)

CONTRACT_MODELS: dict[str, type[BaseModel]] = {
    model.__name__: model
    for model in (
        SafeQueryRequest,
        PlanProposal,
        ApprovedQueryPlan,
        CandidateSet,
        EvidenceSet,
        ValidatedProposal,
        ProgressEvent,
    )
}

__all__ = [
    "CONTRACT_MODELS",
    "ApprovedQueryPlan",
    "CandidateSet",
    "ContractViolation",
    "EvidenceSet",
    "PlanProposal",
    "ProgressEvent",
    "SafeQueryRequest",
    "SourceRevision",
    "ValidatedProposal",
    "Versions",
    "compute_plan_hash",
    "validate_approval",
    "validate_artifact",
    "validate_plan",
]
