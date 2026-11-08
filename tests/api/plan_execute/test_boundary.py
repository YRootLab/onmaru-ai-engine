from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from onmaru_ai.config.secrets import FakeSecretProvider
from onmaru_ai.contracts import ApprovedQueryPlan, PlanProposal, SafeQueryRequest, Versions
from onmaru_ai.main import create_app
from onmaru_ai.security.internal_auth import create_internal_token

FIXTURES = Path(__file__).parents[2] / "contracts" / "fixtures"
NOW = datetime.now(UTC)
TRACE = "00-" + "1" * 32 + "-" + "2" * 16 + "-01"


def fixture(route: str = "sql_plus_retrieval") -> dict[str, Any]:
    return json.loads((FIXTURES / f"accepted-approved-{route}.json").read_text())  # type: ignore[no-any-return]


def headers(scope: str = "journey.plan:write", **updates: str) -> dict[str, str]:
    result = {
        "Authorization": "Bearer "
        + create_internal_token(
            secret="fake-internal-ai-service-token-current",
            issuer="onmaru-spring",
            subject="spring-api",
            audience="onmaru-ai",
            scope=scope,
            issued_at=NOW,
            expires_at=NOW + timedelta(minutes=5),
        ),
        "X-Run-Id": fixture()["payload"]["runId"],
        "X-Request-Id": "request-1",
        "traceparent": TRACE,
        "X-Deadline-At": (NOW + timedelta(seconds=20)).isoformat(),
    }
    result.update(updates)
    return result


@pytest.mark.parametrize(
    "path,scope", [("plan", "journey.plan:write"), ("execute", "journey.execute:write")]
)
def test_private_routes_require_service_auth_before_body_validation(path: str, scope: str) -> None:
    client = TestClient(create_app(secret_provider=FakeSecretProvider()))
    response = client.post(f"/internal/v1/journey/{path}", json={})
    assert response.status_code == 401
    response = client.post(f"/internal/v1/journey/{path}", headers=headers("wrong"), json={})
    assert response.status_code == 403
    assert response.json()["code"] == "INTERNAL_AUTH_FORBIDDEN_SCOPE"


class Harness:
    def __init__(self, route: str = "sql_plus_retrieval") -> None:
        from onmaru_ai.api.plan_execute import PlanExecuteService
        from onmaru_ai.security.plan_validator import QueryGrant

        self.data = fixture(route)
        self.clock = NOW
        self.versions = Versions.model_validate(self.data["context"]["currentVersions"])
        self.plans = 0
        self.effects: list[ApprovedQueryPlan] = []
        self.delay = False
        self.fail = False
        self.grant = QueryGrant(
            grant_id="grant-1",
            run_id=self.data["payload"]["runId"],
            plan_hash=self.data["payload"]["approvedPlanHash"],
            filter_hash=self.data["payload"]["approvedFilters"]["filterHash"],
            versions=self.versions,
            issued_at=NOW,
            expires_at=NOW + timedelta(seconds=30),
        )
        self.service = PlanExecuteService(
            planner=self.plan,
            executor=self.execute,
            current_versions=lambda: self.versions,
            verify_grant=lambda grant_id: self.grant if grant_id == "grant-1" else None,
            now=lambda: self.clock,
        )
        self.client = TestClient(
            create_app(
                secret_provider=FakeSecretProvider(),
                plan_execute_service=self.service,
            )
        )

    async def plan(self, request: SafeQueryRequest) -> PlanProposal:
        self.plans += 1
        return PlanProposal.model_validate(self.data["context"]["proposal"])

    async def execute(self, approved: ApprovedQueryPlan) -> Any:
        from onmaru_ai.api.plan_execute import ExecutionResult

        self.effects.append(approved)
        if self.delay:
            await asyncio.sleep(1)
        if self.fail:
            raise RuntimeError("secret semantic query")
        return ExecutionResult.model_validate(
            {
                "schemaVersion": "ai-execute-result.v1",
                "runId": approved.run_id,
                "planHash": approved.approved_plan_hash,
                "versions": approved.versions.model_dump(by_alias=True),
                "proposal": None,
                "evidence": None,
            }
        )

    def post_plan(self, **header_updates: str) -> Any:
        return self.client.post(
            "/internal/v1/journey/plan",
            headers=headers(**header_updates),
            json=self.data["context"]["request"],
        )

    def post_execute(self, payload: Any = None, **header_updates: str) -> Any:
        return self.client.post(
            "/internal/v1/journey/execute",
            headers=headers("journey.execute:write", **header_updates),
            json=self.data["payload"] if payload is None else payload,
        )


@pytest.mark.parametrize(
    "route", ["sql_only", "lexical_only", "dense_only", "hybrid", "sql_plus_retrieval"]
)
def test_w0_fixture_round_trip_executes_exact_approval_once(route: str) -> None:
    h = Harness(route)
    response = h.post_plan()
    assert response.status_code == 200
    assert response.json() == h.data["context"]["proposal"]
    assert response.headers["cache-control"] == "no-store"
    assert h.effects == []
    executed = h.post_execute()
    assert executed.status_code == 200
    assert executed.json()["planHash"] == h.data["payload"]["approvedPlanHash"]
    assert h.effects == [ApprovedQueryPlan.model_validate(h.data["payload"])]
    assert h.post_execute().status_code == 409
    assert len(h.effects) == 1


