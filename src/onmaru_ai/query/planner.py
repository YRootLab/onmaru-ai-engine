"""Pure plan proposal builder. Retrieval and all model calls belong to approved execution."""
from __future__ import annotations

from onmaru_ai.contracts import (
    ContractViolation,
    PlanProposal,
    SafeQueryRequest,
    compute_plan_hash,
    validate_plan,
)
from onmaru_ai.contracts.models import RetrievalMode, Route
from onmaru_ai.contracts.vocabulary import CLARIFICATION_QUESTIONS, PlanReasonCode

from .dictionary import DICTIONARY_VERSION, EXACT_CONCEPTS, CatalogEntry
from .interpretation import Interpretation, InterpretationError, interpret


def retrieval_mode(frame: Interpretation) -> RetrievalMode:
    if frame.has_negation or frame.operation in ("COMPARE", "REFINE"):
        return "HYBRID"
    if not frame.negative and len(frame.targets) + len(frame.positive) == 1:
        if frame.targets or set(frame.positive) <= EXACT_CONCEPTS:
            return "LEXICAL_ONLY"
        return "DENSE_ONLY"
    return "HYBRID"


class QueryPlanner:
    """Uses a reviewed local catalog. Has no network, provider, or executor capability."""

    def __init__(self, *, catalog: tuple[CatalogEntry, ...] = ()) -> None:
        self._catalog = catalog

    def plan(self, request: SafeQueryRequest) -> PlanProposal:
        if request.versions.question_dictionary_version != DICTIONARY_VERSION:
            raise ContractViolation("VERSION_MISMATCH")
        try:
            frame = interpret(request, self._catalog)
        except InterpretationError as error:
            return self._clarify(request, error)
        mode = retrieval_mode(frame) if frame.has_body else "NONE"
        route: Route
        reason: PlanReasonCode
        if mode == "NONE":
            route, reason = "SQL_ONLY", PlanReasonCode.CANONICAL_FACT_ONLY
        elif frame.fields:
            route, reason = "SQL_PLUS_RETRIEVAL", PlanReasonCode.CANONICAL_FACT_WITH_RETRIEVAL
        else:
            route = mode
            reason = {"LEXICAL_ONLY": PlanReasonCode.EXACT_PUBLIC_TERM,
                      "DENSE_ONLY": PlanReasonCode.SINGLE_SEMANTIC_TOPIC,
                      "HYBRID": PlanReasonCode.COMPOSITE_QUERY}[mode]
        return self._build(request, {
            "route": route, "retrievalMode": mode, "reasonCodes": [reason],
            "questionFrame": {"operation": frame.operation, "targetPlaceIds": frame.targets,
                              "subjectConceptCodes": frame.positive},
            "retrievalExpression": {"positiveConceptCodes": frame.positive,
                                    "negativeConceptCodes": frame.negative,
                                    "publicEntityIds": frame.targets},
            "requestedCanonicalFields": frame.fields, "proposedFilters": frame.filters,
            "semanticQuery": frame.text if mode != "NONE" else None, "clarification": None,
        })

    def _clarify(self, request: SafeQueryRequest, error: InterpretationError) -> PlanProposal:
        return self._build(request, {
            "route": "CLARIFY_OR_SCOPE", "retrievalMode": "NONE", "reasonCodes": [error.reason],
            "questionFrame": {"operation": "EXPLAIN", "targetPlaceIds": [],
                              "subjectConceptCodes": []},
            "retrievalExpression": {"positiveConceptCodes": [], "negativeConceptCodes": [],
                                    "publicEntityIds": []},
            "requestedCanonicalFields": [], "proposedFilters": request.authority_bounds.filters,
            "semanticQuery": None,
            "clarification": {"reason": error.reason,
                              "questionCode": CLARIFICATION_QUESTIONS[error.reason]},
        })

    @staticmethod
    def _build(request: SafeQueryRequest, body: dict[str, object]) -> PlanProposal:
        draft = PlanProposal.model_validate({
            **body, "schemaVersion": "ai-plan-proposal.v1", "planVersion": "ai-query-plan.v1",
            "runId": request.run_id, "versions": request.versions, "limits": request.limits,
            "planHash": "sha256:" + "0" * 64,
        })
        plan = draft.model_copy(update={"plan_hash": compute_plan_hash(draft)})
        validate_plan(request, plan)
        return plan
