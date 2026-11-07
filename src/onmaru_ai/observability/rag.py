"""Low-cardinality RAG stage telemetry boundary (W15).

The adapter records only stages explicitly handed to it. It never manufactures
route steps or combines sibling durations, and exporter failures never escape
into the user execution path.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from typing import Annotated, Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from onmaru_ai.contracts.models import Route
from onmaru_ai.contracts.vocabulary import FailureStage
from onmaru_ai.observability.correlation import TelemetryEvent, TelemetrySink


class Stage(StrEnum):
    AUTH_CONTRACT = "AUTH_CONTRACT"
    INPUT_PRIVACY = "INPUT_PRIVACY"
    QUERY_PREPROCESSING = "QUERY_PREPROCESSING"
    QUERY_INTERPRETATION = "QUERY_INTERPRETATION"
    SEARCH_ROUTING = "SEARCH_ROUTING"
    PLAN_PROPOSAL = "PLAN_PROPOSAL"
    PLAN_AUTHORIZATION = "PLAN_AUTHORIZATION"
    CANONICAL_SQL = "CANONICAL_SQL"
    APPROVED_PLAN_VALIDATION = "APPROVED_PLAN_VALIDATION"
    QUERY_MATERIALIZATION = "QUERY_MATERIALIZATION"
    BM25_SEARCH = "BM25_SEARCH"
    QUERY_EMBEDDING = "QUERY_EMBEDDING"
    VECTOR_SEARCH = "VECTOR_SEARCH"
    RRF_FUSION = "RRF_FUSION"
    CANDIDATE_POLICY = "CANDIDATE_POLICY"
    RERANK = "RERANK"
    EVIDENCE_SELECT = "EVIDENCE_SELECT"
    CONTEXT_ASSEMBLY = "CONTEXT_ASSEMBLY"
    GENERATION = "GENERATION"
    PROPOSAL_PARSE = "PROPOSAL_PARSE"
    LOCAL_EVIDENCE_VALIDATION = "LOCAL_EVIDENCE_VALIDATION"
    FINAL_VALIDATION = "FINAL_VALIDATION"
    PERSISTENCE = "PERSISTENCE"
    SSE_DELIVERY = "SSE_DELIVERY"


Status = Literal["SUCCESS", "EMPTY", "DEGRADED", "FAILED", "SKIPPED"]
DegradedReason = Literal[
    "OTHER_RETRIEVER",
    "RRF_ORDER",
    "VERIFIED_BASELINE",
    "CLARIFICATION",
    "FAILED_CLOSED",
]
Environment = Literal["local", "dev", "test", "staging", "prod"]
_ENVIRONMENTS = {"local", "dev", "test", "staging", "prod"}
Count = Annotated[int, Field(ge=0, strict=True)]


class StageOutcome(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        alias_generator=to_camel,
        populate_by_name=True,
    )

    stage: Stage
    status: Status
    duration_ms: Annotated[int, Field(ge=0, strict=True)]
    route: Route
    candidate_count: Count | None
    unique_place_count: Count | None
    evidence_count: Count | None
    failure_stage: FailureStage | None
    degraded_reason: DegradedReason | None


@dataclass(frozen=True)
class SpanRecord:
    name: str
    attributes: dict[str, str | int]
    trace_id: str | None = None
    parent_span_id: str | None = None


@dataclass(frozen=True)
class MetricPoint:
    name: str
    value: int | float
    labels: dict[str, str]


class SpanSink(Protocol):
    def export(self, span: SpanRecord) -> None: ...


class MetricSink(Protocol):
    def record(self, point: MetricPoint) -> None: ...


class InMemorySpanSink:
    def __init__(self) -> None:
        self.spans: list[SpanRecord] = []

    def export(self, span: SpanRecord) -> None:
        self.spans.append(span)


class InMemoryMetricSink:
    def __init__(self) -> None:
        self.points: list[MetricPoint] = []

    def record(self, point: MetricPoint) -> None:
        self.points.append(point)


class TelemetrySpanSink:
    """Bridge RAG stage records to the repository's configured OTel sink."""

    def __init__(self, sink: TelemetrySink) -> None:
        self._sink = sink

    def export(self, span: SpanRecord) -> None:
        self._sink.record(
            TelemetryEvent(
                name=span.name,
                attributes={name: str(value) for name, value in span.attributes.items()},
            )
        )


