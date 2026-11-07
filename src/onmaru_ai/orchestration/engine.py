"""Five-route orchestration engine for approved runs (W13)."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from onmaru_ai.contracts.models import (
    ApprovedQueryPlan,
    CandidateSet,
    EvidenceSet,
    Route,
    ValidatedProposal,
)
from onmaru_ai.retrieval.hybrid import HybridSearchRequest
from onmaru_ai.storage.postgres import CorpusSnapshot

logger = logging.getLogger(__name__)


class OrchestrationError(Exception):
    """Base error for orchestration execution failure."""


@dataclass(frozen=True, slots=True)
class OrchestrationExecutionResult:
    route: Route
    status: str
    proposal: ValidatedProposal | None = None
    evidence: EvidenceSet | None = None
    candidate_set: CandidateSet | None = None


class OrchestrationEngine:
    """
    Executes approved query plans across the five routes + clarification.
    Enforces:
    - Zero route switching within a run.
    - Zero unneeded module calls (e.g., no embedding/reranker in SQL_ONLY).
    - Graceful fallback within run scope.
    """

    def __init__(
        self,
        *,
        sql_adapter: Any | None = None,
        retrieval_coordinator: Any | None = None,
        reranker: Any | None = None,
        evidence_selector: Any | None = None,
        generator: Any | None = None,
    ) -> None:
        self._sql_adapter = sql_adapter
        self._retrieval_coordinator = retrieval_coordinator
        self._reranker = reranker
        self._evidence_selector = evidence_selector
        self._generator = generator

    async def execute_run(
        self,
        plan: ApprovedQueryPlan,
        snapshot: CorpusSnapshot,
        *,
        override_route: Route | None = None,
    ) -> OrchestrationExecutionResult:
        if override_route is not None and override_route != plan.approved_route:
            raise OrchestrationError("Route switching prohibited during run execution")

        route = plan.approved_route

        # Route 1: CLARIFY_OR_SCOPE
        if route == "CLARIFY_OR_SCOPE":
            return OrchestrationExecutionResult(
                route=route,
                status="CLARIFICATION_REQUIRED",
            )

        # Route 2: SQL_ONLY
        if route == "SQL_ONLY":
            if self._sql_adapter is not None:
                await self._sql_adapter.execute(plan)
            proposal = None
            if self._generator is not None:
                proposal = await self._generator.generate(plan, evidence_set=None)
            return OrchestrationExecutionResult(
                route=route,
                status="SUCCESS",
                proposal=proposal,
            )

        # Routes 3-5: Retrieval-involved routes
        # (LEXICAL_ONLY, DENSE_ONLY, HYBRID, SQL_PLUS_RETRIEVAL)
        if route == "SQL_PLUS_RETRIEVAL" and self._sql_adapter is not None:
            await self._sql_adapter.execute(plan)

        cand_set: CandidateSet | None = None
        if self._retrieval_coordinator is not None:
            cand_set = self._retrieval_coordinator.execute(HybridSearchRequest(plan=plan), snapshot)

        ranked_items: list[dict[str, Any]] = []
        if cand_set and cand_set.candidates:
            cands_dict = [
                {
                    "chunk_id": str(c.chunk_id),
                    "place_id": str(c.place_id),
                    "source_id": str(c.source_id),
                    "source_revision": str(c.source_revision),
                    "rank": c.rank,
                    "score": c.score,
                }
                for c in cand_set.candidates
            ]
            if self._reranker is not None and route in ("HYBRID", "SQL_PLUS_RETRIEVAL"):
                ranked_items = self._reranker.rerank(plan.semantic_query or "", cands_dict)
            else:
                ranked_items = cands_dict

        evidence_set: EvidenceSet | None = None
        if cand_set and self._evidence_selector is not None and ranked_items:
            evidence_set = self._evidence_selector.select_evidence(cand_set, ranked_items)

        proposal = None
        if self._generator is not None and evidence_set is not None:
            proposal = await self._generator.generate(plan, evidence_set=evidence_set)

        return OrchestrationExecutionResult(
            route=route,
            status="SUCCESS",
            proposal=proposal,
            evidence=evidence_set,
            candidate_set=cand_set,
        )
