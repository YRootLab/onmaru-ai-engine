"""Tests for W19 quality aggregation, weekly summary reports, and notification boundaries."""

from __future__ import annotations

import datetime
from unittest.mock import MagicMock

from onmaru_ai.quality_harness.reporting.models import (
    NotificationPayload,
)
from onmaru_ai.quality_harness.reporting.service import QualityReportingService
from onmaru_ai.quality_harness.review.models import (
    EvidenceLevel,
    FailureCategory,
    ReviewQueueItem,
    ReviewStatus,
)


def _sample_queue_item(key: str, count: int = 5) -> ReviewQueueItem:
    now = datetime.datetime.now(datetime.UTC)
    return ReviewQueueItem(
        aggregate_key=key,
        stage="BM25_SEARCH",
        error_code="DB_TIMEOUT",
        category=FailureCategory.RETRIEVAL_FAILURE,
        evidence_level=EvidenceLevel.SUSPECTED,
        status=ReviewStatus.PENDING_REVIEW,
        occurrence_count=count,
        run_ids=(f"run-{key}-1", f"run-{key}-2"),
        first_seen_at=now - datetime.timedelta(days=2),
        last_seen_at=now,
    )


def test_generate_weekly_summary_anonymized_and_aggregated() -> None:
    service = QualityReportingService()
    items = [
        _sample_queue_item("k1", count=10),
        _sample_queue_item("k2", count=3),
    ]
    summary = service.generate_weekly_summary(
        items,
        period_start=datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7),
        period_end=datetime.datetime.now(datetime.UTC),
    )
    assert summary.total_failures == 13
    assert summary.category_distribution[FailureCategory.RETRIEVAL_FAILURE] == 13
    # Ensure raw run IDs, user queries or private tokens are not leaked in human text
    text_repr = summary.render_markdown()
    assert "user private" not in text_repr
    assert "run-k1-1" not in text_repr  # Anonymized / aggregate only


def test_notification_delivery_decoupled_from_pipeline() -> None:
    # Notification sink failure must not raise or block pipeline
    sink = MagicMock()
    sink.send_notification.side_effect = ConnectionError("Discord/Email webhook down")

    service = QualityReportingService(notification_sink=sink)
    payload = NotificationPayload(
        channel="discord",
        title="Weekly Quality Alert",
        summary_markdown="# Weekly Summary",
        severity="INFO",
    )
    # Must handle failure gracefully without raising exception
    result = service.dispatch_notification(payload)
    assert result.success is False
    assert result.error_message is not None
    assert "Discord/Email webhook down" in result.error_message
