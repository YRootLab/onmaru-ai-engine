"""Tests for W18 FailureCase classification, review queue, and retention."""

from __future__ import annotations

import datetime

import pytest

from onmaru_ai.quality_harness.review.models import (
    EvidenceLevel,
    FailureCategory,
    ReviewStatus,
)
from onmaru_ai.quality_harness.review.service import ReviewQueueService


def test_classify_operational_observation_as_suspected() -> None:
    # Operational observation has no ground truth, so evidenceLevel must be SUSPECTED
    service = ReviewQueueService()
    case = service.record_operational_failure(
        run_id="run-1",
        stage="BM25_SEARCH",
        error_code="DB_TIMEOUT",
        versions={
            "corpusRevision": "c1",
            "questionDictionaryVersion": "q1",
            "sourceRevocationSequence": 1,
        },
    )
    assert case.evidence_level == EvidenceLevel.SUSPECTED
    assert case.category == FailureCategory.RETRIEVAL_FAILURE
    assert case.status == ReviewStatus.PENDING_REVIEW


def test_classify_gold_replay_as_reproduced() -> None:
    # Gold replay has ground truth, so evidenceLevel must be REPRODUCED
    service = ReviewQueueService()
    case = service.record_gold_replay_failure(
        query_id="query-123",
        stage="EVIDENCE",
        error_code="CLAIM_UNSUPPORTED",
        versions={
            "corpusRevision": "c1",
            "questionDictionaryVersion": "q1",
            "sourceRevocationSequence": 1,
        },
    )
    assert case.evidence_level == EvidenceLevel.REPRODUCED
    assert case.category == FailureCategory.GROUNDING_FAILURE
    assert case.status == ReviewStatus.PENDING_REVIEW


def test_deduplicate_identical_signals_into_same_review_item() -> None:
    # Multiple failures with same aggregate key aggregate into one item
    service = ReviewQueueService()
    versions = {
        "corpusRevision": "c1",
        "questionDictionaryVersion": "q1",
        "sourceRevocationSequence": 1,
    }
    c1 = service.record_operational_failure("run-1", "BM25_SEARCH", "DB_TIMEOUT", versions)
    c2 = service.record_operational_failure("run-2", "BM25_SEARCH", "DB_TIMEOUT", versions)

    assert c1.aggregate_key == c2.aggregate_key
    queue_item = service.get_queue_item(c1.aggregate_key)
    assert queue_item is not None
    assert queue_item.occurrence_count == 2
    assert set(queue_item.run_ids) == {"run-1", "run-2"}


def test_forbid_raw_query_pii_and_model_tokens() -> None:
    # FailureCase schema forbids raw queries, user/member IDs, full body, model outputs
    service = ReviewQueueService()
    with pytest.raises(ValueError, match="raw text and memberId are forbidden"):
        service.record_operational_failure(
            "run-1",
            "BM25_SEARCH",
            "DB_TIMEOUT",
            {
                "corpusRevision": "c1",
                "questionDictionaryVersion": "q1",
                "sourceRevocationSequence": 1,
            },
            raw_query="user private query",
        )


def test_closed_status_state_transitions() -> None:
    # State transitions: PENDING_REVIEW -> INVESTIGATING -> RESOLVED / WONT_FIX / SUPPRESSED
    service = ReviewQueueService()
    versions = {
        "corpusRevision": "c1",
        "questionDictionaryVersion": "q1",
        "sourceRevocationSequence": 1,
    }
    case = service.record_operational_failure("run-1", "BM25_SEARCH", "DB_TIMEOUT", versions)

    # Valid transitions
    service.transition_status(case.aggregate_key, ReviewStatus.INVESTIGATING)
    item = service.get_queue_item(case.aggregate_key)
    assert item is not None and item.status == ReviewStatus.INVESTIGATING

    service.transition_status(case.aggregate_key, ReviewStatus.RESOLVED)
    item = service.get_queue_item(case.aggregate_key)
    assert item is not None and item.status == ReviewStatus.RESOLVED

    # Invalid backward transition from terminal state
    with pytest.raises(ValueError, match="Invalid status transition"):
        service.transition_status(case.aggregate_key, ReviewStatus.PENDING_REVIEW)


def test_retention_and_gc_expires_after_3_months() -> None:
    service = ReviewQueueService()
    versions = {
        "corpusRevision": "c1",
        "questionDictionaryVersion": "q1",
        "sourceRevocationSequence": 1,
    }
    now = datetime.datetime.now(datetime.UTC)
    old_time = now - datetime.timedelta(days=95)

    service.record_operational_failure(
        "run-old", "BM25_SEARCH", "DB_TIMEOUT", versions, recorded_at=old_time
    )
    service.record_operational_failure(
        "run-new", "BM25_SEARCH", "DB_TIMEOUT", versions, recorded_at=now
    )

    # Run GC with 90-day retention
    purged_count = service.purge_expired(retention_days=90, current_time=now)
    assert purged_count == 1
    # Check that old run is removed from queue
    queue_item = service.get_queue_item_by_run_id("run-old")
    assert queue_item is None
