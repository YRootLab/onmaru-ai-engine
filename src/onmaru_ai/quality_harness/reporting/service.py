"""Quality Reporting Service (W19)."""

from __future__ import annotations

import datetime
import logging
from collections import Counter
from collections.abc import Sequence
from typing import Protocol

from onmaru_ai.quality_harness.reporting.models import (
    NotificationPayload,
    NotificationResult,
    WeeklyQualitySummary,
)
from onmaru_ai.quality_harness.review.models import FailureCategory, ReviewQueueItem

logger = logging.getLogger(__name__)


class NotificationSink(Protocol):
    def send_notification(self, payload: NotificationPayload) -> None: ...


class QualityReportingService:
    def __init__(self, *, notification_sink: NotificationSink | None = None) -> None:
        self._notification_sink = notification_sink

    def generate_weekly_summary(
        self,
        items: Sequence[ReviewQueueItem],
        *,
        period_start: datetime.datetime,
        period_end: datetime.datetime,
    ) -> WeeklyQualitySummary:
        total = sum(i.occurrence_count for i in items)
        cat_dist: Counter[FailureCategory] = Counter()
        stage_dist: Counter[str] = Counter()

        for item in items:
            cat_dist[item.category] += item.occurrence_count
            stage_dist[item.stage] += item.occurrence_count

        return WeeklyQualitySummary(
            period_start=period_start,
            period_end=period_end,
            total_failures=total,
            category_distribution=dict(cat_dist),
            top_stages=dict(stage_dist),
        )

    def dispatch_notification(self, payload: NotificationPayload) -> NotificationResult:
        if self._notification_sink is None:
            return NotificationResult(success=True, error_message=None)

        try:
            self._notification_sink.send_notification(payload)
            return NotificationResult(success=True, error_message=None)
        except Exception as e:
            logger.warning("Failed to dispatch notification to %s: %s", payload.channel, e)
            return NotificationResult(success=False, error_message=str(e))
