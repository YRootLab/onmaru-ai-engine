from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from contextlib import suppress
from datetime import UTC, datetime
from typing import Any, Protocol
from uuid import UUID

from onmaru_ai.corpus.revocation import RevocationLedger
from onmaru_ai.corpus.revocation_feed import (
    EventPage,
    FeedEvent,
    PublicPlacePage,
    SnapshotResponse,
    SpringRevocationFeedClient,
)

logger = logging.getLogger(__name__)
POLL_INTERVAL_SECONDS = 10.0


class RevocationFeed(Protocol):
    async def watermark(self) -> int: ...
    async def create_snapshot(self) -> SnapshotResponse: ...
    async def snapshot_events(self, snapshot_id: UUID, after_sequence: int) -> EventPage: ...
    async def snapshot_public_places(
        self, snapshot_id: UUID, after_public_id: str | None
    ) -> PublicPlacePage: ...
    async def events_after(self, after_sequence: int) -> EventPage: ...


class SourceRevocationPoller:
    def __init__(
        self,
        ledger: RevocationLedger,
        feed: SpringRevocationFeedClient | RevocationFeed,
        *,
        clock: Callable[[], datetime] = lambda: datetime.now(UTC),
        run_sync: Callable[..., Awaitable[Any]] = asyncio.to_thread,
    ) -> None:
        self._ledger = ledger
        self._feed = feed
        self._clock = clock
        self._run_sync = run_sync

    async def ready(self) -> bool:
        try:
            state = await self._run_sync(self._ledger.state)
            age = (
                (self._clock() - state.heartbeat_at).total_seconds()
                if state.heartbeat_at else None
            )
            return (
                state.source_snapshot_watermark is not None
                and age is not None
                and 0 <= age <= 60
            )
        except Exception:
            return False

    async def run(self, stop: asyncio.Event) -> None:
        while not stop.is_set():
            try:
                await self.poll_once()
            except asyncio.CancelledError:
                raise
            except Exception as error:
                try:
                    await self._run_sync(self._ledger.mark_unhealthy)
                except Exception as health_error:
                    # Keep the poller alive when the database is unavailable; readiness
                    # remains closed because its persisted heartbeat cannot be refreshed.
                    logger.error(
                        "Could not mark source revocation state unhealthy (%s)",
                        type(health_error).__name__,
                    )
                logger.warning(
                    "Source revocation poll failed; readiness remains closed (%s)",
                    type(error).__name__,
                )
            with suppress(TimeoutError):
                await asyncio.wait_for(stop.wait(), timeout=POLL_INTERVAL_SECONDS)

    async def poll_once(self) -> None:
        state = await self._run_sync(self._ledger.state)
        watermark = await self._feed.watermark()
        if state.source_snapshot_watermark is None or state.sequence > watermark:
            await self._bootstrap()
        await self._catch_up()

    async def _bootstrap(self) -> None:
        await self._run_sync(self._ledger.mark_unhealthy)
        snapshot = await self._feed.create_snapshot()
        if not snapshot.history_complete:
            raise RuntimeError("source revocation snapshot history is incomplete")
        await self._run_sync(
            self._ledger.begin_snapshot,
            snapshot.snapshot_id,
            snapshot.watermark,
            snapshot.active_revision_id,
            snapshot.public_place_count,
        )

        cursor = 0
        while True:
            page = await self._feed.snapshot_events(snapshot.snapshot_id, cursor)
            self._validate_page(page, snapshot.snapshot_id, cursor, snapshot.watermark)
            self._validate_contiguous(tuple(page.events), cursor, page.watermark, page.has_more)
            events = tuple(event.to_event() for event in page.events)
            await self._run_sync(
                self._ledger.stage_snapshot_events,
                snapshot.snapshot_id,
                watermark=snapshot.watermark,
                after_sequence=cursor,
                events=events,
                has_more=page.has_more,
            )
            cursor = events[-1].sequence if events else cursor
            if not page.has_more:
                break

        place_cursor: str | None = None
        place_count = 0
        while True:
            place_page = await self._feed.snapshot_public_places(
                snapshot.snapshot_id, place_cursor
            )
            if (
                place_page.contract_version != "source-revocation.v1"
                or place_page.snapshot_id != snapshot.snapshot_id
                or place_page.after_public_id != place_cursor
            ):
                raise RuntimeError("source revocation public-place snapshot mismatch")
            ids = tuple(place_page.public_place_ids)
            if tuple(sorted(set(ids))) != ids or any(
                not item or (place_cursor is not None and item <= place_cursor) for item in ids
            ):
                raise RuntimeError("source revocation public-place page is invalid")
            await self._run_sync(
                self._ledger.stage_snapshot_places,
                snapshot.snapshot_id,
                after_public_id=place_cursor,
                public_place_ids=ids,
                has_more=place_page.has_more,
            )
            place_count += len(ids)
            if not place_page.has_more:
                break
            if not ids:
                raise RuntimeError("source revocation public-place page is incomplete")
            place_cursor = ids[-1]
        if place_count != snapshot.public_place_count:
            raise RuntimeError("source revocation public-place count mismatch")
        await self._run_sync(
            self._ledger.install_snapshot, snapshot.snapshot_id, heartbeat_at=self._clock()
        )

    async def _catch_up(self) -> None:
        state = await self._run_sync(self._ledger.state)
        cursor = state.sequence
        while True:
            page = await self._feed.events_after(cursor)
            if (page.contract_version != "source-revocation.v1"
                    or page.snapshot_id is not None or page.after_sequence != cursor
                    or page.watermark < cursor):
                raise RuntimeError("source revocation event page mismatch")
            self._validate_contiguous(tuple(page.events), cursor, page.watermark, page.has_more)
            events = tuple(event.to_event() for event in page.events)
            if events:
                cursor = events[-1].sequence
                await self._run_sync(
                    self._ledger.apply,
                    events,
                    heartbeat_sequence=cursor,
                    heartbeat_at=None,
                )
            if cursor < page.watermark:
                if not page.has_more:
                    raise RuntimeError("source revocation event feed has a gap")
                continue
            if page.has_more:
                raise RuntimeError("source revocation page reports inconsistent continuation")
            latest = await self._feed.watermark()
            if latest < cursor:
                await self._bootstrap()
                cursor = (await self._run_sync(self._ledger.state)).sequence
                continue
            if latest > cursor:
                continue
            await self._run_sync(self._ledger.heartbeat, cursor, self._clock())
            return

    @staticmethod
    def _validate_page(page: EventPage, snapshot_id: UUID, cursor: int, watermark: int) -> None:
        if (page.contract_version != "source-revocation.v1" or page.snapshot_id != snapshot_id
                or page.after_sequence != cursor or page.watermark != watermark):
            raise RuntimeError("source revocation snapshot event page mismatch")
        SourceRevocationPoller._validate_contiguous(
            tuple(page.events), cursor, watermark, page.has_more
        )

    @staticmethod
    def _validate_contiguous(
        events: tuple[FeedEvent, ...],
        cursor: int,
        watermark: int,
        has_more: bool,
    ) -> None:
        sequences = tuple(event.sequence for event in events)
        if sequences != tuple(range(cursor + 1, cursor + 1 + len(sequences))):
            raise RuntimeError("source revocation sequence is not contiguous")
        end = sequences[-1] if sequences else cursor
        if end > watermark or (has_more and end >= watermark):
            raise RuntimeError("source revocation page cursor is invalid")
        if not has_more and end != watermark:
            raise RuntimeError("source revocation feed did not reach its watermark")
