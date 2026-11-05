"""Grant-only private REST adapter for Spring's fixed PlaceQueryPort lookup."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Callable
from enum import StrEnum
from typing import Annotated, Literal, Self
from urllib.parse import urlsplit

import httpx
from pydantic import Field, ValidationError, model_validator

from onmaru_ai.contracts import ApprovedQueryPlan
from onmaru_ai.contracts.models import CanonicalField, ClosedModel, Identifier

LOOKUP_PATH = "/internal/v1/ai/place-query/lookup"
MAX_RESPONSE_BYTES = 24 * 1024
_TRACEPARENT = re.compile(r"00-([a-f0-9]{32})-([a-f0-9]{16})-([a-f0-9]{2})")
_SQL_ROUTES = frozenset(("SQL_ONLY", "SQL_PLUS_RETRIEVAL"))


class PlaceLookupDisposition(StrEnum):
    """Closed orchestration decisions; no downstream exception text is exposed."""

    COMPLETE = "COMPLETE"
    NOT_ELIGIBLE = "NOT_ELIGIBLE"
    OMIT_CANONICAL = "OMIT_CANONICAL"
    FALLBACK_REQUIRED = "FALLBACK_REQUIRED"


class PlaceLookupRequest(ClosedModel):
    query_grant_id: Identifier


class CanonicalPlaceProjection(ClosedModel):
    place_id: Identifier
    public_address: Annotated[str, Field(min_length=1, max_length=500)] | None = None
    region_code: Identifier | None = None
    category_code: Identifier | None = None
    public_status: Literal["PUBLIC"] | None = None

    def populated_fields(self) -> frozenset[CanonicalField]:
        values: dict[CanonicalField, object | None] = {
            "PUBLIC_ADDRESS": self.public_address,
            "REGION_CODE": self.region_code,
            "CATEGORY_CODE": self.category_code,
            "PUBLIC_STATUS": self.public_status,
        }
        return frozenset(field for field, value in values.items() if value is not None)


class PlaceLookupResponse(ClosedModel):
    schema_version: Literal["journey.lookup.result.v1"]
    status: Literal["OK", "NO_MATCH"]
    plan_hash: str = Field(pattern=r"^sha256:[a-f0-9]{64}$")
    source_revocation_sequence: Annotated[int, Field(ge=0, strict=True)]
    places: Annotated[tuple[CanonicalPlaceProjection, ...], Field(max_length=5)]

    @model_validator(mode="after")
    def unique_places(self) -> Self:
        if len({place.place_id for place in self.places}) != len(self.places):
            raise ValueError("place IDs must be unique")
        if (self.status == "NO_MATCH") != (not self.places):
            raise ValueError("lookup status must agree with places")
        return self


class PlaceLookupOutcome(ClosedModel):
    disposition: PlaceLookupDisposition
    places: tuple[CanonicalPlaceProjection, ...] = ()
    error_code: (
        Literal[
            "ROUTE_NOT_ELIGIBLE",
            "GRANT_MISSING",
            "CORRELATION_INVALID",
            "LOOKUP_ALREADY_ATTEMPTED",
            "SPRING_TIMEOUT",
            "GRANT_REJECTED",
            "SPRING_UNAVAILABLE",
            "INVALID_RESPONSE",
        ]
        | None
    ) = None

    @model_validator(mode="after")
    def consistent_result(self) -> Self:
        if self.disposition == PlaceLookupDisposition.COMPLETE:
            if self.error_code is not None:
                raise ValueError("complete lookup cannot include an error")
        elif self.places:
            raise ValueError("failed lookup cannot retain projections")
        return self


class SpringPlaceQueryAdapter:
    """Single-attempt adapter whose network payload contains only an opaque grant.

    A run is reserved before the first await. Timeouts, invalid responses and
    downstream errors consume that attempt so orchestration cannot retry a lookup
    with ambiguous Spring-side effects.
    """

    def __init__(
        self,
        *,
        base_url: str,
        service_token: Callable[[], str],
        client: httpx.AsyncClient | None = None,
        timeout_seconds: float = 1.5,
    ) -> None:
        parsed = urlsplit(base_url)
        if (
            parsed.scheme != "https"
            or not parsed.netloc
            or parsed.path not in ("", "/")
            or parsed.query
            or parsed.fragment
        ):
            raise ValueError("base_url must be an HTTPS origin")
        if not 0 < timeout_seconds <= 5:
            raise ValueError("timeout_seconds must be in (0, 5]")
        self._url = base_url.rstrip("/") + LOOKUP_PATH
        self._service_token = service_token
        self._client = client or httpx.AsyncClient(follow_redirects=False)
        self._owns_client = client is None
        self._timeout_seconds = timeout_seconds
        self._attempted_runs: set[str] = set()

    async def lookup(
        self,
        plan: ApprovedQueryPlan,
        *,
        traceparent: str,
    ) -> PlaceLookupOutcome:
        if plan.approved_route not in _SQL_ROUTES:
            return self._failure(plan, "ROUTE_NOT_ELIGIBLE", eligible=False)
        if plan.query_grant_id is None:
            return self._failure(plan, "GRANT_MISSING")
        if not self._valid_traceparent(traceparent):
            return self._failure(plan, "CORRELATION_INVALID")
        if plan.run_id in self._attempted_runs:
            return self._failure(plan, "LOOKUP_ALREADY_ATTEMPTED")
        # There is no await between the membership check and reservation.
        self._attempted_runs.add(plan.run_id)

        try:
            token = self._service_token()
        except Exception:
            return self._failure(plan, "SPRING_UNAVAILABLE")
        if not token or "\n" in token or "\r" in token:
            return self._failure(plan, "SPRING_UNAVAILABLE")
        request = PlaceLookupRequest.model_validate({"queryGrantId": plan.query_grant_id})
        try:
            async with asyncio.timeout(self._timeout_seconds):
                response = await self._client.post(
                    self._url,
                    content=request.model_dump_json(by_alias=True),
                    headers={
                        "Authorization": f"Bearer {token}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                        "Cache-Control": "no-store",
                        "traceparent": traceparent,
                    },
                    timeout=httpx.Timeout(self._timeout_seconds),
                )
        except (TimeoutError, httpx.TimeoutException):
            return self._failure(plan, "SPRING_TIMEOUT")
        except httpx.HTTPError:
            return self._failure(plan, "SPRING_UNAVAILABLE")

        if response.status_code in (401, 403, 409, 410):
            return self._failure(plan, "GRANT_REJECTED")
        if response.status_code != 200:
            return self._failure(plan, "SPRING_UNAVAILABLE")
        if len(response.content) > MAX_RESPONSE_BYTES:
            return self._failure(plan, "INVALID_RESPONSE")
        try:
            parsed_response = PlaceLookupResponse.model_validate_json(response.content)
        except (ValidationError, ValueError):
            return self._failure(plan, "INVALID_RESPONSE")
        approved_fields = frozenset(plan.approved_canonical_fields)
        if (
            parsed_response.plan_hash != plan.approved_plan_hash
            or parsed_response.source_revocation_sequence
            != plan.versions.source_revocation_sequence
            or any(
                not place.populated_fields() <= approved_fields
                for place in parsed_response.places
            )
        ):
            return self._failure(plan, "INVALID_RESPONSE")
        return PlaceLookupOutcome.model_validate(
            {
                "disposition": PlaceLookupDisposition.COMPLETE,
                "places": parsed_response.places,
            }
        )

    async def aclose(self) -> None:
        """Close only the internally-created HTTP client."""

        if self._owns_client:
            await self._client.aclose()

    @staticmethod
    def _valid_traceparent(value: str) -> bool:
        match = _TRACEPARENT.fullmatch(value)
        return bool(match and int(match[1], 16) != 0 and int(match[2], 16) != 0)

    @staticmethod
    def _failure(
        plan: ApprovedQueryPlan,
        error_code: Literal[
            "ROUTE_NOT_ELIGIBLE",
            "GRANT_MISSING",
            "CORRELATION_INVALID",
            "LOOKUP_ALREADY_ATTEMPTED",
            "SPRING_TIMEOUT",
            "GRANT_REJECTED",
            "SPRING_UNAVAILABLE",
            "INVALID_RESPONSE",
        ],
        *,
        eligible: bool = True,
    ) -> PlaceLookupOutcome:
        if not eligible:
            disposition = PlaceLookupDisposition.NOT_ELIGIBLE
        elif plan.approved_route == "SQL_PLUS_RETRIEVAL":
            disposition = PlaceLookupDisposition.OMIT_CANONICAL
        else:
            disposition = PlaceLookupDisposition.FALLBACK_REQUIRED
        return PlaceLookupOutcome.model_validate(
            {"disposition": disposition, "errorCode": error_code}
        )