def test_unplanned_execute_has_zero_executor_side_effects() -> None:
    h = Harness()
    assert h.post_execute().json()["code"] == "PLAN_NOT_FOUND"
    assert h.effects == []


@pytest.mark.parametrize(
    "field,value,code",
    [
        ("approvedPlanHash", "sha256:" + "b" * 64, "PLAN_HASH_MISMATCH"),
        ("approvedRoute", "SQL_ONLY", "INVALID_PLAN"),
        ("approvedRetrievalMode", "LEXICAL_ONLY", "INVALID_PLAN"),
        ("semanticQuery", "changed", "INVALID_PLAN"),
        ("approvedCanonicalFields", ["REGION_CODE"], "INVALID_PLAN"),
        ("queryGrantId", None, "INVALID_PAYLOAD"),
        ("queryGrantId", "grant-other", "GRANT_INVALID"),
        ("schemaVersion", "ai-approved-plan.v2", "INVALID_PAYLOAD"),
        ("planVersion", "ai-query-plan.v2", "INVALID_PAYLOAD"),
    ],
)
def test_approval_mismatch_blocks_execution(field: str, value: Any, code: str) -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    payload = deepcopy(h.data["payload"])
    payload[field] = value
    response = h.post_execute(payload)
    assert response.status_code in (409, 422, 403)
    assert response.json()["code"] == code
    assert h.effects == []


@pytest.mark.parametrize(
    "field,value",
    [
        ("corpusRevision", "corpus-other"),
        ("configHash", "sha256:" + "b" * 64),
        ("questionDictionaryVersion", "questions-2"),
        ("sourceRevocationSequence", 8),
    ],
)
def test_current_runtime_version_change_blocks_execution(field: str, value: Any) -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    current = h.versions.model_dump(by_alias=True)
    current[field] = value
    h.versions = Versions.model_validate(current)
    assert h.post_execute().json()["code"] == "VERSION_MISMATCH"
    assert h.effects == []


@pytest.mark.parametrize(
    "field,value", [("filterHash", "sha256:" + "b" * 64), ("placeIds", ["place-1"])]
)
def test_approval_filters_must_echo_exact_plan(field: str, value: Any) -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    payload = deepcopy(h.data["payload"])
    payload["approvedFilters"][field] = value
    assert h.post_execute(payload).json()["code"] == "FILTER_MISMATCH"
    assert h.effects == []


@pytest.mark.parametrize(
    "header,value,code",
    [
        ("X-Run-Id", "other-run", "RUN_MISMATCH"),
        ("traceparent", "invalid", "CORRELATION_INVALID"),
        ("traceparent", "00-" + "1" * 32 + "-" + "0" * 16 + "-01", "CORRELATION_INVALID"),
        ("X-Request-Id", "", "CORRELATION_INVALID"),
        ("X-Deadline-At", "invalid", "DEADLINE_INVALID"),
        ("X-Deadline-At", NOW.isoformat(), "DEADLINE_EXCEEDED"),
    ],
)
def test_plan_transport_rejection_has_no_planner_or_executor_effects(
    header: str,
    value: str,
    code: str,
) -> None:
    h = Harness()
    assert h.post_plan(**{header: value}).json()["code"] == code
    assert h.plans == 0
    assert h.effects == []


def test_changed_trace_on_execute_is_rejected() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    changed_trace = "00-" + "3" * 32 + "-" + "2" * 16 + "-01"
    assert h.post_execute(traceparent=changed_trace).json()["code"] == "CORRELATION_MISMATCH"
    assert h.effects == []


def test_expired_plan_cannot_be_revived_with_new_deadline() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    h.clock += timedelta(seconds=31)
    assert (
        h.post_execute(**{"X-Deadline-At": (h.clock + timedelta(seconds=20)).isoformat()}).json()[
            "code"
        ]
        == "PLAN_NOT_FOUND"
    )
    assert h.effects == []


def test_executor_failure_is_sanitized_and_never_retried() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    h.fail = True
    response = h.post_execute()
    assert response.status_code == 503
    assert "secret semantic" not in response.text
    assert h.post_execute().status_code == 409
    assert len(h.effects) == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("grant_id", "other"),
        ("run_id", "other"),
        ("plan_hash", "sha256:" + "b" * 64),
        ("filter_hash", "sha256:" + "b" * 64),
        ("expires_at", NOW),
        ("issued_at", NOW + timedelta(seconds=1)),
        ("expires_at", NOW + timedelta(seconds=31)),
        ("expires_at", NOW.replace(tzinfo=None)),
    ],
)
def test_grant_reference_requires_trusted_matching_short_lived_binding(
    field: str,
    value: Any,
) -> None:
    from dataclasses import replace

    h = Harness()
    assert h.post_plan().status_code == 200
    h.grant = replace(h.grant, **{field: value})
    assert h.post_execute().json()["code"] == "GRANT_INVALID"
    assert h.effects == []


