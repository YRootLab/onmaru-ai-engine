from __future__ import annotations

import pytest
from pydantic import ValidationError

from onmaru_ai.observability import InMemoryTelemetrySink
from onmaru_ai.observability.rag import (
    InMemoryMetricSink,
    InMemorySpanSink,
    RagTelemetry,
    Stage,
    StageOutcome,
    TelemetrySpanSink,
)


def outcome(stage: Stage = Stage.BM25_SEARCH) -> StageOutcome:
    return StageOutcome(
        stage=stage,
        status="SUCCESS",
        duration_ms=12,
        route="HYBRID",
        candidate_count=8,
        unique_place_count=5,
        evidence_count=0,
        failure_stage=None,
        degraded_reason=None,
    )


def test_records_only_executed_stages_without_synthetic_retrieval_total() -> None:
    spans = InMemorySpanSink()
    metrics = InMemoryMetricSink()
    telemetry = RagTelemetry(environment="test", spans=spans, metrics=metrics)

    telemetry.record(outcome(Stage.BM25_SEARCH))
    telemetry.record(outcome(Stage.VECTOR_SEARCH).model_copy(update={"duration_ms": 18}))

    assert [span.name for span in spans.spans] == ["rag.bm25_search", "rag.vector_search"]
    assert all(span.name != "rag.retrieval" for span in spans.spans)
    durations = [
        point.value
        for point in metrics.points
        if point.name == "onmaru.ai.stage.duration"
    ]
    assert durations == [0.012, 0.018]


def test_sql_only_records_no_retrieval_span_when_only_validation_executes() -> None:
    spans = InMemorySpanSink()
    telemetry = RagTelemetry(environment="test", spans=spans, metrics=InMemoryMetricSink())

    telemetry.record(
        outcome(Stage.APPROVED_PLAN_VALIDATION).model_copy(
            update={"route": "SQL_ONLY", "candidate_count": 0, "unique_place_count": 0}
        )
    )

    assert [span.name for span in spans.spans] == ["rag.approved_plan_validation"]


def test_metric_labels_are_low_cardinality_and_never_include_identifiers_or_text() -> None:
    spans = InMemorySpanSink()
    metrics = InMemoryMetricSink()
    telemetry = RagTelemetry(environment="prod", spans=spans, metrics=metrics)

    telemetry.record(outcome())

    forbidden = {"runId", "traceId", "memberId", "placeId", "chunkId", "query", "prompt"}
    assert metrics.points
    assert all(not (set(point.labels) & forbidden) for point in metrics.points)
    allowed = {"environment", "stage", "outcome", "route", "reason"}
    assert all(set(point.labels) <= allowed for point in metrics.points)


@pytest.mark.parametrize("field", ["rawQuery", "memberId", "prompt", "sourceBody", "runId"])
def test_stage_outcome_rejects_sensitive_or_high_cardinality_fields(field: str) -> None:
    payload = outcome().model_dump(by_alias=True)
    payload[field] = "secret"
    with pytest.raises(ValidationError):
        StageOutcome.model_validate(payload)


def test_export_failure_does_not_fail_execution_and_increments_drop_metric() -> None:
    class FailingSpanSink:
        def export(self, _span: object) -> None:
            raise RuntimeError("collector unavailable")

    metrics = InMemoryMetricSink()
    telemetry = RagTelemetry(environment="prod", spans=FailingSpanSink(), metrics=metrics)

    telemetry.record(outcome())

    dropped = [point for point in metrics.points if point.name == "onmaru.ai.trace.dropped.total"]
    assert len(dropped) == 1
    assert dropped[0].labels == {"environment": "prod", "reason": "export_error"}
    assert dropped[0].value == 1


def test_metric_export_failure_is_swallowed_and_counted_separately() -> None:
    class FailingMetricSink:
        def record(self, _point: object) -> None:
            raise RuntimeError("metrics unavailable")

    spans = InMemorySpanSink()
    telemetry = RagTelemetry(environment="prod", spans=spans, metrics=FailingMetricSink())

    telemetry.record(outcome())

    assert len(spans.spans) == 1
    assert telemetry.metric_drop_count == 3


def test_traceparent_is_validated_without_becoming_a_metric_label() -> None:
    spans = InMemorySpanSink()
    telemetry = RagTelemetry(environment="test", spans=spans, metrics=InMemoryMetricSink())
    parent = "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01"

    telemetry.record(outcome(), traceparent=parent)

    assert spans.spans[0].trace_id == "4bf92f3577b34da6a3ce929d0e0e4736"
    assert spans.spans[0].parent_span_id == "00f067aa0ba902b7"
    with pytest.raises(ValueError, match="traceparent"):
        telemetry.record(outcome(), traceparent="invalid")


def test_candidate_histogram_is_emitted_only_for_candidate_stages() -> None:
    metrics = InMemoryMetricSink()
    telemetry = RagTelemetry(environment="test", spans=InMemorySpanSink(), metrics=metrics)

    telemetry.record(outcome(Stage.BM25_SEARCH))
    telemetry.record(outcome(Stage.GENERATION).model_copy(update={"candidate_count": None}))

    candidates = [p for p in metrics.points if p.name == "onmaru.ai.retrieval.candidates"]
    assert len(candidates) == 1
    assert candidates[0].value == 8


def test_unknown_route_status_stage_and_reason_are_rejected() -> None:
    payload = outcome().model_dump(by_alias=True)
    for field, value in (
        ("route", "OTHER_ROUTE"),
        ("status", "BROKEN"),
        ("stage", "NOT_A_STAGE"),
        ("degradedReason", "free form message"),
        ("failureStage", "free form message"),
    ):
        changed = {**payload, field: value}
        with pytest.raises(ValidationError):
            StageOutcome.model_validate(changed)


def test_environment_label_is_a_closed_vocabulary() -> None:
    with pytest.raises(ValueError, match="environment"):
        RagTelemetry(
            environment="preview-123",  # type: ignore[arg-type]
            spans=InMemorySpanSink(),
            metrics=InMemoryMetricSink(),
        )


def test_repository_otel_sink_bridge_receives_only_allowlisted_stage_attributes() -> None:
    sink = InMemoryTelemetrySink()
    telemetry = RagTelemetry(
        environment="test",
        spans=TelemetrySpanSink(sink),
        metrics=InMemoryMetricSink(),
    )

    telemetry.record(outcome())

    assert len(sink.events) == 1
    assert sink.events[0].name == "rag.bm25_search"
    assert set(sink.events[0].attributes) == {
        "stage",
        "outcome",
        "route",
        "durationMs",
        "candidateCount",
        "uniquePlaceCount",
        "evidenceCount",
    }
