"""Tests for W13 five-route orchestration and in-run fallback."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import pytest

from onmaru_ai.contracts.models import ApprovedQueryPlan, EvidenceSet, ValidatedProposal
from onmaru_ai.orchestration.engine import (
    OrchestrationEngine,
    OrchestrationError,
)


def _load_approved_plan(mode: str) -> ApprovedQueryPlan:
    fixture_path = (
        Path(__file__).parent.parent
        / "contracts"
        / "fixtures"
        / (
            "accepted-approved-sql_only.json"
            if mode == "SQL_ONLY"
            else "accepted-approved-hybrid.json"
        )
    )
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    payload = dict(data["payload"])
    payload["approvedRoute"] = mode
    payload["approvedRetrievalMode"] = (
        mode if mode in ("LEXICAL_ONLY", "DENSE_ONLY", "HYBRID") else "LEXICAL_ONLY"
    )
    return ApprovedQueryPlan.model_validate(payload)


@pytest.mark.anyio
async def test_sql_only_route_does_not_call_retrieval_or_reranker() -> None:
    plan = _load_approved_plan("SQL_ONLY")

    sql_adapter = AsyncMock()
    sql_adapter.execute.return_value = [{"place_id": "p1", "name": "한옥"}]

    retrieval_coord = MagicMock()
    reranker = MagicMock()
    generator = AsyncMock()
    generator.generate.return_value = MagicMock(spec=ValidatedProposal)

    engine = OrchestrationEngine(
        sql_adapter=sql_adapter,
        retrieval_coordinator=retrieval_coord,
        reranker=reranker,
        generator=generator,
    )

    result = await engine.execute_run(plan, snapshot=MagicMock())
    assert result.route == "SQL_ONLY"
    sql_adapter.execute.assert_awaited_once()
    retrieval_coord.execute.assert_not_called()
    reranker.rerank.assert_not_called()


@pytest.mark.anyio
async def test_hybrid_route_executes_pipeline_and_reranker() -> None:
    plan = _load_approved_plan("HYBRID")

    retrieval_coord = MagicMock()
    cand_set = MagicMock()
    cand_set.candidates = [
        MagicMock(
            chunk_id="c1", place_id="p1", source_id="s1", source_revision="r1", rank=1, score=0.8
        )
    ]
    retrieval_coord.execute.return_value = cand_set

    reranker = MagicMock()
    reranker.rerank.return_value = [
        {
            "chunk_id": "c1",
            "place_id": "p1",
            "source_id": "s1",
            "source_revision": "r1",
            "rank": 1,
            "score": 0.9,
        }
    ]

    evidence_selector = MagicMock()
    evidence_selector.select_evidence.return_value = MagicMock(spec=EvidenceSet)

    generator = AsyncMock()
    generator.generate.return_value = MagicMock(spec=ValidatedProposal)

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        reranker=reranker,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    result = await engine.execute_run(plan, snapshot=MagicMock())
    assert result.route == "HYBRID"
    retrieval_coord.execute.assert_called_once()
    reranker.rerank.assert_called_once()
    evidence_selector.select_evidence.assert_called_once()
    generator.generate.assert_awaited_once()


@pytest.mark.anyio
async def test_route_change_prohibited_in_execution() -> None:
    plan = _load_approved_plan("HYBRID")
    engine = OrchestrationEngine()
    # Route cannot be mutated or switched during run
    with pytest.raises(OrchestrationError, match="Route switching prohibited"):
        await engine.execute_run(plan, snapshot=MagicMock(), override_route="SQL_ONLY")


@pytest.mark.anyio
async def test_lexical_only_route_does_not_call_reranker() -> None:
    plan = _load_approved_plan("LEXICAL_ONLY")

    retrieval_coord = MagicMock()
    cand_set = MagicMock()
    cand_set.candidates = [
        MagicMock(
            chunk_id="c1", place_id="p1", source_id="s1", source_revision="r1", rank=1, score=0.8
        )
    ]
    retrieval_coord.execute.return_value = cand_set

    reranker = MagicMock()
    evidence_selector = MagicMock()
    evidence_selector.select_evidence.return_value = MagicMock(spec=EvidenceSet)

    generator = AsyncMock()
    generator.generate.return_value = MagicMock(spec=ValidatedProposal)

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        reranker=reranker,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    result = await engine.execute_run(plan, snapshot=MagicMock())
    assert result.route == "LEXICAL_ONLY"
    retrieval_coord.execute.assert_called_once()
    reranker.rerank.assert_not_called()
    evidence_selector.select_evidence.assert_called_once()
    generator.generate.assert_awaited_once()


@pytest.mark.anyio
async def test_clarify_or_scope_route_returns_clarification_status() -> None:
    # Build a minimal CLARIFY_OR_SCOPE plan
    plan = _load_approved_plan("HYBRID")
    # Using model_copy with update for CLARIFY_OR_SCOPE route
    clarify_plan = plan.model_copy(update={"approved_route": "CLARIFY_OR_SCOPE"})

    sql_adapter = AsyncMock()
    retrieval_coord = MagicMock()
    reranker = MagicMock()
    generator = AsyncMock()

    engine = OrchestrationEngine(
        sql_adapter=sql_adapter,
        retrieval_coordinator=retrieval_coord,
        reranker=reranker,
        generator=generator,
    )

    result = await engine.execute_run(clarify_plan, snapshot=MagicMock())
    assert result.route == "CLARIFY_OR_SCOPE"
    assert result.status == "CLARIFICATION_REQUIRED"
    assert result.proposal is None
    sql_adapter.execute.assert_not_called()
    retrieval_coord.execute.assert_not_called()
    reranker.rerank.assert_not_called()
    generator.generate.assert_not_called()

