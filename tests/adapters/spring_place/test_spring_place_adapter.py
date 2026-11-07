from __future__ import annotations

import asyncio
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

import httpx
import pytest

from onmaru_ai.adapters.spring_place import (
    PlaceLookupDisposition,
    SpringPlaceQueryAdapter,
)
from onmaru_ai.contracts import ApprovedQueryPlan

FIXTURES = Path(__file__).parents[2] / "contracts" / "fixtures"
TRACEPARENT = "00-" + "1" * 32 + "-" + "2" * 16 + "-01"


def approved(route: str = "sql_plus_retrieval") -> ApprovedQueryPlan:
    raw = json.loads((FIXTURES / f"accepted-approved-{route}.json").read_text())
    return ApprovedQueryPlan.model_validate(raw["payload"])


def response_for(plan: ApprovedQueryPlan) -> dict[str, Any]:
    projection: dict[str, object] = {"placeId": "place-1"}
    values = {
        "PUBLIC_ADDRESS": ("publicAddress", "서울 종로구"),
        "REGION_CODE": ("regionCode", "KR-11"),
        "CATEGORY_CODE": ("categoryCode", "HANOK"),
        "PUBLIC_STATUS": ("publicStatus", "PUBLIC"),
    }
    for field in plan.approved_canonical_fields:
        key, value = values[field]
        projection[key] = value
    return {
        "schemaVersion": "journey.lookup.result.v1",
        "status": "OK",
        "planHash": plan.approved_plan_hash,
        "sourceRevocationSequence": plan.versions.source_revocation_sequence,
        "places": [projection],
    }


def adapter(
    handler: Any,
    *,
    timeout_seconds: float = 0.05,
) -> SpringPlaceQueryAdapter:
    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    return SpringPlaceQueryAdapter(
        base_url="https://spring.internal",
        service_token=lambda: "service-secret",
        client=client,
        timeout_seconds=timeout_seconds,
    )


