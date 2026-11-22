import asyncio
from datetime import UTC, datetime

import httpx
import pytest

from onmaru_ai.corpus.revocation_feed import (
    EventPage,
    SpringRevocationFeedClient,
)
from onmaru_ai.corpus.revocation_poller import SourceRevocationPoller


@pytest.mark.anyio
async def test_feed_client_parses_ordered_events_and_uses_service_bearer() -> None:
    seen: list[httpx.Request] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(
            200,
            json={
                "contractVersion": "source-revocation.v1",
                "snapshotId": None,
                "afterSequence": 3,
                "watermark": 4,
                "events": [
                    {
                        "sequence": 4,
                        "scope": "SOURCE_REVISION",
                        "sourceType": "TOUR_API",
                        "sourceId": "p-tourapi-123",
                        "sourceRevision": "dataset-revision-uuid",
                        "placeId": None,
                        "revokedAt": "2026-11-23T00:00:00Z",
                        "reasonCode": "NOT_IN_NEW_ACTIVE_REVISION",
                    }
                ],
                "hasMore": False,
            },
        )

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    feed = SpringRevocationFeedClient(
        "http://spring-api:8080", lambda: "test-service-token", client
    )
    try:
        page = await feed.events_after(3)
    finally:
        await client.aclose()

    assert page == EventPage.model_validate(page.model_dump(by_alias=True))
    assert page.events[0].to_event().source_id == "p-tourapi-123"
    assert page.events[0].revoked_at == datetime(2026, 11, 23, tzinfo=UTC)
    assert seen[0].headers["Authorization"] == "Bearer test-service-token"
    assert seen[0].url.params["afterSequence"] == "3"


def test_event_parser_rejects_wrong_scope_identity_and_contract_version() -> None:
    page = EventPage.model_validate(
        {
            "contractVersion": "source-revocation.v1",
            "snapshotId": None,
            "afterSequence": 0,
            "watermark": 1,
            "events": [{"sequence": 1, "scope": "PLACE", "reasonCode": "PRIVATE",
                        "revokedAt": "2026-11-23T00:00:00Z"}],
            "hasMore": False,
        }
    )
    with pytest.raises(ValueError, match="placeId"):
        page.events[0].to_event()


@pytest.mark.anyio
async def test_poller_survives_database_failure_while_marking_unhealthy() -> None:
    class BrokenLedger:
        def state(self) -> object:
            raise RuntimeError("database unavailable")

        def mark_unhealthy(self) -> None:
            raise RuntimeError("database unavailable")

    class NeverReachedFeed:
        async def watermark(self) -> int:
            raise AssertionError("polling must stop after ledger state fails")

    class StopAfterOneWait(asyncio.Event):
        async def wait(self) -> bool:
            self.set()
            return True

    poller = SourceRevocationPoller(BrokenLedger(), NeverReachedFeed())  # type: ignore[arg-type]
    await poller.run(StopAfterOneWait())
