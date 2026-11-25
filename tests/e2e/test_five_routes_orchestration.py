"""Comprehensive end-to-end integration tests for all five routes (Issue #76)."""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from onmaru_ai.contracts import SafeQueryRequest
from onmaru_ai.contracts.models import (
    ApprovedQueryPlan,
    EvidenceSet,
    ValidatedProposal,
)
from onmaru_ai.orchestration.engine import (
    OrchestrationEngine,
)
from onmaru_ai.query.dictionary import CatalogEntry
from onmaru_ai.query.planner import QueryPlanner
from onmaru_ai.retrieval.rerank import (
    DeterministicSemanticCrossScorer,
    Reranker,
    RerankerConfig,
)
from onmaru_ai.storage.postgres import CorpusSnapshot


def _build_test_catalog() -> tuple[CatalogEntry, ...]:
    return (
        CatalogEntry(code="SEOUL", kind="REGION", display_label="서울", synonyms=("서울시",)),
        CatalogEntry(code="JEONJU", kind="REGION", display_label="전주", synonyms=("전주시",)),
        CatalogEntry(code="p1", kind="PLACE", display_label="경복궁", region_code="SEOUL"),
        CatalogEntry(code="p2", kind="PLACE", display_label="창덕궁", region_code="SEOUL"),
        CatalogEntry(code="p3", kind="PLACE", display_label="전주한옥마을", region_code="JEONJU"),
    )


def _build_safe_query_request(
    query: str, run_id: str = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
) -> SafeQueryRequest:
    return SafeQueryRequest.model_validate(
        {
            "schemaVersion": "ai-safe-query.v1",
            "runId": run_id,
            "safeQuery": query,
            "confirmedContext": {
                "regionCode": None,
                "pinnedPlaceIds": [],
                "excludedPlaceIds": [],
                "lastConfirmedPlaceIds": [],
            },
            "authorityBounds": {
                "filters": {
                    "filterHash": "sha256:" + "a" * 64,
                    "publicOnly": True,
                    "placeIds": None,
                    "regionCodes": None,
                    "categoryCodes": None,
                    "pinnedPlaceIds": [],
                    "excludedPlaceIds": [],
                },
                "allowedCanonicalFields": [
                    "PUBLIC_ADDRESS",
                    "REGION_CODE",
                    "CATEGORY_CODE",
                    "PUBLIC_STATUS",
                ],
            },
            "versions": {
                "corpusRevision": "corpus-1",
                "configHash": "sha256:" + "a" * 64,
                "questionDictionaryVersion": "questions-1",
                "sourceRevocationSequence": 7,
            },
            "limits": {
                "bm25K": 20,
                "vectorK": 20,
                "rerankK": 30,
                "evidenceK": 12,
                "maxPlaces": 5,
            },
        }
    )


def _build_approved_plan_from_proposal(
    proposal: Any, run_id: str = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
) -> ApprovedQueryPlan:
    # Architectural security gate: SQL routes require grant; other routes forbid grant
    grant_id = "grant-e2e-1" if proposal.route in ("SQL_ONLY", "SQL_PLUS_RETRIEVAL") else None
    return ApprovedQueryPlan.model_validate(
        {
            "schemaVersion": "ai-approved-plan.v1",
            "planVersion": proposal.plan_version,
            "runId": run_id,
            "approvedPlanHash": proposal.plan_hash,
            "approvedRoute": proposal.route,
            "approvedRetrievalMode": proposal.retrieval_mode,
            "approvedFilters": proposal.proposed_filters,
            "approvedCanonicalFields": proposal.requested_canonical_fields,
            "semanticQuery": proposal.semantic_query,
            "versions": {
                "corpusRevision": "corpus-1",
                "configHash": "sha256:" + "a" * 64,
                "questionDictionaryVersion": "questions-1",
                "sourceRevocationSequence": 7,
            },
            "queryGrantId": grant_id,
        }
    )


class FakeSqlAdapter:
    def __init__(self) -> None:
        self.lookup_called = 0

    async def lookup(self, plan: Any, traceparent: str | None = None) -> Any:
        self.lookup_called += 1
        mock_outcome = MagicMock()
        mock_outcome.disposition = "COMPLETE"
        mock_outcome.places = (MagicMock(place_id="p1", canonical_name="경복궁"),)
        return mock_outcome


class E2EFixtureHarness:
    def __init__(self) -> None:
        self.catalog = _build_test_catalog()
        self.planner = QueryPlanner(catalog=self.catalog)

        # SQL adapter for Spring PlaceQueryPort
        self.sql_adapter = FakeSqlAdapter()

        # Mock Retrieval Coordinator
        self.retrieval_coord = MagicMock()
        cand1 = MagicMock(
            source_id="s-1",
            source_revision="r-1",
            chunk_id="c1",
            place_id="p1",
            rank=1,
            score=0.95,
        )
        cand2 = MagicMock(
            source_id="s-2",
            source_revision="r-1",
            chunk_id="c2",
            place_id="p2",
            rank=2,
            score=0.88,
        )
        cand_set = MagicMock()
        cand_set.candidates = [cand1, cand2]
        self.retrieval_coord.execute.return_value = cand_set

        # Reranker
        self.reranker = Reranker(
            scorer=DeterministicSemanticCrossScorer(),
            config=RerankerConfig(timeout_seconds=0.5),
        )

        # Evidence selector
        self.evidence_selector = MagicMock()
        ev1 = MagicMock(
            source_id="s-1",
            source_revision="r-1",
            chunk_id="c1",
            place_id="p1",
            start_offset=0,
            end_offset=50,
        )
        evidence_set = MagicMock(spec=EvidenceSet)
        evidence_set.evidence = [ev1]
        evidence_set.allowed_place_ids = ["p1"]
        self.evidence_selector.select_evidence.return_value = evidence_set

        # Generator
        self.generator = AsyncMock()
        mock_proposal = MagicMock(spec=ValidatedProposal)
        mock_proposal.run_id = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
        mock_proposal.retrieval_status = "COMPLETE"
        mock_proposal.generation_status = "SUCCESS"
        mock_proposal.places = [MagicMock(place_id="p1")]
        mock_proposal.summary_claims = []
        mock_proposal.degraded_reason = None
        self.generator.generate.return_value = mock_proposal

        self.engine = OrchestrationEngine(
            sql_adapter=self.sql_adapter,
            retrieval_coordinator=self.retrieval_coord,
            reranker=self.reranker,
            evidence_selector=self.evidence_selector,
            generator=self.generator,
        )


