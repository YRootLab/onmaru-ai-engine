"""Unit tests verifying production composition root in default create_app()."""

from __future__ import annotations

import httpx
import pytest
from fastapi.testclient import TestClient

from onmaru_ai.api.plan_execute import PlanExecuteService
from onmaru_ai.composition import create_production_plan_execute_service
from onmaru_ai.config.secrets import FakeSecretProvider
from onmaru_ai.main import create_app
from onmaru_ai.rag import InMemoryRagActivationLog


def test_default_create_app_wires_production_components() -> None:
    app = create_app(secret_provider=FakeSecretProvider())
    assert hasattr(app.state, "plan_execute_service")
    service: PlanExecuteService = app.state.plan_execute_service
    assert service is not None
    assert callable(service.planner)
    assert callable(service.executor)
    assert callable(service.current_versions)
    assert callable(service.verify_grant)

    assert hasattr(app.state, "http_client")
    client: httpx.AsyncClient = app.state.http_client
    assert client is not None
    assert not client.is_closed


def test_readiness_returns_200_when_wired() -> None:
    client = TestClient(create_app(secret_provider=FakeSecretProvider()))
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
        )
        assert service is not None
        assert service.executor is not None
    finally:
        await client.aclose()
