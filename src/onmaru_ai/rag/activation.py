from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Literal, Protocol

from onmaru_ai.evals import EvalReport

logger = logging.getLogger(__name__)

RagActivationAction = Literal["ACTIVATE", "ROLLBACK"]
RagActivationReason = Literal[
    "FEATURE_FLAG_DISABLED",
    "EVAL_GATE_FAILED",
    "BASELINE_COMPARISON_REQUIRED",
    "BASELINE_GAIN_INSUFFICIENT",
    "CORPUS_REVISION_MISMATCH",
    "CANDIDATE_POLICY_UNSUPPORTED",
    "EVAL_GATE_PASSED_WITH_BASELINE_GAIN",
]


@dataclass(frozen=True)
class RagActivationThresholds:
    min_retrieval_recall_at_5_delta: float = 0.0
    min_ndcg_at_3_delta: float = 0.0
    min_claim_support_delta: float = 0.0
    max_latency_p95_ms_delta: int | None = None
    max_mean_cost_micros_delta: int | None = None


@dataclass(frozen=True)
class RagActivationDecision:
    enabled: bool
    action: RagActivationAction
    reason: RagActivationReason
    candidate_policy: str
    corpus_revision_id: str
    image_digest: str
    embedding_profile: str
    dataset_input_sha256: str
    dataset_gold_sha256: str
    evaluated_at: datetime
    metric_deltas: dict[str, float | int]
    baseline_passed: bool
    candidate_passed: bool


class RagActivationLog(Protocol):
    durable: bool

    def append(self, decision: RagActivationDecision) -> None: ...

    def latest_for_revision(self, corpus_revision_id: str) -> RagActivationDecision | None: ...


class InMemoryRagActivationLog:
    durable = False

    def __init__(self) -> None:
        self._records: list[RagActivationDecision] = []

    @property
    def records(self) -> tuple[RagActivationDecision, ...]:
        return tuple(self._records)

    def append(self, decision: RagActivationDecision) -> None:
        self._records.append(decision)

    def latest_for_revision(self, corpus_revision_id: str) -> RagActivationDecision | None:
        for record in reversed(self._records):
            if record.corpus_revision_id == corpus_revision_id:
                return record
        return None


class RagActivationPolicy:
    def __init__(
        self,
        *,
        thresholds: RagActivationThresholds | None = None,
        log: RagActivationLog | None = None,
        feature_enabled: bool = True,
        clock: Callable[[], datetime] | None = None,
    ) -> None:
        self._thresholds = thresholds or RagActivationThresholds()
        self._log = log or InMemoryRagActivationLog()
        self._feature_enabled = feature_enabled
        self._clock = clock or (lambda: datetime.now(UTC))

    def evaluate(self, report: EvalReport, *, corpus_revision_id: str) -> RagActivationDecision:
        if not corpus_revision_id.strip():
            raise ValueError("corpus_revision_id must not be blank")

        reason = self._reason(report, corpus_revision_id)
        enabled = reason == "EVAL_GATE_PASSED_WITH_BASELINE_GAIN"
        decision = RagActivationDecision(
            enabled=enabled,
            action="ACTIVATE" if enabled else "ROLLBACK",
            reason=reason,
            candidate_policy=report.candidate_policy,
            corpus_revision_id=corpus_revision_id,
            image_digest=report.image_digest,
            embedding_profile=report.embedding_profile,
            dataset_input_sha256=report.dataset.input_sha256,
            dataset_gold_sha256=report.dataset.gold_sha256,
            evaluated_at=self._clock(),
            metric_deltas=dict(report.comparison.metric_deltas)
            if report.comparison is not None
            else {},
            baseline_passed=self._baseline_passed(report),
            candidate_passed=report.overall_passed,
        )
        self._log.append(decision)
        logger.info(
            "rag.activation.decision action=%s reason=%s candidate_policy=%s corpus_revision_id=%s "
            "image_digest=%s embedding_profile=%s "
            "dataset_gold_sha256=%s enabled=%s",
            decision.action,
            decision.reason,
            decision.candidate_policy,
            decision.corpus_revision_id,
            decision.image_digest,
            decision.embedding_profile,
            decision.dataset_gold_sha256,
            decision.enabled,
        )
        return decision

    def _reason(self, report: EvalReport, corpus_revision_id: str) -> RagActivationReason:
        if not self._feature_enabled:
            return "FEATURE_FLAG_DISABLED"
        if report.corpus_revision != corpus_revision_id:
            return "CORPUS_REVISION_MISMATCH"
        if report.candidate_policy != "v1":
            return "CANDIDATE_POLICY_UNSUPPORTED"
        if not report.overall_passed or not self._baseline_passed(report):
            return "EVAL_GATE_FAILED"
        comparison = report.comparison
        if comparison is None or not comparison.compatible:
            return "BASELINE_COMPARISON_REQUIRED"
        if not self._has_required_gain(comparison.metric_deltas):
            return "BASELINE_GAIN_INSUFFICIENT"
        return "EVAL_GATE_PASSED_WITH_BASELINE_GAIN"

    @staticmethod
    def _baseline_passed(report: EvalReport) -> bool:
        return (
            report.comparison is not None
            and report.comparison.compatible
            and report.comparison.baseline_passed
            and all(gate.passed for gate in report.gates)
        )

    def _has_required_gain(self, deltas: dict[str, float | int]) -> bool:
        thresholds = self._thresholds
        quality_passed = (
            float(deltas.get("retrievalRecallAt5", 0.0))
            >= thresholds.min_retrieval_recall_at_5_delta
            and float(deltas.get("ndcgAt3", 0.0)) >= thresholds.min_ndcg_at_3_delta
            and float(deltas.get("claimSupport", 0.0)) >= thresholds.min_claim_support_delta
        )
        latency_passed = (
            thresholds.max_latency_p95_ms_delta is None
            or int(deltas.get("latencyP95Ms", 0)) <= thresholds.max_latency_p95_ms_delta
        )
        cost_passed = (
            thresholds.max_mean_cost_micros_delta is None
            or int(deltas.get("meanCostMicros", 0)) <= thresholds.max_mean_cost_micros_delta
        )
        has_positive_quality_delta = (
            float(deltas.get("retrievalRecallAt5", 0.0)) > 0.0
            or float(deltas.get("ndcgAt3", 0.0)) > 0.0
            or float(deltas.get("claimSupport", 0.0)) > 0.0
        )
        return quality_passed and latency_passed and cost_passed and has_positive_quality_delta


class RagRetrievalGate:
    def __init__(self, log: RagActivationLog) -> None:
        self._log = log

    def retrieve_if_active(
        self,
        *,
        corpus_revision_id: str,
        retrieve: Callable[[], tuple[str, ...]],
    ) -> tuple[str, ...]:
        decision = self._log.latest_for_revision(corpus_revision_id)
        if decision is None or not decision.enabled:
            return ()
        return retrieve()