def test_sql_routes_send_only_opaque_grant_and_transport_metadata_once() -> None:
    requests: list[httpx.Request] = []
    plan = approved()

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=response_for(plan))

    async def scenario() -> None:
        client = adapter(handler)
        result = await client.lookup(plan, traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.COMPLETE
        assert result.places[0].public_address == "서울 종로구"
        repeated = await client.lookup(plan, traceparent=TRACEPARENT)
        assert repeated.disposition is PlaceLookupDisposition.OMIT_CANONICAL
        assert repeated.error_code == "LOOKUP_ALREADY_ATTEMPTED"
        await client.aclose()

    asyncio.run(scenario())
    assert len(requests) == 1
    request = requests[0]
    assert request.url == "https://spring.internal/internal/mcp/journey/tools/journey_execute_approved_lookup"
    assert json.loads(request.content) == {
        "queryGrantId": plan.query_grant_id,
        "regionCode": "SEOUL",
        "category": "HANOK",
        "limit": 5,
    }
    assert request.headers["authorization"] == "Bearer service-secret"
    assert request.headers["traceparent"] == TRACEPARENT
    forbidden = ("sql", "filter", "member", "semantic", "question")
    body_keys = {key.lower() for key in json.loads(request.content)}
    assert all(not any(word in key for word in forbidden) for key in body_keys - {"querygrantid"})


@pytest.mark.parametrize("route", ["lexical_only", "dense_only", "hybrid"])
def test_non_sql_routes_are_rejected_without_network(route: str) -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        return httpx.Response(500)

    async def scenario() -> None:
        client = adapter(handler)
        result = await client.lookup(approved(route), traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.NOT_ELIGIBLE
        assert result.error_code == "ROUTE_NOT_ELIGIBLE"
        await client.aclose()

    asyncio.run(scenario())
    assert calls == 0


def test_timeout_is_bounded_consumes_attempt_and_classifies_route_fallback() -> None:
    calls = 0
    plan = approved("sql_only")

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.sleep(1)
        return httpx.Response(200, json=response_for(plan))

    async def scenario() -> None:
        client = adapter(handler, timeout_seconds=0.01)
        result = await client.lookup(plan, traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.FALLBACK_REQUIRED
        assert result.error_code == "SPRING_TIMEOUT"
        again = await client.lookup(plan, traceparent=TRACEPARENT)
        assert again.error_code == "LOOKUP_ALREADY_ATTEMPTED"
        await client.aclose()

    asyncio.run(scenario())
    assert calls == 1


@pytest.mark.parametrize("status", [401, 403, 409, 410, 429, 500, 503])
def test_spring_errors_are_typed_and_sql_plus_retrieval_omits_canonical_claims(
    status: int,
) -> None:
    async def scenario() -> None:
        client = adapter(lambda request: httpx.Response(status, json={"secret": "not exposed"}))
        result = await client.lookup(approved(), traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.OMIT_CANONICAL
        expected = "GRANT_REJECTED" if status in (401, 403, 409, 410) else "SPRING_UNAVAILABLE"
        assert result.error_code == expected
        assert "secret" not in repr(result)
        await client.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "mutation",
    [
        lambda body: body.update(extra="leak"),
        lambda body: body.update(schemaVersion="journey.lookup.result.v2"),
        lambda body: body.update(places=[{"placeId": "place-1", "memberId": "member-1"}]),
        lambda body: body.update(
            places=[
                {
                    "placeId": "place-1",
                    "publicAddress": "서울 종로구",
                    "regionCode": "KR-11",
                }
            ]
        ),
        lambda body: body.update(places=[{"placeId": "place-1"}] * 6),
        lambda body: body.update(planHash="sha256:" + "b" * 64),
        lambda body: body.update(sourceRevocationSequence=8),
        lambda body: body.update(status="NO_MATCH"),
    ],
)
def test_response_is_closed_bounded_and_matches_approved_projection(mutation: Any) -> None:
    plan = approved()
    body = deepcopy(response_for(plan))
    mutation(body)

    async def scenario() -> None:
        client = adapter(lambda request: httpx.Response(200, json=body))
        result = await client.lookup(plan, traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.OMIT_CANONICAL
        assert result.error_code == "INVALID_RESPONSE"
        assert result.places == ()
        await client.aclose()

    asyncio.run(scenario())


def test_concurrent_calls_reserve_before_await_and_make_one_network_call() -> None:
    calls = 0
    plan = approved()

    async def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        await asyncio.sleep(0)
        return httpx.Response(200, json=response_for(plan))

    async def scenario() -> None:
        client = adapter(handler)
        first, second = await asyncio.gather(
            client.lookup(plan, traceparent=TRACEPARENT),
            client.lookup(plan, traceparent=TRACEPARENT),
        )
        assert {first.error_code, second.error_code} == {None, "LOOKUP_ALREADY_ATTEMPTED"}
        await client.aclose()

    asyncio.run(scenario())
    assert calls == 1


def test_approved_projection_may_be_reduced_by_current_public_state() -> None:
    plan = approved()
    body = response_for(plan)
    body["places"] = [{"placeId": "place-1"}]

    async def scenario() -> None:
        client = adapter(lambda request: httpx.Response(200, json=body))
        result = await client.lookup(plan, traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.COMPLETE
        assert result.places[0].public_address is None
        await client.aclose()

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "response",
    [
        httpx.Response(200, content=b"not-json"),
        httpx.Response(200, content=b" " * (24 * 1024 + 1)),
    ],
)
def test_malformed_or_oversized_response_fails_closed(response: httpx.Response) -> None:
    async def scenario() -> None:
        client = adapter(lambda request: response)
        result = await client.lookup(approved(), traceparent=TRACEPARENT)
        assert result.disposition is PlaceLookupDisposition.OMIT_CANONICAL
        assert result.error_code == "INVALID_RESPONSE"
        await client.aclose()

    asyncio.run(scenario())


def test_network_failure_is_sanitized_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("private host details", request=request)

    async def scenario() -> None:
        client = adapter(handler)
        result = await client.lookup(approved(), traceparent=TRACEPARENT)
        assert result.error_code == "SPRING_UNAVAILABLE"
        assert "private host" not in repr(result)
        await client.aclose()

    asyncio.run(scenario())
    assert calls == 1
