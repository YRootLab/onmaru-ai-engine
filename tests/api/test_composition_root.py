"""Unit tests verifying production composition root in default create_app()."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from pathlib import Path

import httpx
import pytest
from fastapi.testclient import TestClient

from onmaru_ai.api.plan_execute import PlanExecuteService
from onmaru_ai.composition import (
    bind_spring_grant_reference,
    create_production_plan_execute_service,
)
from onmaru_ai.config.secrets import FakeSecretProvider
from onmaru_ai.contracts.models import ApprovedQueryPlan
from onmaru_ai.main import create_app
from onmaru_ai.rag import InMemoryRagActivationLog


def test_default_create_app_wires_production_components() -> None:
    app = create_app(secret_provider=FakeSecretProvider())
    assert hasattr(app.state, "plan_execute_service")
    service: PlanExecuteService = app.state.plan_execute_service
    # No configured AI corpus DSN means the production gate fails closed.
    assert service is None

    assert hasattr(app.state, "http_client")
    client: httpx.AsyncClient = app.state.http_client
    assert client is not None
    assert not client.is_closed


def test_readiness_returns_200_when_wired() -> None:
    client = TestClient(
        create_app(secret_provider=FakeSecretProvider(), plan_execute_service=_ready_service())
    )
    resp = client.get("/ready")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_readiness_fails_503_when_disabled() -> None:
    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            environ={"ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE": "true"},
        )
    )
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "not_ready"
    assert resp.json()["reason"] == "plan_execute_service_unwired"


def test_readiness_fails_when_rag_is_enabled_without_runtime_dependencies() -> None:
    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            environ={"ONMARU_RAG_ENABLED": "true"},
        )
    )

    resp = client.get("/ready")

    assert resp.status_code == 503
    assert resp.json() == {"status": "not_ready", "reason": "rag_runtime_unwired"}


def test_readiness_rejects_process_local_activation_log_for_rag() -> None:
    class ActiveRevisionRetriever:
        def active_revision_id(self) -> str:
            return "corpus-v1"

        def retrieve(self, corpus_revision_id: str) -> tuple[str, ...]:
            return (corpus_revision_id,)

    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            rag_activation_log=InMemoryRagActivationLog(),
            rag_retriever=ActiveRevisionRetriever(),
            plan_execute_service=_ready_service(),
            environ={"ONMARU_RAG_ENABLED": "true"},
        )
    )

    resp = client.get("/ready")

    assert resp.status_code == 503
    assert resp.json()["reason"] == "rag_runtime_unwired"


def test_readiness_passes_when_rag_is_enabled_with_durable_log_and_retriever() -> None:
    class DurableActiveRetriever:
        def active_revision_id(self) -> str:
            return "corpus-v1"

        def retrieve(self, corpus_revision_id: str) -> tuple[str, ...]:
            return (corpus_revision_id,)

    class DurableTestLog:
        durable = True

        def append(self, decision: object) -> None:
            pass

        def latest_for_revision(self, corpus_revision_id: str) -> object | None:
            return None

    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            rag_activation_log=DurableTestLog(),  # type: ignore[arg-type]
            rag_retriever=DurableActiveRetriever(),
            plan_execute_service=_ready_service(),
            environ={"ONMARU_RAG_ENABLED": "true"},
        )
    )

    resp = client.get("/ready")

    assert resp.status_code == 200
    assert resp.json() == {"status": "ready"}


def test_readiness_fails_503_when_spring_url_invalid() -> None:
    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            environ={"ONMARU_SPRING_BASE_URL": "ftp://not-an-http-url"},
        )
    )
    resp = client.get("/ready")
    assert resp.status_code == 503
    assert resp.json()["status"] == "not_ready"
    assert resp.json()["reason"] == "invalid_spring_base_url"

@pytest.mark.anyio
async def test_composition_root_wires_retrieval_components() -> None:
    provider = FakeSecretProvider()
    client = httpx.AsyncClient()
    try:
        service = create_production_plan_execute_service(
            secret_provider=provider,
            http_client=client,
            environ={"ONMARU_SPRING_BASE_URL": "http://127.0.0.1:8080"},
            corpus_store=object(),
        )
        assert service is not None
        assert service.executor is not None
    finally:
        await client.aclose()


def _ready_service() -> PlanExecuteService:
    async def planner(_request: object) -> object:
        raise AssertionError("readiness does not plan")

    async def executor(_plan: object) -> object:
        raise AssertionError("readiness does not execute")

    from onmaru_ai.contracts.models import Versions

    return PlanExecuteService(
        planner=planner,  # type: ignore[arg-type]
        executor=executor,  # type: ignore[arg-type]
        current_versions=lambda: Versions.model_validate({
            "corpusRevision": "corpus-v1",
            "configHash": "sha256:" + "a" * 64,
            "questionDictionaryVersion": "questions-1",
            "sourceRevocationSequence": 1,
        }),
        verify_grant=lambda _grant_id: None,
    )


def test_create_app_configures_onmaru_ai_stdout_info_logging_and_redaction() -> None:
    import logging
    from io import StringIO

    from onmaru_ai.main import _ApplicationStdoutHandler, configure_application_logging

    app_logger = logging.getLogger("onmaru_ai")
    original_level = app_logger.level
    original_handlers = list(app_logger.handlers)
    stream = StringIO()
    try:
        app_logger.handlers = []
        app_logger.setLevel(logging.NOTSET)
        configure_application_logging(stream=stream)
        create_app(secret_provider=FakeSecretProvider())

        assert app_logger.level == logging.INFO
        stdout_handlers = [
            h for h in app_logger.handlers if isinstance(h, _ApplicationStdoutHandler)
        ]
        assert len(stdout_handlers) == 1

        child_logger = logging.getLogger("onmaru_ai.security.internal_auth")
        child_logger.info(
            "journey.request.accepted request_id=req-1 run_id=run-1 secret=%s",
            FakeSecretProvider().get("gemini.api-key").current,
        )

        output = stream.getvalue()
        assert "INFO [onmaru_ai.security.internal_auth] journey.request.accepted" in output
        assert "<REDACTED>" in output
        assert "fake-gemini-api-key-current" not in output
    finally:
        app_logger.handlers = original_handlers
        app_logger.setLevel(original_level)


def test_create_app_registers_screen_hanok_route_only_when_enabled() -> None:
    disabled_app = create_app(
        secret_provider=FakeSecretProvider(),
        environ={"ONMARU_SCREEN_HANOK_RESEARCH_ENABLED": "false"},
    )
    enabled_app = create_app(
        secret_provider=FakeSecretProvider(),
        environ={"ONMARU_SCREEN_HANOK_RESEARCH_ENABLED": "true"},
    )

    disabled_paths = {getattr(route, "path", "") for route in disabled_app.routes}
    enabled_paths = {getattr(route, "path", "") for route in enabled_app.routes}

    assert "/internal/v1/screen-hanok/research" not in disabled_paths
    assert "/internal/v1/screen-hanok/research" in enabled_paths


def test_spring_grant_binding_requires_opaque_reference_shape_and_approved_plan() -> None:
    fixture = (
        Path(__file__).parent.parent
        / "contracts/fixtures/accepted-approved-sql_plus_retrieval.json"
    )
    plan_payload = json.loads(fixture.read_text(encoding="utf-8"))["payload"]
    plan = ApprovedQueryPlan.model_validate(plan_payload)
    now = datetime.now(UTC)

    bound = bind_spring_grant_reference("qg_" + "A" * 43, plan, now)

    assert bound is not None
    assert bound.run_id == plan.run_id
    assert bound.plan_hash == plan.approved_plan_hash
    assert bind_spring_grant_reference("not-a-spring-grant", plan, now) is None
    assert bind_spring_grant_reference("qg_" + "A" * 43, None, now) is None
