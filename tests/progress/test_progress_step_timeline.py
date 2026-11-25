"""Unit tests for progress timeline step keys, statuses, and candidate counts."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from pydantic import ValidationError

from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    CandidateSet,
    EvidenceSet,
    ProgressEvent,
    StepKey,
    StepStatus,
    ValidatedProposal,
)
from onmaru_ai.orchestration.engine import OrchestrationEngine
from onmaru_ai.progress import (
    InMemoryProgressSink,
    ProgressStage,
)
from onmaru_ai.storage.postgres import CorpusSnapshot

RUN_ID = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
PLAN_HASH = "sha256:" + "a" * 64


def _create_approved_plan(route: str = "HYBRID") -> ApprovedQueryPlan:
    return ApprovedQueryPlan.model_validate(
        {
            "schemaVersion": "ai-approved-plan.v1",
            "planVersion": "ai-query-plan.v1",
            "runId": RUN_ID,
            "approvedPlanHash": PLAN_HASH,
            "approvedRoute": route,
            "approvedRetrievalMode": "HYBRID",
            "approvedFilters": {
                "filterHash": "sha256:" + "b" * 64,
                "publicOnly": True,
                "placeIds": None,
                "regionCodes": None,
                "categoryCodes": None,
                "pinnedPlaceIds": [],
                "excludedPlaceIds": [],
            },
            "approvedCanonicalFields": ["PUBLIC_ADDRESS"],
            "semanticQuery": "서울 한옥 맛집",
            "versions": {
                "corpusRevision": "corpus-1",
                "configHash": "sha256:" + "a" * 64,
                "questionDictionaryVersion": "questions-1",
                "sourceRevocationSequence": 7,
            },
            "queryGrantId": None,
        }
    )


@pytest.mark.anyio
async def test_normal_path_progress_timeline_order_and_counts() -> None:
    sink = InMemoryProgressSink(run_id=RUN_ID, plan_hash=PLAN_HASH)

    # 12 candidates found
    retrieval_coord = MagicMock()
    cands = [
        MagicMock(
            source_id="s-1",
            source_revision="r-1",
            chunk_id=f"c{i}",
            place_id=f"p{i}",
            rank=i,
            score=0.9 - i * 0.05,
        )
        for i in range(12)
    ]
    cand_set = MagicMock(spec=CandidateSet)
    cand_set.candidates = cands
    retrieval_coord.execute.return_value = cand_set

    # 3 places selected
    evidence_selector = MagicMock()
    ev_set = MagicMock(spec=EvidenceSet)
    ev_set.allowed_place_ids = ["p0", "p1", "p2"]
    ev_set.evidence = [MagicMock(place_id=pid) for pid in ev_set.allowed_place_ids]
    evidence_selector.select_evidence.return_value = ev_set

    generator = AsyncMock()
    mock_proposal = MagicMock(spec=ValidatedProposal)
    mock_proposal.run_id = RUN_ID
    mock_proposal.places = [MagicMock(place_id=pid) for pid in ev_set.allowed_place_ids]
    mock_proposal.degraded_reason = None
    generator.generate.return_value = mock_proposal

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    plan = _create_approved_plan(route="HYBRID")
    result = await engine.execute_run(
        plan,
        snapshot=MagicMock(spec=CorpusSnapshot),
        progress_sink=sink,
    )
    assert result.status == "SUCCESS"

    # Verify exact 10 events: UNDERSTAND -> SEARCH -> SELECT -> WRITE -> CHECK
    expected_timeline = [
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.STARTED, None, 1),
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.DONE, None, 2),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.STARTED, None, 3),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.DONE, 12, 4),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.STARTED, None, 5),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.DONE, 3, 6),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.STARTED, None, 7),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.DONE, None, 8),
        (ProgressStage.CHECKING_OUTPUT, StepKey.CHECK, StepStatus.STARTED, None, 9),
        (ProgressStage.CHECKING_OUTPUT, StepKey.CHECK, StepStatus.DONE, None, 10),
    ]

    actual_timeline = [
        (ev.stage, ev.step_key, ev.status, ev.count, ev.ordinal)
        for ev in sink.events
    ]
    assert actual_timeline == expected_timeline

    # Verify serialized JSON payload structure
    dumped = [ev.model_dump(by_alias=True) for ev in sink.events]
    assert dumped[3]["stepKey"] == "SEARCH"
    assert dumped[3]["status"] == "DONE"
    assert dumped[3]["count"] == 12

    assert dumped[5]["stepKey"] == "SELECT"
    assert dumped[5]["status"] == "DONE"
    assert dumped[5]["count"] == 3


@pytest.mark.anyio
async def test_empty_result_path_emits_search_done_zero_and_select_skipped() -> None:
    sink = InMemoryProgressSink(run_id=RUN_ID, plan_hash=PLAN_HASH)

    # 0 candidates found
    retrieval_coord = MagicMock()
    cand_set = MagicMock(spec=CandidateSet)
    cand_set.candidates = []
    retrieval_coord.execute.return_value = cand_set

    evidence_selector = MagicMock()
    generator = AsyncMock()

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    plan = _create_approved_plan(route="HYBRID")
    result = await engine.execute_run(
        plan,
        snapshot=MagicMock(spec=CorpusSnapshot),
        progress_sink=sink,
    )
    assert result.status == "SUCCESS"
    assert result.proposal is None

    actual_timeline = [
        (ev.stage, ev.step_key, ev.status, ev.count, ev.ordinal)
        for ev in sink.events
    ]

    # Verify SEARCH DONE has count=0 and SELECT has SKIPPED with count=None
    expected_timeline = [
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.STARTED, None, 1),
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.DONE, None, 2),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.STARTED, None, 3),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.DONE, 0, 4),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.SKIPPED, None, 5),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.SKIPPED, None, 6),
        (ProgressStage.CHECKING_OUTPUT, StepKey.CHECK, StepStatus.SKIPPED, None, 7),
    ]
    assert actual_timeline == expected_timeline

    # Selector and generator should never be invoked when search is empty
    evidence_selector.select_evidence.assert_not_called()
    generator.generate.assert_not_called()


@pytest.mark.anyio
async def test_failure_path_closes_open_step_as_skipped() -> None:
    sink = InMemoryProgressSink(run_id=RUN_ID, plan_hash=PLAN_HASH)

    # Retrieval raises runtime error while SEARCH stage is open
    retrieval_coord = MagicMock()
    retrieval_coord.execute.side_effect = RuntimeError("Elasticsearch cluster unavailable")

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
    )

    plan = _create_approved_plan(route="HYBRID")
    with pytest.raises(RuntimeError, match="Elasticsearch cluster unavailable"):
        await engine.execute_run(
            plan,
            snapshot=MagicMock(spec=CorpusSnapshot),
            progress_sink=sink,
        )

    # Verify that the open RETRIEVING stage was closed with status=SKIPPED
    actual_timeline = [
        (ev.stage, ev.step_key, ev.status, ev.count, ev.ordinal)
        for ev in sink.events
    ]
    assert actual_timeline == [
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.STARTED, None, 1),
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.DONE, None, 2),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.STARTED, None, 3),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.SKIPPED, None, 4),
    ]
    assert sink.open_stage is None


@pytest.mark.anyio
async def test_generation_failure_closes_write_step_as_skipped() -> None:
    sink = InMemoryProgressSink(run_id=RUN_ID, plan_hash=PLAN_HASH)

    retrieval_coord = MagicMock()
    cand = MagicMock(
        source_id="s-1",
        source_revision="r-1",
        chunk_id="c1",
        place_id="p1",
        rank=1,
        score=0.9,
    )
    cand_set = MagicMock(spec=CandidateSet)
    cand_set.candidates = [cand]
    retrieval_coord.execute.return_value = cand_set

    evidence_selector = MagicMock()
    ev_set = MagicMock(spec=EvidenceSet)
    ev_set.allowed_place_ids = ["p1"]
    ev_set.evidence = [MagicMock(place_id="p1")]
    evidence_selector.select_evidence.return_value = ev_set

    generator = AsyncMock()
    generator.generate.side_effect = RuntimeError("LLM rate limit exceeded")

    engine = OrchestrationEngine(
        retrieval_coordinator=retrieval_coord,
        evidence_selector=evidence_selector,
        generator=generator,
    )

    plan = _create_approved_plan(route="HYBRID")
    with pytest.raises(RuntimeError, match="LLM rate limit exceeded"):
        await engine.execute_run(
            plan,
            snapshot=MagicMock(spec=CorpusSnapshot),
            progress_sink=sink,
        )

    actual_timeline = [
        (ev.stage, ev.step_key, ev.status, ev.count, ev.ordinal)
        for ev in sink.events
    ]
    assert actual_timeline == [
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.STARTED, None, 1),
        (ProgressStage.PREPARING_INPUT, StepKey.UNDERSTAND, StepStatus.DONE, None, 2),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.STARTED, None, 3),
        (ProgressStage.RETRIEVING, StepKey.SEARCH, StepStatus.DONE, 1, 4),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.STARTED, None, 5),
        (ProgressStage.SELECTING_EVIDENCE, StepKey.SELECT, StepStatus.DONE, 1, 6),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.STARTED, None, 7),
        (ProgressStage.GENERATING, StepKey.WRITE, StepStatus.SKIPPED, None, 8),
    ]
    assert sink.open_stage is None


def test_progress_event_count_rules_and_privacy() -> None:
    # Only SEARCH DONE and SELECT DONE retain count
    ev_search_done = ProgressEvent.model_validate(
        {
            "schemaVersion": "internal.ai.progress.v1",
            "runId": RUN_ID,
            "planHash": PLAN_HASH,
            "ordinal": 1,
            "stage": "RETRIEVING",
            "stepKey": "SEARCH",
            "status": "DONE",
            "count": 15,
        }
    )
    assert ev_search_done.count == 15

    ev_search_started = ProgressEvent.model_validate(
        {
            "schemaVersion": "internal.ai.progress.v1",
            "runId": RUN_ID,
            "planHash": PLAN_HASH,
            "ordinal": 2,
            "stage": "RETRIEVING",
            "stepKey": "SEARCH",
            "status": "STARTED",
            "count": 15,
        }
    )
    assert ev_search_started.count is None

    ev_understand_done = ProgressEvent.model_validate(
        {
            "schemaVersion": "internal.ai.progress.v1",
            "runId": RUN_ID,
            "planHash": PLAN_HASH,
            "ordinal": 3,
            "stage": "PREPARING_INPUT",
            "stepKey": "UNDERSTAND",
            "status": "DONE",
            "count": 5,
        }
    )
    assert ev_understand_done.count is None

    # Model rejects privacy-leaking fields
    with pytest.raises(ValidationError):
        ProgressEvent.model_validate(
            {
                "schemaVersion": "internal.ai.progress.v1",
                "runId": RUN_ID,
                "planHash": PLAN_HASH,
                "ordinal": 4,
                "stage": "RETRIEVING",
                "stepKey": "SEARCH",
                "status": "DONE",
                "count": 5,
                "rawQuestion": "경복궁 어디야?",
            }
        )