@pytest.mark.anyio
async def test_e2e_route_1_sql_only() -> None:
    """SQL_ONLY: canonical fact only; skips vector/bm25 retrieval and reranker."""
    h = E2EFixtureHarness()
    req = _build_safe_query_request("경복궁 주소")
    proposal = h.planner.plan(req)

    assert proposal.route == "SQL_ONLY"
    assert proposal.retrieval_mode == "NONE"

    approved_plan = _build_approved_plan_from_proposal(proposal)
    res = await h.engine.execute_run(approved_plan, snapshot=MagicMock(spec=CorpusSnapshot))

    assert res.route == "SQL_ONLY"
    assert res.status == "SUCCESS"
    assert res.proposal is not None
    # Retrieval and reranker must NEVER be called in SQL_ONLY
    h.retrieval_coord.execute.assert_not_called()
    assert h.sql_adapter.lookup_called == 1


@pytest.mark.anyio
async def test_e2e_route_2_lexical_only() -> None:
    """LEXICAL_ONLY: single target place without negation/comparison."""
    h = E2EFixtureHarness()
    req = _build_safe_query_request("경복궁")
    proposal = h.planner.plan(req)

    assert proposal.route == "LEXICAL_ONLY"
    assert proposal.retrieval_mode == "LEXICAL_ONLY"

    approved_plan = _build_approved_plan_from_proposal(proposal)
    res = await h.engine.execute_run(approved_plan, snapshot=MagicMock(spec=CorpusSnapshot))

    assert res.route == "LEXICAL_ONLY"
    assert res.status == "SUCCESS"
    assert res.evidence is not None
    h.retrieval_coord.execute.assert_called_once()
    assert h.sql_adapter.lookup_called == 0


@pytest.mark.anyio
async def test_e2e_route_3_dense_only() -> None:
    """DENSE_ONLY: single non-exact semantic concept without target place."""
    h = E2EFixtureHarness()
    req = _build_safe_query_request("조용한 곳 추천")
    proposal = h.planner.plan(req)

    assert proposal.route == "DENSE_ONLY"
    assert proposal.retrieval_mode == "DENSE_ONLY"

    approved_plan = _build_approved_plan_from_proposal(proposal)
    res = await h.engine.execute_run(approved_plan, snapshot=MagicMock(spec=CorpusSnapshot))

    assert res.route == "DENSE_ONLY"
    assert res.status == "SUCCESS"
    assert res.evidence is not None
    h.retrieval_coord.execute.assert_called_once()
    assert h.sql_adapter.lookup_called == 0


@pytest.mark.anyio
async def test_e2e_route_4_hybrid() -> None:
    """HYBRID: composite query with negation or multiple concepts; runs BM25+Vector+RRF+Reranker."""
    h = E2EFixtureHarness()
    req = _build_safe_query_request("경복궁 말고 창덕궁")
    proposal = h.planner.plan(req)

    assert proposal.route == "HYBRID"
    assert proposal.retrieval_mode == "HYBRID"

    approved_plan = _build_approved_plan_from_proposal(proposal)
    res = await h.engine.execute_run(approved_plan, snapshot=MagicMock(spec=CorpusSnapshot))

    assert res.route == "HYBRID"
    assert res.status == "SUCCESS"
    assert res.candidate_set is not None
    assert res.evidence is not None
    h.retrieval_coord.execute.assert_called_once()
    h.generator.generate.assert_awaited_once()
    assert h.sql_adapter.lookup_called == 0


@pytest.mark.anyio
async def test_e2e_route_5_sql_plus_retrieval() -> None:
    """SQL_PLUS_RETRIEVAL: combines canonical SQL fields and text retrieval."""
    h = E2EFixtureHarness()
    req = _build_safe_query_request("경복궁 주소와 역사")
    proposal = h.planner.plan(req)

    assert proposal.route == "SQL_PLUS_RETRIEVAL"

    approved_plan = _build_approved_plan_from_proposal(proposal)
    res = await h.engine.execute_run(approved_plan, snapshot=MagicMock(spec=CorpusSnapshot))

    assert res.route == "SQL_PLUS_RETRIEVAL"
    assert res.status == "SUCCESS"
    # Both SQL lookup and retrieval must execute
    assert h.sql_adapter.lookup_called == 1
    h.retrieval_coord.execute.assert_called_once()
    assert res.proposal is not None