def test_revision_change_during_grant_verification_blocks_executor() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200

    def verify(grant_id: str) -> Any:
        h.versions = h.versions.model_copy(update={"source_revocation_sequence": 8})
        return h.grant

    h.service.verify_grant = verify
    assert h.post_execute().json()["code"] == "VERSION_MISMATCH"
    assert h.effects == []


def test_deadline_cancels_inflight_execute_without_retry() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    h.delay = True
    response = h.post_execute(**{"X-Deadline-At": (NOW + timedelta(milliseconds=10)).isoformat()})
    assert response.status_code == 504
    assert response.json()["code"] == "DEADLINE_EXCEEDED"
    assert h.post_execute().status_code == 409
    assert len(h.effects) == 1


def test_duplicate_planning_does_not_generate_new_strategy() -> None:
    h = Harness()
    assert h.post_plan().status_code == 200
    assert h.post_plan().json()["code"] == "RUN_ALREADY_PLANNED"
    assert h.plans == 1
    assert h.post_execute().status_code == 200
    assert h.post_plan().status_code == 409
    assert h.plans == 1


def test_capacity_fails_closed_without_evicting_prior_run() -> None:
    h = Harness()
    h.service.capacity = 0
    assert h.post_plan().json()["code"] == "PLAN_CAPACITY_EXCEEDED"
    assert h.plans == 0


def test_clarification_never_enters_executor() -> None:
    h = Harness()
    data = json.loads((FIXTURES / "accepted-plan-clarify_or_scope.json").read_text())
    h.data["context"]["proposal"] = data["payload"]
    assert h.post_plan().status_code == 200
    approval = h.data["payload"]
    approval.update(
        approvedPlanHash=data["payload"]["planHash"],
        approvedRoute="CLARIFY_OR_SCOPE",
        approvedRetrievalMode="NONE",
        approvedCanonicalFields=[],
        semanticQuery=None,
        queryGrantId=None,
    )
    assert h.post_execute().json()["code"] == "PLAN_NOT_EXECUTABLE"
    assert h.effects == []


def test_default_service_is_unavailable_and_does_not_synthesize_plans() -> None:
    client = TestClient(
        create_app(
            secret_provider=FakeSecretProvider(),
            environ={"ONMARU_DISABLE_DEFAULT_PLAN_EXECUTE": "true"},
        )
    )
    response = client.post(
        "/internal/v1/journey/plan", headers=headers(), json=fixture()["context"]["request"]
    )
    assert response.status_code == 503
    assert response.json()["code"] == "AI_SERVICE_UNAVAILABLE"


def test_payload_error_does_not_echo_sensitive_fields() -> None:
    h = Harness()
    response = h.post_execute({"safeQuery": "secret user text"})
    assert response.status_code == 422
    assert "secret user text" not in response.text
    assert h.effects == []


def test_concurrent_execute_only_dispatches_once() -> None:
    from httpx import ASGITransport, AsyncClient

    h = Harness()
    assert h.post_plan().status_code == 200
    h.delay = True

    async def run() -> list[int]:
        async with AsyncClient(
            transport=ASGITransport(h.client.app), base_url="http://test"
        ) as client:
            results = await asyncio.gather(
                *[
                    client.post(
                        "/internal/v1/journey/execute",
                        headers=headers("journey.execute:write"),
                        json=h.data["payload"],
                    )
                    for _ in range(2)
                ]
            )
        return sorted(response.status_code for response in results)

    assert asyncio.run(run()) == [200, 409]
    assert len(h.effects) == 1


@pytest.mark.parametrize(
    "field,value",
    [("runId", "e9665d58-83fe-45f7-b76d-757ef58127de"), ("planHash", "sha256:" + "b" * 64)],
)
def test_executor_result_cannot_cross_run_or_plan(field: str, value: str) -> None:
    from onmaru_ai.api.plan_execute import ExecutionResult

    h = Harness()
    assert h.post_plan().status_code == 200

    async def execute(approved: ApprovedQueryPlan) -> ExecutionResult:
        result = await h.execute(approved)
        payload = result.model_dump(by_alias=True)
        payload[field] = value
        return ExecutionResult.model_validate(payload)

    h.service.executor = execute
    assert h.post_execute().status_code == 409
    assert h.post_execute().status_code == 409
    assert len(h.effects) == 1


@pytest.mark.parametrize(
    "operation,scope",
    [
        ("plan", "journey.execute:write"),
        ("execute", "journey.plan:write"),
        ("execute", "journey.proposal:write"),
    ],
)
def test_other_operation_scope_cannot_authorize_request(operation: str, scope: str) -> None:
    h = Harness()
    response = h.client.post(f"/internal/v1/journey/{operation}", headers=headers(scope), json={})
    assert response.status_code == 403
    assert h.plans == 0
    assert h.effects == []
