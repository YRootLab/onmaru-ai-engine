from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Literal
from uuid import UUID

import httpx
from pydantic import BaseModel, ConfigDict, Field

from onmaru_ai.corpus.revocation import RevocationEvent, RevocationScope

CONTRACT_VERSION = "source-revocation.v1"
PAGE_SIZE = 100


class FeedModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True)


class FeedEvent(FeedModel):
    sequence: int = Field(gt=0)
    scope: Literal["PLACE", "SOURCE_REVISION"]
    source_type: str | None = Field(default=None, alias="sourceType")
    source_id: str | None = Field(default=None, alias="sourceId")
    source_revision: str | None = Field(default=None, alias="sourceRevision")
    place_id: UUID | None = Field(default=None, alias="placeId", strict=False)
    revoked_at: datetime = Field(alias="revokedAt", strict=False)
    reason_code: str = Field(min_length=1, alias="reasonCode")

    def to_event(self) -> RevocationEvent:
        scope = RevocationScope(self.scope)
        if scope is RevocationScope.PLACE:
            if self.place_id is None:
                raise ValueError("PLACE event has no placeId")
            return RevocationEvent.place(
                self.sequence, self.place_id, self.reason_code, self.revoked_at
            )
        if not self.source_type or not self.source_id or not self.source_revision:
            raise ValueError("SOURCE_REVISION event is incomplete")
        return RevocationEvent.source_revision(
            self.sequence,
            self.source_type,
            self.source_id,
            self.source_revision,
            self.reason_code,
            self.revoked_at,
        )


class WatermarkResponse(FeedModel):
    contract_version: str = Field(alias="contractVersion")
    watermark: int = Field(ge=0)


class SnapshotResponse(FeedModel):
    contract_version: str = Field(alias="contractVersion")
    snapshot_id: UUID = Field(alias="snapshotId", strict=False)
    watermark: int = Field(ge=0)
    active_revision_id: UUID = Field(alias="activeRevisionId", strict=False)
    public_place_count: int = Field(ge=0, alias="publicPlaceCount")
    history_complete: bool = Field(alias="historyComplete")


class EventPage(FeedModel):
    contract_version: str = Field(alias="contractVersion")
    snapshot_id: UUID | None = Field(default=None, alias="snapshotId", strict=False)
    after_sequence: int = Field(ge=0, alias="afterSequence")
    watermark: int = Field(ge=0)
    events: list[FeedEvent]
    has_more: bool = Field(alias="hasMore")


class PublicPlacePage(FeedModel):
    contract_version: str = Field(alias="contractVersion")
    snapshot_id: UUID = Field(alias="snapshotId", strict=False)
    after_public_id: str | None = Field(default=None, alias="afterPublicId")
    public_place_ids: list[str] = Field(alias="publicPlaceIds")
    has_more: bool = Field(alias="hasMore")


class SpringRevocationFeedClient:
    def __init__(
        self,
        base_url: str,
        token: Callable[[], str],
        client: httpx.AsyncClient,
        *,
        timeout_seconds: float = 2.0,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._token = token
        self._client = client
        self._timeout = timeout_seconds

    async def watermark(self) -> int:
        payload = await self._request("GET", "/watermark")
        response = WatermarkResponse.model_validate(payload)
        self._check_contract(response.contract_version)
        return response.watermark

    async def create_snapshot(self) -> SnapshotResponse:
        payload = await self._request("POST", "/snapshots")
        response = SnapshotResponse.model_validate(payload)
        self._check_contract(response.contract_version)
        return response

    async def events_after(self, after_sequence: int, limit: int = PAGE_SIZE) -> EventPage:
        page = EventPage.model_validate(await self._request(
            "GET", "/events", params={"afterSequence": after_sequence, "limit": limit}
        ))
        self._check_contract(page.contract_version)
        return page

    async def snapshot_events(
        self, snapshot_id: UUID, after_sequence: int, limit: int = PAGE_SIZE
    ) -> EventPage:
        page = EventPage.model_validate(await self._request(
            "GET", f"/snapshots/{snapshot_id}/events",
            params={"afterSequence": after_sequence, "limit": limit},
        ))
        self._check_contract(page.contract_version)
        return page

    async def snapshot_public_places(
        self, snapshot_id: UUID, after_public_id: str | None, limit: int = PAGE_SIZE
    ) -> PublicPlacePage:
        params: dict[str, str | int] = {"limit": limit}
        if after_public_id is not None:
            params["afterPublicId"] = after_public_id
        page = PublicPlacePage.model_validate(await self._request(
            "GET", f"/snapshots/{snapshot_id}/public-places", params=params
        ))
        self._check_contract(page.contract_version)
        return page

    async def _request(
        self, method: str, path: str, *, params: dict[str, str | int] | None = None
    ) -> dict[str, object]:
        response = await self._client.request(
            method,
            self._base_url + "/internal/v1/ai/source-revocations" + path,
            params=params,
            headers={"Authorization": f"Bearer {self._token()}"},
            timeout=self._timeout,
        )
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict):
            raise ValueError("revocation feed response must be an object")
        return payload

    @staticmethod
    def _check_contract(version: str) -> None:
        if version != CONTRACT_VERSION:
            raise ValueError("revocation feed contract version mismatch")
