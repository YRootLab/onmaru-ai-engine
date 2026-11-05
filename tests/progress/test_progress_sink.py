from __future__ import annotations

import asyncio
import json

import httpx
import pytest
from pydantic import ValidationError

from onmaru_ai.progress import (
    CallbackProgressSink,
    DeliveryResult,
    InMemoryProgressSink,
    ProgressStage,
)

RUN_ID = "45e6a7f5-31bc-469d-9e30-6f510a1dc497"
PLAN_HASH = "sha256:" + "a" * 64


def test_memory_sink_emits_only_entered_stages_with_monotonic_ordinals() -> None:
    sink = InMemoryProgressSink(run_id=RUN_ID, plan_hash=PLAN_HASH)

    assert asyncio.run(sink.enter(ProgressStage.PREPARING_INPUT)) == DeliveryResult.DELIVERED
    assert asyncio.run(sink.enter(ProgressStage.GENERATING)) == DeliveryResult.DELIVERED

    assert [(event.ordinal, event.stage) for event in sink.events] == [
        (1, "PREPARING_INPUT"),
        (2, "GENERATING"),
    ]


def test_sink_rejects_invalid_run_or_plan_before_delivery() -> None:
    with pytest.raises(ValidationError):
        InMemoryProgressSink(run_id="member@example.com", plan_hash=PLAN_HASH)
    with pytest.raises(ValidationError):
        InMemoryProgressSink(run_id=RUN_ID, plan_hash="not-a-plan-hash")


def test_callback_retries_the_exact_same_event_and_bears_token_only_in_header() -> None:
    requests: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(503 if len(requests) == 1 else 204)

    async def scenario() -> DeliveryResult:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            sink = CallbackProgressSink(
                run_id=RUN_ID,
                plan_hash=PLAN_HASH,
                receiver_base_url="https://spring.internal",
                bearer_token="short-lived-secret",
                client=client,
                max_attempts=2,
                retry_delay_seconds=0,
            )
            return await sink.enter(ProgressStage.RETRIEVING)

    result = asyncio.run(scenario())

    assert result == DeliveryResult.DELIVERED
    assert len(requests) == 2
    assert requests[0].content == requests[1].content
    assert json.loads(requests[0].content) == {
        "schemaVersion": "ai-progress.v1",
        "runId": RUN_ID,
        "planHash": PLAN_HASH,
        "ordinal": 1,
        "stage": "RETRIEVING",
    }
    assert requests[0].headers["authorization"] == "Bearer short-lived-secret"
    assert b"short-lived-secret" not in requests[0].content
    assert requests[0].url.path == f"/internal/v1/ai/runs/{RUN_ID}/progress"


def test_callback_failure_is_bounded_and_does_not_raise() -> None:
    attempts = 0

    async def handler(request: httpx.Request) -> httpx.Response:
        del request
        nonlocal attempts
        attempts += 1
        raise httpx.ConnectError("unavailable")

    async def scenario() -> str:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            sink = CallbackProgressSink(
                run_id=RUN_ID,
                plan_hash=PLAN_HASH,
                receiver_base_url="https://spring.internal",
                bearer_token="secret",
                client=client,
                max_attempts=3,
                retry_delay_seconds=0,
            )
            assert await sink.enter(ProgressStage.GENERATING) == DeliveryResult.DROPPED
            return "execute-result"

    result = asyncio.run(scenario())

    assert result == "execute-result"
    assert attempts == 3


def test_client_error_is_not_retried_and_next_stage_gets_next_ordinal() -> None:
    bodies: list[dict[str, object]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(json.loads(request.content))
        return httpx.Response(409)

    async def scenario() -> None:
        async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
            sink = CallbackProgressSink(
                run_id=RUN_ID,
                plan_hash=PLAN_HASH,
                receiver_base_url="https://spring.internal",
                bearer_token="secret",
                client=client,
                max_attempts=3,
                retry_delay_seconds=0,
            )
            assert await sink.enter(ProgressStage.SELECTING_EVIDENCE) == DeliveryResult.REJECTED
            assert await sink.enter(ProgressStage.CHECKING_OUTPUT) == DeliveryResult.REJECTED

    asyncio.run(scenario())

    assert [body["ordinal"] for body in bodies] == [1, 2]


def test_timeout_is_applied_to_each_bounded_attempt() -> None:
    observed_timeouts: list[httpx.Timeout] = []

    class CapturingClient:
        async def post(
            self,
            url: str,
            *,
            content: bytes,
            headers: dict[str, str],
            timeout: httpx.Timeout,
        ) -> httpx.Response:
            del url, content, headers
            observed_timeouts.append(timeout)
            return httpx.Response(204)

    sink = CallbackProgressSink(
        run_id=RUN_ID,
        plan_hash=PLAN_HASH,
        receiver_base_url="https://spring.internal",
        bearer_token="secret",
        client=CapturingClient(),
        max_attempts=2,
        attempt_timeout_seconds=0.25,
    )

    assert asyncio.run(sink.enter(ProgressStage.PREPARING_INPUT)) == DeliveryResult.DELIVERED
    assert observed_timeouts[0].connect == 0.25


def test_adapter_enforces_timeout_even_if_client_ignores_timeout_argument() -> None:
    class HangingClient:
        async def post(self, *args: object, **kwargs: object) -> httpx.Response:
            del args, kwargs
            await asyncio.sleep(1)
            return httpx.Response(204)

    sink = CallbackProgressSink(
        run_id=RUN_ID,
        plan_hash=PLAN_HASH,
        receiver_base_url="https://spring.internal",
        bearer_token="secret",
        client=HangingClient(),
        max_attempts=1,
        attempt_timeout_seconds=0.01,
    )

    assert asyncio.run(sink.enter(ProgressStage.GENERATING)) == DeliveryResult.DROPPED


def test_unexpected_adapter_exception_is_contained() -> None:
    class BrokenClient:
        async def post(self, *args: object, **kwargs: object) -> httpx.Response:
            del args, kwargs
            raise RuntimeError("adapter bug")

    sink = CallbackProgressSink(
        run_id=RUN_ID,
        plan_hash=PLAN_HASH,
        receiver_base_url="https://spring.internal",
        bearer_token="secret",
        client=BrokenClient(),
        max_attempts=1,
    )

    assert asyncio.run(sink.enter(ProgressStage.CHECKING_OUTPUT)) == DeliveryResult.DROPPED
