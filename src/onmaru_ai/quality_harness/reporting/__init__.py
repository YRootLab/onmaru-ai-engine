"""Quality reporting package (W19)."""

from .models import (
    NotificationPayload,
    NotificationResult,
    WeeklyQualitySummary,
)
from .service import NotificationSink, QualityReportingService

__all__ = [
    "NotificationPayload",
    "NotificationResult",
    "WeeklyQualitySummary",
    "NotificationSink",
    "QualityReportingService",
]
