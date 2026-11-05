"""Privacy-safe progress events for the private Spring callback boundary."""

from __future__ import annotations

import asyncio
from enum import StrEnum
from typing import Protocol

import httpx

from onmaru_ai.contracts import ProgressEvent


class ProgressStage(StrEnum):
    """Major stages that an execution route may explicitly enter."""

    PREPARING_INPUT = "PREPARING_INPUT"
    RETRIEVING = "RETRIEVING"
    SELECTING_EVIDENCE = "SELECTING_EVIDENCE"
    GENERATING = "GENERATING"
    CHECKING_OUTPUT = "CHECKING_OUTPUT"


class DeliveryResult(StrEnum):
    """Local delivery outcome; it is never part of the callback payload."""

    DELIVERED = "DELIVERED"
    REJECTED = "REJECTED"
    DROPPED = "DROPPED"


class ProgressSink(Protocol):
    async def enter(self, stage: ProgressStage) -> DeliveryResult:
        """Report a stage after the route has actually entered it."""


class ProgressHttpClient(Protocol):
    async def post(
        self,
        url: str,
        *,
        content: bytes,
        headers: dict[str, str],
        timeout: httpx.Timeout,
    ) -> httpx.Response: ...


class _OrderedProgressSink:
    def __init__(self, *, run_id: str, plan_hash: str) -> None:
        # Validate correlation metadata before any network or execution work.
        ProgressEvent.model_validate(
            {
                "schemaVersion": "ai-progress.v1",
                "runId": run_id,
                "planHash": plan_hash,
                "ordinal": 1,
                "stage": ProgressStage.PREPARING_INPUT,
            }
        )
        self._run_id = run_id
        self._plan_hash = plan_hash
        self._ordinal = 0
        # Serial delivery keeps entry order deterministic under concurrent callers.
        self._lock = asyncio.Lock()

    def _next_event(self, stage: ProgressStage) -> ProgressEvent:
        self._ordinal += 1
        return ProgressEvent.model_validate(
            {
                "schemaVersion": "ai-progress.v1",
                "runId": self._run_id,
                "planHash": self._plan_hash,
                "ordinal": self._ordinal,
                "stage": stage,
            }
        )


class InMemoryProgressSink(_OrderedProgressSink):
    """Deterministic fake for route and orchestration tests."""

    def __init__(self, *, run_id: str, plan_hash: str) -> None:
        super().__init__(run_id=run_id, plan_hash=plan_hash)
        self.events: list[ProgressEvent] = []

    async def enter(self, stage: ProgressStage) -> DeliveryResult:
        async with self._lock:
            self.events.append(self._next_event(stage))
        return DeliveryResult.DELIVERED


class CallbackProgressSink(_OrderedProgressSink):
    """Bounded best-effort adapter to Spring's private progress receiver.

    Every retry reuses the same serialized event. Delivery errors are converted
    to a local outcome so they cannot replace or reopen the execute result.
    """

    def __init__(
        self,
        *,
        run_id: str,
        plan_hash: str,
        receiver_base_url: str,
        bearer_token: str,
        client: ProgressHttpClient,
        max_attempts: int = 2,
        attempt_timeout_seconds: float = 1.0,
        retry_delay_seconds: float = 0.05,
    ) -> None:
        super().__init__(run_id=run_id, plan_hash=plan_hash)
        base = httpx.URL(receiver_base_url)
        if (
            base.scheme != "https"
            or not base.host
            or base.userinfo
            or base.query
            or base.fragment
        ):
            raise ValueError("receiver_base_url must be a plain HTTPS service URL")
        if not bearer_token or "\n" in bearer_token or "\r" in bearer_token:
            raise ValueError("bearer_token must be a nonempty header value")
        if not 1 <= max_attempts <= 3:
            raise ValueError("max_attempts must be between 1 and 3")
        if not 0 < attempt_timeout_seconds <= 2:
            raise ValueError("attempt_timeout_seconds must be in (0, 2]")
        if not 0 <= retry_delay_seconds <= 0.5:
            raise ValueError("retry_delay_seconds must be in [0, 0.5]")

        self._url = (
            f"{str(base).rstrip('/')}/internal/v1/ai/runs/{run_id}/progress"
        )
        self._headers = {
            "Authorization": f"Bearer {bearer_token}",
            "Content-Type": "application/json",
        }
        self._client = client
        self._max_attempts = max_attempts
        self._timeout = httpx.Timeout(attempt_timeout_seconds)
        self._retry_delay_seconds = retry_delay_seconds

    async def enter(self, stage: ProgressStage) -> DeliveryResult:
        async with self._lock:
            event = self._next_event(stage)
            payload = event.model_dump_json(by_alias=True).encode()
            for attempt in range(self._max_attempts):
                try:
                    async with asyncio.timeout(self._timeout.connect):
                        response = await self._client.post(
                            self._url,
                            content=payload,
                            headers=self._headers,
                            timeout=self._timeout,
                        )
                except Exception:  # callback failure must remain outside execute semantics
                    if attempt + 1 == self._max_attempts:
                        return DeliveryResult.DROPPED
                else:
                    if 200 <= response.status_code < 300:
                        return DeliveryResult.DELIVERED
                    if response.status_code != 429 and response.status_code < 500:
                        return DeliveryResult.REJECTED
                    if attempt + 1 == self._max_attempts:
                        return DeliveryResult.DROPPED
                if self._retry_delay_seconds:
                    await asyncio.sleep(self._retry_delay_seconds)
        return DeliveryResult.DROPPED


__all__ = [
    "CallbackProgressSink",
    "DeliveryResult",
    "InMemoryProgressSink",
    "ProgressSink",
    "ProgressStage",
]
