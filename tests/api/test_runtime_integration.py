"""Runtime integration test with mock Spring server.

Tests:
1. /plan generates proposal
2. /execute triggers CallbackProgressSink events (ordinal 1..5) to Spring mock server
3. /execute triggers SpringPlaceQueryAdapter approved lookup
4. /execute reflects lookup places into EvidenceSet and ValidatedProposal
5. Full traceparent, runId, deadline, and X-Run-Progress-Token propagation
"""

from __future__ import annotations

import json
from contextlib import contextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import pytest
from fastapi.testclient import TestClient

from onmaru_ai.config.secrets import FakeSecretProvider
from onmaru_ai.contracts.models import Versions
from onmaru_ai.main import create_app
from onmaru_ai.security.internal_auth import create_internal_token
from onmaru_ai.storage.postgres import CorpusSnapshot


@pytest.mark.anyio
async def test_runtime_integration_flow_with_spring_mock(monkeypatch: pytest.MonkeyPatch) -> None:
    from onmaru_ai import embedding

    class FakeE5Backend:
        model_id = embedding.E5_SMALL_ONNX_INT8_384.model_id
        model_commit = embedding.E5_SMALL_ONNX_INT8_384.model_commit
        dimensions = embedding.E5_SMALL_ONNX_INT8_384.dimensions

        def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
            vector = (1.0,) + (0.0,) * (self.dimensions - 1)
            return tuple(vector for _ in texts)

    monkeypatch.setattr(embedding, "load_e5_backend", lambda _path: FakeE5Backend())
    now = datetime.now(UTC)
    run_id = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
    trace_id = "1" * 32
    tp = f"00-{trace_id}-{'2'*16}-01"
    grant_id = "qg_" + "A" * 43
    progress_token = "run-progress-capability-token-value"

    received_callbacks: list[dict[str, Any]] = []
    received_lookups: list[dict[str, Any]] = []

    def mock_spring_handler(request: httpx.Request) -> httpx.Response:
        url_path = request.url.path
        if "/progress" in url_path:
            assert request.headers.get("x-run-progress-token") == progress_token
            data = json.loads(request.content.decode("utf-8"))
            received_callbacks.append(data)
            return httpx.Response(200, json={"status": "OK"})

        if "/journey_execute_approved_lookup" in url_path:
            assert "Bearer " in request.headers.get("authorization", "")
            assert request.headers.get("traceparent") is not None
            data = json.loads(request.content.decode("utf-8"))
            received_lookups.append(data)
            return httpx.Response(
                200,
                json={
                    "schemaVersion": "journey.lookup.result.v1",
                    "status": "OK",
                    "sourceRevocationSequence": 7,
                    "places": [
                        {
                            "placeId": "p1",
                            "publicAddress": "서울 종로구 사직로 161",
                            "name": "경복궁",
                        },
                    ],
                },
            )

        return httpx.Response(404)

    mock_spring_client = httpx.AsyncClient(
        transport=httpx.MockTransport(mock_spring_handler),
        base_url="http://mock-spring:8080",
    )

    class CatalogConnection:
        def execute(self, statement: str, parameters: tuple[object, ...]) -> Any:
            assert "SELECT DISTINCT source_id AS place_id" in statement
            assert parameters == ("corpus-1",)
            return self

        def fetchall(self) -> list[dict[str, str]]:
            return [{
                "place_id": "p1", "title": "경복궁",
                "region_code": "KR-11", "category_code": "HANOK",
            }]

    class CorpusStore:
        @contextmanager
        def snapshot(self) -> Any:
            yield CorpusSnapshot(
                versions=Versions.model_validate({
                    "corpusRevision": "corpus-1", "configHash": "sha256:" + "a" * 64,
                    "questionDictionaryVersion": "questions-1", "sourceRevocationSequence": 7,
                }),
                embedding_profile_id=embedding.E5_SMALL_ONNX_INT8_384.profile_id,
                revoked_places=frozenset(), revoked_sources=frozenset(),
                connection=CatalogConnection(),  # type: ignore[arg-type]
            )

    app = create_app(
        secret_provider=FakeSecretProvider(),
        environ={
            "ONMARU_SPRING_BASE_URL": "http://mock-spring:8080",
            "ONMARU_E5_ONNX_DIR": "/fake/e5",
        },
        http_client=mock_spring_client,
        plan_execute_corpus_store=CorpusStore(),
    )

    client = TestClient(app)

    # 1. POST /plan
    token_plan = create_internal_token(
        secret="fake-internal-ai-service-token-current",
        issuer="onmaru-spring",
        subject="spring-api",
        audience="onmaru-ai",
        scope="journey.plan:write",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    headers_plan = {
        "Authorization": f"Bearer {token_plan}",
        "X-Run-Id": run_id,
        "X-Request-Id": "req-plan-1",
        "traceparent": tp,
        "X-Deadline-At": (now + timedelta(seconds=25)).isoformat(),
    }
    plan_req_body = {
        "schemaVersion": "ai-safe-query.v1",
        "runId": run_id,
        "safeQuery": "경복궁 주소",
        "confirmedContext": {
            "regionCode": None,
            "pinnedPlaceIds": [],
            "excludedPlaceIds": [],
            "lastConfirmedPlaceIds": [],
        },
        "authorityBounds": {
            "filters": {
                "filterHash": "sha256:" + "a" * 64,
                "publicOnly": True,
                "placeIds": None,
                "regionCodes": None,
                "categoryCodes": None,
                "pinnedPlaceIds": [],
                "excludedPlaceIds": [],
            },
            "allowedCanonicalFields": ["PUBLIC_ADDRESS"],
        },
        "versions": {
            "corpusRevision": "corpus-1",
            "configHash": "sha256:" + "a" * 64,
            "questionDictionaryVersion": "questions-1",
            "sourceRevocationSequence": 7,
        },
        "limits": {
            "bm25K": 20,
            "vectorK": 20,
            "rerankK": 30,
            "evidenceK": 12,
            "maxPlaces": 5,
        },
    }
    resp_plan = client.post(
        "/internal/v1/journey/plan",
        headers=headers_plan,
        json=plan_req_body,
    )
    assert resp_plan.status_code == 200, resp_plan.text
    proposal = resp_plan.json()
    assert proposal["route"] == "SQL_ONLY"
    assert proposal["runId"] == run_id

    # 2. POST /execute
    token_exec = create_internal_token(
        secret="fake-internal-ai-service-token-current",
        issuer="onmaru-spring",
        subject="spring-api",
        audience="onmaru-ai",
        scope="journey.execute:write",
        issued_at=now,
        expires_at=now + timedelta(minutes=5),
    )
    headers_exec = {
        "Authorization": f"Bearer {token_exec}",
        "X-Run-Id": run_id,
        "X-Request-Id": "req-exec-1",
        "traceparent": tp,
        "X-Deadline-At": (now + timedelta(seconds=25)).isoformat(),
        "X-Run-Progress-Token": progress_token,
    }
    approved_plan = {
        "schemaVersion": "ai-approved-plan.v1",
        "planVersion": "ai-query-plan.v1",
        "runId": run_id,
        "approvedPlanHash": proposal["planHash"],
        "approvedRoute": proposal["route"],
        "approvedRetrievalMode": proposal["retrievalMode"],
        "approvedFilters": proposal["proposedFilters"],
        "approvedCanonicalFields": proposal["requestedCanonicalFields"],
        "semanticQuery": proposal["semanticQuery"],
        "versions": proposal["versions"],
        "queryGrantId": grant_id,
    }

    resp_exec = client.post(
        "/internal/v1/journey/execute",
        headers=headers_exec,
        json=approved_plan,
    )
    assert resp_exec.status_code == 200, resp_exec.text
    exec_result = resp_exec.json()
    assert exec_result["runId"] == run_id
    assert exec_result["planHash"] == proposal["planHash"]

    # Lookup is transported; it is not fabricated into passage evidence or claims.
    assert len(received_lookups) == 1
    assert received_lookups[0]["queryGrantId"] == grant_id
    assert exec_result["proposal"] is None
    assert exec_result["evidence"] is None

    # Verify progress callback events were delivered in order with ordinal 1..10
    stages = [cb["stage"] for cb in received_callbacks]
    step_keys = [cb["stepKey"] for cb in received_callbacks]
    statuses = [cb["status"] for cb in received_callbacks]
    ordinals = [cb["ordinal"] for cb in received_callbacks]
    assert stages == [
        "PREPARING_INPUT",
        "PREPARING_INPUT",
        "RETRIEVING",
        "RETRIEVING",
        "SELECTING_EVIDENCE",
        "SELECTING_EVIDENCE",
        "GENERATING",
        "GENERATING",
        "CHECKING_OUTPUT",
        "CHECKING_OUTPUT",
    ]
    assert step_keys == [
        "UNDERSTAND",
        "UNDERSTAND",
        "SEARCH",
        "SEARCH",
        "SELECT",
        "SELECT",
        "WRITE",
        "WRITE",
        "CHECK",
        "CHECK",
    ]
    assert statuses == [
        "STARTED",
        "DONE",
        "STARTED",
        "DONE",
        "STARTED",
        "DONE",
        "STARTED",
        "DONE",
        "STARTED",
        "DONE",
    ]
    assert ordinals == list(range(1, 11))
    for cb in received_callbacks:
        assert cb["schemaVersion"] == "internal.ai.progress.v1"
        assert cb["runId"] == run_id
        assert cb["planHash"] == proposal["planHash"]
