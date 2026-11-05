"""Quality reporting models (W19)."""

from __future__ import annotations

import datetime
from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, Field

from onmaru_ai.quality_harness.review.models import FailureCategory


class QualityReportModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class WeeklyQualitySummary(QualityReportModel):
    period_start: datetime.datetime
    period_end: datetime.datetime
    total_failures: int
    category_distribution: Mapping[FailureCategory, int]
    top_stages: Mapping[str, int]
    generated_at: datetime.datetime = Field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC)
    )

    def render_markdown(self) -> str:
        s_date = self.period_start.strftime("%Y-%m-%d")
        e_date = self.period_end.strftime("%Y-%m-%d")
        lines = [
            f"# Weekly RAG Quality Summary ({s_date} ~ {e_date})",
            "",
            f"- **Total Recorded Failures / Signals**: {self.total_failures}",
            "",
            "## Category Breakdown",
        ]
        for cat, cnt in sorted(self.category_distribution.items(), key=lambda x: -x[1]):
            lines.append(f"- **{cat.value}**: {cnt}")

        lines.extend(["", "## Top Failure Stages"])
        for stage, cnt in sorted(self.top_stages.items(), key=lambda x: -x[1]):
            lines.append(f"- `{stage}`: {cnt}")

        return "\n".join(lines)


class NotificationPayload(QualityReportModel):
    channel: str
    title: str
    summary_markdown: str
    severity: str = "INFO"


class NotificationResult(QualityReportModel):
    success: bool
    error_message: str | None = None
