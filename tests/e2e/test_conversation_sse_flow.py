"""End-to-end test for member conversation, multi-turn state, and SSE streaming flow (Issue #76)."""

from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest

from onmaru_ai.contracts import SafeQueryRequest
from onmaru_ai.contracts.models import (
    ApprovedQueryPlan,
    EvidenceSet,
    StepKey,
    StepStatus,
    ValidatedProposal,
)
from onmaru_ai.orchestration.engine import OrchestrationEngine
from onmaru_ai.progress import InMemoryProgressSink, ProgressStage
from onmaru_ai.query.dictionary import CatalogEntry
from onmaru_ai.query.planner import QueryPlanner
from onmaru_ai.storage.postgres import CorpusSnapshot


def _format_sse_event(event_type: str, data: dict[str, Any]) -> str:
    """Format an SSE frame conforming to the Spring/AI RAG SSE contract."""
    return f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@pytest.mark.anyio
async def test_member_multiturn_conversation_and_progress_events() -> None:
    catalog = (
        CatalogEntry(code="SEOUL", kind="REGION", display_label="서울"),
        CatalogEntry(code="p1", kind="PLACE", display_label="경복궁", region_code="SEOUL"),
        CatalogEntry(code="p2", kind="PLACE", display_label="창덕궁", region_code="SEOUL"),
    )
    planner = QueryPlanner(catalog=catalog)

    # Turn 1: Initial query "경복궁"
    req_turn1 = SafeQueryRequest.model_validate(
        {
            "schemaVersion": "ai-safe-query.v1",
            "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc497",
            "safeQuery": "경복궁",
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
                "allowedCanonicalFields": ["PUBLIC_ADDRESS"],
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
    proposal_turn1 = planner.plan(req_turn1)
    assert proposal_turn1.route == "LEXICAL_ONLY"

    # Turn 1 Execution with progress sink
    sink = InMemoryProgressSink(
        run_id="45e6a7f5-31bc-469d-9e30-6f510a1dc497",
        plan_hash=proposal_turn1.plan_hash,
    )

    retrieval_coord = MagicMock()
    cand = MagicMock(
        source_id="s-1", source_revision="r-1", chunk_id="c1", place_id="p1", rank=1, score=0.9
    )
    cand_set = MagicMock()
    cand_set.candidates = [cand]
    retrieval_coord.execute.return_value = cand_set

    evidence_selector = MagicMock()
    ev = MagicMock(
        source_id="s-1",
        source_revision="r-1",
        chunk_id="c1",
        place_id="p1",
        start_offset=0,
        end_offset=50,
    )
    ev_set = MagicMock(spec=EvidenceSet)
    ev_set.evidence = [ev]
    ev_set.allowed_place_ids = ["p1"]
    evidence_selector.select_evidence.return_value = ev_set

    generator = AsyncMock()
    mock_proposal = MagicMock(spec=ValidatedProposal)
    mock_proposal.run_id = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
    mock_proposal.places = [MagicMock(place_id="p1")]
    mock_proposal.degraded_reason = None
    generator.generate.return_value = mock_proposal

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    approved_plan_t1 = ApprovedQueryPlan.model_validate(
        {
            "schemaVersion": "ai-approved-plan.v1",
            "planVersion": proposal_turn1.plan_version,
            "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc497",
            "approvedPlanHash": proposal_turn1.plan_hash,
            "approvedRoute": proposal_turn1.route,
            "approvedRetrievalMode": proposal_turn1.retrieval_mode,
            "approvedFilters": proposal_turn1.proposed_filters,
            "approvedCanonicalFields": proposal_turn1.requested_canonical_fields,
            "semanticQuery": proposal_turn1.semantic_query,
            "versions": {
                "corpusRevision": "corpus-1",
                "configHash": "sha256:" + "a" * 64,
                "questionDictionaryVersion": "questions-1",
                "sourceRevocationSequence": 7,
            },
            "queryGrantId": None,
        }
    )

    res_t1 = await engine.execute_run(
        approved_plan_t1,
        snapshot=MagicMock(spec=CorpusSnapshot),
        progress_sink=sink,
    )

    assert res_t1.status == "SUCCESS"
    # Verify exact progression of stages and step keys
    assert [(event.stage, event.step_key, event.status) for event in sink.events] == [
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.STARTED),
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.DONE),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.STARTED),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.DONE),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.STARTED),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.DONE),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.STARTED),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.DONE),
        (ProgressStage.CHECKING_OUTPUT, StepKey.CHECK, StepStatus.STARTED),
        (ProgressStage.CHECKING_OUTPUT, StepKey.CHECK, StepStatus.DONE),
    ]
    assert sink.events[3].count == 1
    assert sink.events[5].count == 1

    # SSE event simulation
    sse_frames = [
        _format_sse_event(
            "progress",
            {
                "stage": str(ev.stage),
                "stepKey": str(ev.step_key),
                "status": str(ev.status),
                "count": ev.count,
                "ordinal": ev.ordinal,
            },
        )
        for ev in sink.events
    ]
    # Add final snapshot SSE event
    sse_frames.append(_format_sse_event("snapshot", {"status": "COMPLETE", "places": ["p1"]}))

    assert len(sse_frames) == 11
    assert "event: progress\n" in sse_frames[0]
    assert "event: snapshot\n" in sse_frames[-1]

    # Turn 2: Follow-up comparison query
    req_turn2 = SafeQueryRequest.model_validate(
        {
            "schemaVersion": "ai-safe-query.v1",
            "runId": "45e6a7f5-31bc-469d-9e30-6f510a1dc498",
            "safeQuery": "경복궁 창덕궁 비교",
            "confirmedContext": {
                "regionCode": "SEOUL",
                "pinnedPlaceIds": [],
                "excludedPlaceIds": [],
                "lastConfirmedPlaceIds": ["p1"],
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
                "allowedCanonicalFields": ["PUBLIC_ADDRESS"],
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
    proposal_turn2 = planner.plan(req_turn2)
    # Comparison is planned as HYBRID route
    assert proposal_turn2.route == "HYBRID"
