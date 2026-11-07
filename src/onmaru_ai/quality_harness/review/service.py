"""Quality Harness Review Queue Service (W18)."""

from __future__ import annotations

import datetime
import hashlib
import json
import uuid
from collections.abc import Mapping
from typing import Any

from onmaru_ai.quality_harness.review.models import (
    _VALID_TRANSITIONS,
    EvidenceLevel,
    FailureCase,
    FailureCategory,
    ReviewQueueItem,
    ReviewStatus,
)


def _compute_versions_hash(versions: Mapping[str, Any]) -> str:
    serialized = json.dumps(versions, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()[:16]


def _compute_aggregate_key(
    stage: str, error_code: str, category: FailureCategory, versions_hash: str
) -> str:
    raw = f"{stage}:{error_code}:{category.value}:{versions_hash}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _categorize(stage: str, error_code: str) -> FailureCategory:
    if "BM25" in stage or "VECTOR" in stage or "RRF" in stage or "RETRIEVAL" in stage:
        return FailureCategory.RETRIEVAL_FAILURE
    if "EVIDENCE" in stage or "CLAIM" in error_code or "GROUND" in stage:
        return FailureCategory.GROUNDING_FAILURE
    if (
        "POLICY" in error_code
        or "AUTH" in error_code
        or "RIGHTS" in error_code
        or "REVOCATION" in error_code
    ):
        return FailureCategory.POLICY_VIOLATION
    if "TIMEOUT" in error_code or "ERROR" in error_code:
        return FailureCategory.INFRASTRUCTURE_ERROR
    return FailureCategory.UNKNOWN


class ReviewQueueService:
    def __init__(self) -> None:
        self._cases: dict[str, FailureCase] = {}
        self._queue: dict[str, ReviewQueueItem] = {}

    def record_operational_failure(
        self,
        run_id: str,
        stage: str,
        error_code: str,
        versions: Mapping[str, Any],
        *,
        recorded_at: datetime.datetime | None = None,
        **extra: Any,
    ) -> FailureCase:
        category = _categorize(stage, error_code)
        versions_hash = _compute_versions_hash(versions)
        aggregate_key = _compute_aggregate_key(stage, error_code, category, versions_hash)
        now = recorded_at or datetime.datetime.now(datetime.UTC)

        data = {
            "case_id": f"case-{uuid.uuid4().hex[:12]}",
            "run_or_query_id": run_id,
            "stage": stage,
            "error_code": error_code,
            "category": category,
            "evidence_level": EvidenceLevel.SUSPECTED,
            "status": ReviewStatus.PENDING_REVIEW,
            "aggregate_key": aggregate_key,
            "versions_hash": versions_hash,
            "recorded_at": now,
            **extra,
        }
        case = FailureCase.model_validate(data)
        self._cases[case.case_id] = case
        self._update_queue(case)
        return case

    def record_gold_replay_failure(
        self,
        query_id: str,
        stage: str,
        error_code: str,
        versions: Mapping[str, Any],
        *,
        recorded_at: datetime.datetime | None = None,
        **extra: Any,
    ) -> FailureCase:
        category = _categorize(stage, error_code)
        versions_hash = _compute_versions_hash(versions)
        aggregate_key = _compute_aggregate_key(stage, error_code, category, versions_hash)
        now = recorded_at or datetime.datetime.now(datetime.UTC)

        data = {
            "case_id": f"case-{uuid.uuid4().hex[:12]}",
            "run_or_query_id": query_id,
            "stage": stage,
            "error_code": error_code,
            "category": category,
            "evidence_level": EvidenceLevel.REPRODUCED,
            "status": ReviewStatus.PENDING_REVIEW,
            "aggregate_key": aggregate_key,
            "versions_hash": versions_hash,
            "recorded_at": now,
            **extra,
        }
        case = FailureCase.model_validate(data)
        self._cases[case.case_id] = case
        self._update_queue(case)
        return case

    def _update_queue(self, case: FailureCase) -> None:
        key = case.aggregate_key
        existing = self._queue.get(key)
        if existing is None:
            self._queue[key] = ReviewQueueItem(
                aggregate_key=key,
                stage=case.stage,
                error_code=case.error_code,
                category=case.category,
                evidence_level=case.evidence_level,
                status=case.status,
                occurrence_count=1,
                run_ids=(case.run_or_query_id,),
                first_seen_at=case.recorded_at,
                last_seen_at=case.recorded_at,
            )
        else:
            new_run_ids = existing.run_ids + (case.run_or_query_id,)
            self._queue[key] = ReviewQueueItem(
                aggregate_key=key,
                stage=existing.stage,
                error_code=existing.error_code,
                category=existing.category,
                evidence_level=existing.evidence_level,
                status=existing.status,
                occurrence_count=existing.occurrence_count + 1,
                run_ids=new_run_ids,
                first_seen_at=min(existing.first_seen_at, case.recorded_at),
                last_seen_at=max(existing.last_seen_at, case.recorded_at),
            )

    def get_queue_item(self, aggregate_key: str) -> ReviewQueueItem | None:
        return self._queue.get(aggregate_key)

    def get_queue_item_by_run_id(self, run_id: str) -> ReviewQueueItem | None:
        for item in self._queue.values():
            if run_id in item.run_ids:
                return item
        return None

    def transition_status(self, aggregate_key: str, new_status: ReviewStatus) -> None:
        item = self._queue.get(aggregate_key)
        if item is None:
            raise KeyError(f"Item not found: {aggregate_key}")
        allowed = _VALID_TRANSITIONS.get(item.status, set())
        if new_status not in allowed:
            raise ValueError(f"Invalid status transition from {item.status} to {new_status}")
        self._queue[aggregate_key] = ReviewQueueItem(
            aggregate_key=item.aggregate_key,
            stage=item.stage,
            error_code=item.error_code,
            category=item.category,
            evidence_level=item.evidence_level,
            status=new_status,
            occurrence_count=item.occurrence_count,
            run_ids=item.run_ids,
            first_seen_at=item.first_seen_at,
            last_seen_at=item.last_seen_at,
        )

    def purge_expired(
        self, retention_days: int = 90, current_time: datetime.datetime | None = None
    ) -> int:
        now = current_time or datetime.datetime.now(datetime.UTC)
        cutoff = now - datetime.timedelta(days=retention_days)

        expired_case_ids = [
            case_id for case_id, case in self._cases.items() if case.recorded_at < cutoff
        ]
        for cid in expired_case_ids:
            del self._cases[cid]

        # Rebuild or purge queue items
        purged_keys: list[str] = []
        for key, item in list(self._queue.items()):
            active_run_ids = tuple(
                rid
                for rid in item.run_ids
                if any(c.run_or_query_id == rid for c in self._cases.values())
            )
            if not active_run_ids:
                del self._queue[key]
                purged_keys.append(key)
            elif len(active_run_ids) != len(item.run_ids):
                self._queue[key] = ReviewQueueItem(
                    aggregate_key=item.aggregate_key,
                    stage=item.stage,
                    error_code=item.error_code,
                    category=item.category,
                    evidence_level=item.evidence_level,
                    status=item.status,
                    occurrence_count=len(active_run_ids),
                    run_ids=active_run_ids,
                    first_seen_at=item.first_seen_at,
                    last_seen_at=item.last_seen_at,
                )

        return len(expired_case_ids)
