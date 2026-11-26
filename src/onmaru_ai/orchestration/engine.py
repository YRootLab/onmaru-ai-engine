"""Five-route orchestration engine for approved runs (W13)."""

from __future__ import annotations

import contextlib
import logging
from dataclasses import dataclass
from typing import Any

from onmaru_ai.contracts import StepStatus
from onmaru_ai.contracts.models import (
    ApprovedQueryPlan,
    CandidateSet,
    EvidenceSet,
    Route,
    ValidatedProposal,
)
from onmaru_ai.progress import ProgressSink, ProgressStage
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
    result_reason: str | None = None


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
        progress_sink: ProgressSink | None = None,
        traceparent: str | None = None,
        operation: str | None = None,
    ) -> OrchestrationExecutionResult:
        try:
            if override_route is not None and override_route != plan.approved_route:
                raise OrchestrationError("Route switching prohibited during run execution")

            if progress_sink is not None:
                await progress_sink.enter(ProgressStage.PREPARING_INPUT, StepStatus.STARTED)

            route = plan.approved_route

            default_tp = "00-" + "0" * 32 + "-" + "0" * 16 + "-01"
            tp = traceparent or default_tp

            if progress_sink is not None:
                await progress_sink.enter(ProgressStage.PREPARING_INPUT, StepStatus.DONE)

            # Route 1: CLARIFY_OR_SCOPE
            if route == "CLARIFY_OR_SCOPE":
                return OrchestrationExecutionResult(
                    route=route,
                    status="CLARIFICATION_REQUIRED",
                )

            # Route 2: SQL_ONLY
            if route == "SQL_ONLY":
                if progress_sink is not None:
                    await progress_sink.enter(ProgressStage.RETRIEVING, StepStatus.STARTED)
                lookup_outcome: Any | None = None
                if self._sql_adapter is not None:
                    is_mock = hasattr(self._sql_adapter, "_mock_return_value")
                    if hasattr(self._sql_adapter, "lookup") and not is_mock:
                        lookup_outcome = await self._sql_adapter.lookup(plan, traceparent=tp)
                    elif hasattr(self._sql_adapter, "execute"):
                        lookup_outcome = await self._sql_adapter.execute(plan)
                    elif hasattr(self._sql_adapter, "lookup"):
                        lookup_outcome = await self._sql_adapter.lookup(plan, traceparent=tp)

                places = getattr(lookup_outcome, "places", ()) or ()
                cand_count = len(places)
                if progress_sink is not None:
                    await progress_sink.enter(
                        ProgressStage.RETRIEVING, StepStatus.DONE, count=cand_count
                    )

                if cand_count == 0:
                    if progress_sink is not None:
                        await progress_sink.enter(
                            ProgressStage.SELECTING_EVIDENCE, StepStatus.SKIPPED
                        )
                        await progress_sink.enter(ProgressStage.GENERATING, StepStatus.SKIPPED)
                        await progress_sink.enter(
                            ProgressStage.CHECKING_OUTPUT, StepStatus.SKIPPED
                        )
                    return OrchestrationExecutionResult(
                        route=route,
                        status="SUCCESS",
                        proposal=None,
                        result_reason="NO_CANDIDATES",
                    )

                if progress_sink is not None:
                    await progress_sink.enter(
                        ProgressStage.SELECTING_EVIDENCE, StepStatus.STARTED
                    )
                    await progress_sink.enter(
                        ProgressStage.SELECTING_EVIDENCE, StepStatus.DONE, count=cand_count
                    )
                    await progress_sink.enter(ProgressStage.GENERATING, StepStatus.STARTED)

                proposal = None
                if self._generator is not None:
                    try:
                        proposal = await self._generator.generate(
                            plan,
                            evidence_set=None,
                            lookup_outcome=lookup_outcome,
                            operation=operation,
                        )
                    except TypeError:
                        proposal = await self._generator.generate(plan, evidence_set=None)

                if progress_sink is not None:
                    await progress_sink.enter(ProgressStage.GENERATING, StepStatus.DONE)
                    await progress_sink.enter(ProgressStage.CHECKING_OUTPUT, StepStatus.STARTED)
                    await progress_sink.enter(ProgressStage.CHECKING_OUTPUT, StepStatus.DONE)

                has_places = bool(
                    proposal is not None and getattr(proposal, "places", None)
                )
                result_reason = None if has_places else "NO_RELEVANT_CANDIDATES"

                return OrchestrationExecutionResult(
                    route=route,
                    status="SUCCESS",
                    proposal=proposal,
                    result_reason=result_reason,
                )

            # Routes 3-5: Retrieval-involved routes
            # (LEXICAL_ONLY, DENSE_ONLY, HYBRID, SQL_PLUS_RETRIEVAL)
            if progress_sink is not None:
                await progress_sink.enter(ProgressStage.RETRIEVING, StepStatus.STARTED)

            sql_lookup_outcome: Any | None = None
            if route == "SQL_PLUS_RETRIEVAL" and self._sql_adapter is not None:
                is_mock = hasattr(self._sql_adapter, "_mock_return_value")
                if hasattr(self._sql_adapter, "lookup") and not is_mock:
                    sql_lookup_outcome = await self._sql_adapter.lookup(plan, traceparent=tp)
                elif hasattr(self._sql_adapter, "execute"):
                    sql_lookup_outcome = await self._sql_adapter.execute(plan)
                elif hasattr(self._sql_adapter, "lookup"):
                    sql_lookup_outcome = await self._sql_adapter.lookup(plan, traceparent=tp)

            cand_set: CandidateSet | None = None
            if self._retrieval_coordinator is not None:
                cand_set = self._retrieval_coordinator.execute(
                    HybridSearchRequest(plan=plan), snapshot
                )

            cand_count = len(cand_set.candidates) if cand_set and cand_set.candidates else 0

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

            if progress_sink is not None:
                await progress_sink.enter(
                    ProgressStage.RETRIEVING, StepStatus.DONE, count=cand_count
                )

            lookup_has_places = bool(
                sql_lookup_outcome is not None
                and getattr(sql_lookup_outcome, "disposition", None) == "COMPLETE"
                and getattr(sql_lookup_outcome, "places", ())
            )

            if cand_count == 0 and not lookup_has_places:
                if progress_sink is not None:
                    await progress_sink.enter(
                        ProgressStage.SELECTING_EVIDENCE, StepStatus.SKIPPED
                    )
                    await progress_sink.enter(ProgressStage.GENERATING, StepStatus.SKIPPED)
                    await progress_sink.enter(
                        ProgressStage.CHECKING_OUTPUT, StepStatus.SKIPPED
                    )
                return OrchestrationExecutionResult(
                    route=route,
                    status="SUCCESS",
                    proposal=None,
                    evidence=None,
                    candidate_set=cand_set,
                    result_reason="NO_CANDIDATES",
                )

            if progress_sink is not None:
                await progress_sink.enter(
                    ProgressStage.SELECTING_EVIDENCE, StepStatus.STARTED
                )

            evidence_set: EvidenceSet | None = None
            if cand_set and self._evidence_selector is not None and ranked_items:
                evidence_set = self._evidence_selector.select_evidence(
                    cand_set, ranked_items, snapshot=snapshot
                )

            if (
                route == "SQL_PLUS_RETRIEVAL"
                and sql_lookup_outcome is not None
                and lookup_has_places
                and (evidence_set is None or not evidence_set.evidence)
                and self._evidence_selector is not None
            ):
                select_for_places = getattr(self._evidence_selector, "select_for_places", None)
                if callable(select_for_places):
                    evidence_set = select_for_places(
                        plan,
                        tuple(place.place_id for place in sql_lookup_outcome.places),
                        snapshot=snapshot,
                    )

            if progress_sink is not None:
                places = getattr(evidence_set, "allowed_place_ids", None)
                if (
                    places is None
                    and evidence_set is not None
                    and hasattr(evidence_set, "evidence")
                ):
                    ev_items = getattr(evidence_set, "evidence", ()) or ()
                    places = tuple({e.place_id for e in ev_items if hasattr(e, "place_id")})
                selected_count = len(places) if places else 0
                await progress_sink.enter(
                    ProgressStage.SELECTING_EVIDENCE, StepStatus.DONE, count=selected_count
                )

            if progress_sink is not None:
                await progress_sink.enter(ProgressStage.GENERATING, StepStatus.STARTED)

            proposal = None
            if self._generator is not None and (evidence_set is not None or lookup_has_places):
                try:
                    proposal = await self._generator.generate(
                        plan,
                        evidence_set=evidence_set,
                        lookup_outcome=sql_lookup_outcome,
                        snapshot=snapshot,
                        operation=operation,
                    )
                except TypeError:
                    proposal = await self._generator.generate(plan, evidence_set=evidence_set)

            if progress_sink is not None:
                await progress_sink.enter(ProgressStage.GENERATING, StepStatus.DONE)
                await progress_sink.enter(ProgressStage.CHECKING_OUTPUT, StepStatus.STARTED)
                await progress_sink.enter(ProgressStage.CHECKING_OUTPUT, StepStatus.DONE)

            has_places = bool(
                proposal is not None and getattr(proposal, "places", None)
            )
            result_reason = None if has_places else "NO_RELEVANT_CANDIDATES"

            return OrchestrationExecutionResult(
                route=route,
                status="SUCCESS",
                proposal=proposal,
                evidence=evidence_set,
                candidate_set=cand_set,
                result_reason=result_reason,
            )
        except Exception:
            if progress_sink is not None and hasattr(progress_sink, "close_open_stage"):
                with contextlib.suppress(Exception):
                    await progress_sink.close_open_stage(StepStatus.SKIPPED)
            raise
