"""Quality Harness Review Models (W18)."""

from __future__ import annotations

import datetime
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


class EvidenceLevel(StrEnum):
    SUSPECTED = "SUSPECTED"
    REPRODUCED = "REPRODUCED"


class FailureCategory(StrEnum):
    RETRIEVAL_FAILURE = "RETRIEVAL_FAILURE"
    GROUNDING_FAILURE = "GROUNDING_FAILURE"
    POLICY_VIOLATION = "POLICY_VIOLATION"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    UNKNOWN = "UNKNOWN"


class ReviewStatus(StrEnum):
    PENDING_REVIEW = "PENDING_REVIEW"
    INVESTIGATING = "INVESTIGATING"
    RESOLVED = "RESOLVED"
    WONT_FIX = "WONT_FIX"
    SUPPRESSED = "SUPPRESSED"


_VALID_TRANSITIONS: dict[ReviewStatus, set[ReviewStatus]] = {
    ReviewStatus.PENDING_REVIEW: {
        ReviewStatus.INVESTIGATING,
        ReviewStatus.RESOLVED,
        ReviewStatus.WONT_FIX,
        ReviewStatus.SUPPRESSED,
    },
    ReviewStatus.INVESTIGATING: {
        ReviewStatus.RESOLVED,
        ReviewStatus.WONT_FIX,
        ReviewStatus.SUPPRESSED,
    },
    ReviewStatus.RESOLVED: set(),
    ReviewStatus.WONT_FIX: set(),
    ReviewStatus.SUPPRESSED: {ReviewStatus.PENDING_REVIEW},
}


class QualityModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class FailureCase(QualityModel):
    case_id: str
    run_or_query_id: str
    stage: str
    error_code: str
    category: FailureCategory
    evidence_level: EvidenceLevel
    status: ReviewStatus
    aggregate_key: str
    versions_hash: str
    recorded_at: datetime.datetime

    @model_validator(mode="before")
    @classmethod
    def forbid_sensitive_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            for forbidden in (
                "raw_query",
                "rawQuery",
                "member_id",
                "memberId",
                "source_body",
                "prompt",
                "model_tokens",
            ):
                if forbidden in data:
                    raise ValueError(f"raw text and memberId are forbidden: {forbidden}")
        return data


class ReviewQueueItem(QualityModel):
    aggregate_key: str
    stage: str
    error_code: str
    category: FailureCategory
    evidence_level: EvidenceLevel
    status: ReviewStatus
    occurrence_count: int
    run_ids: tuple[str, ...]
    first_seen_at: datetime.datetime
    last_seen_at: datetime.datetime
