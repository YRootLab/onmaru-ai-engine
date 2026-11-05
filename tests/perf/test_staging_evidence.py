"""Tests for W21 staging load simulation and release evidence packaging."""

from __future__ import annotations

from scripts.perf.run_staging_evidence import (
    generate_release_evidence,
    simulate_staging_load,
)


def test_simulate_staging_load_metrics_within_budget() -> None:
    metrics = simulate_staging_load(concurrent_runs=5, sse_connections=100)
    assert metrics.concurrent_runs == 5
    assert metrics.sse_connections == 100
    assert metrics.successful_requests == 50
    assert metrics.failed_requests == 0
    assert metrics.oom_killed is False
    assert metrics.db_connection_pool_exhausted is False
    assert metrics.max_rss_mb < 500.0  # Well within 1200MB budget
    assert metrics.p95_latency_ms > 0.0


def test_infrastructure_gates_default_pending_holds_release() -> None:
    report = generate_release_evidence(image_tag="onmaru-ai-engine:sha-test", environ={})
    # By default, without explicit BE staging confirmations, release MUST be held
    assert report.release_decision == "HELD_BE_INFRA_PENDING"
    assert "BE host upgrade to 2GB" in report.decision_reason
    assert report.infrastructure_gates.all_gates_passed is False


def test_release_approved_when_all_gates_pass() -> None:
    env = {
        "STAGING_LIGHTSAIL_2GB": "true",
        "STAGING_PGVECTOR_READY": "true",
        "STAGING_POSTGIS_READY": "true",
        "STAGING_AI_SCHEMA_ISOLATED": "true",
        "STAGING_BE_DEPLOYER_COMPAT": "true",
    }
    report = generate_release_evidence(
        image_tag="onmaru-ai-engine:sha-test",
        image_digest="sha256:abcd1234ef5678",
        environ=env,
    )
    assert report.release_decision == "RELEASE_APPROVED"
    assert report.infrastructure_gates.all_gates_passed is True
    assert report.image_digest == "sha256:abcd1234ef5678"
    assert report.contract_version == "ai-release-evidence.v1"