_TRACEPARENT = re.compile(
    r"^(?P<version>[0-9a-f]{2})-(?P<trace>[0-9a-f]{32})-"
    r"(?P<parent>[0-9a-f]{16})-(?P<flags>[0-9a-f]{2})$"
)
_CANDIDATE_STAGES = {
    Stage.BM25_SEARCH,
    Stage.VECTOR_SEARCH,
    Stage.RRF_FUSION,
    Stage.CANDIDATE_POLICY,
    Stage.RERANK,
    Stage.EVIDENCE_SELECT,
}


class RagTelemetry:
    def __init__(self, *, environment: Environment, spans: SpanSink, metrics: MetricSink) -> None:
        if environment not in _ENVIRONMENTS:
            raise ValueError("environment must be one of local, dev, test, staging, prod")
        self._environment = environment
        self._spans = spans
        self._metrics = metrics
        self.metric_drop_count = 0

    def record(self, outcome: StageOutcome, *, traceparent: str | None = None) -> None:
        trace_id, parent_span_id = self._parse_traceparent(traceparent)
        span = SpanRecord(
            name=f"rag.{outcome.stage.value.lower()}",
            attributes=self._span_attributes(outcome),
            trace_id=trace_id,
            parent_span_id=parent_span_id,
        )
        try:
            self._spans.export(span)
            self._metric(
                MetricPoint(
                    name="onmaru.ai.trace.export.total",
                    value=1,
                    labels={"environment": self._environment, "reason": "none"},
                )
            )
        except Exception:
            self._metric(
                MetricPoint(
                    name="onmaru.ai.trace.dropped.total",
                    value=1,
                    labels={"environment": self._environment, "reason": "export_error"},
                )
            )
        labels = {
            "environment": self._environment,
            "stage": outcome.stage.value,
            "outcome": outcome.status,
            "route": outcome.route,
        }
        self._metric(
            MetricPoint(
                name="onmaru.ai.stage.duration",
                value=outcome.duration_ms / 1000,
                labels=labels,
            )
        )
        if outcome.stage in _CANDIDATE_STAGES and outcome.candidate_count is not None:
            self._metric(
                MetricPoint(
                    name="onmaru.ai.retrieval.candidates",
                    value=outcome.candidate_count,
                    labels={"environment": self._environment, "stage": outcome.stage.value},
                )
            )

    def _metric(self, point: MetricPoint) -> None:
        try:
            self._metrics.record(point)
        except Exception:
            self.metric_drop_count += 1

    @staticmethod
    def _parse_traceparent(traceparent: str | None) -> tuple[str | None, str | None]:
        if traceparent is None:
            return None, None
        match = _TRACEPARENT.fullmatch(traceparent)
        if match is None or match.group("trace") == "0" * 32 or match.group("parent") == "0" * 16:
            raise ValueError("invalid traceparent")
        return match.group("trace"), match.group("parent")

    @staticmethod
    def _span_attributes(outcome: StageOutcome) -> dict[str, str | int]:
        attributes: dict[str, str | int] = {
            "stage": outcome.stage.value,
            "outcome": outcome.status,
            "route": outcome.route,
            "durationMs": outcome.duration_ms,
        }
        for key, value in (
            ("candidateCount", outcome.candidate_count),
            ("uniquePlaceCount", outcome.unique_place_count),
            ("evidenceCount", outcome.evidence_count),
            ("failureStage", outcome.failure_stage),
            ("degradedReason", outcome.degraded_reason),
        ):
            if value is not None:
                attributes[key] = value
        return attributes
