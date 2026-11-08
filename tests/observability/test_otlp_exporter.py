from onmaru_ai.observability.correlation import (
    OpenTelemetryTelemetrySink,
    TelemetryEvent,
    create_telemetry_sink,
    parse_otlp_headers,
)


def test_parse_otlp_headers() -> None:
    raw = "Authorization=Bearer token123, X-Custom=Value"
    parsed = parse_otlp_headers(raw)
    assert parsed["Authorization"] == "Bearer token123"
    assert parsed["X-Custom"] == "Value"


def test_create_telemetry_sink_without_endpoint() -> None:
    sink = create_telemetry_sink(environ={})
    assert isinstance(sink, OpenTelemetryTelemetrySink)
    # Should safely record without throwing
    sink.record(TelemetryEvent(name="test_event", attributes={"key": "value"}))


def test_create_telemetry_sink_with_endpoint() -> None:
    env = {
        "OTEL_EXPORTER_OTLP_ENDPOINT": "http://otel-collector:4318/v1/traces",
        "OTEL_SERVICE_NAME": "onmaru-ai-test",
    }
    sink = create_telemetry_sink(environ=env)
    assert isinstance(sink, OpenTelemetryTelemetrySink)
