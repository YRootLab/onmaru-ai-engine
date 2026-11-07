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
from .vocabulary import (
    ClaimKind,
    ClarificationQuestionCode,
    ConceptCode,
    FailureStage,
    PlanReasonCode,
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
    "ClaimKind",
    "ClarificationQuestionCode",
    "ConceptCode",
    "FailureStage",
    "PlanReasonCode",
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
