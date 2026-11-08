"""Fail-closed, two-step private API. No default planner or execution authority."""

from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from onmaru_ai.config.secrets import SecretProvider
from onmaru_ai.contracts import (
    ApprovedQueryPlan,
    ContractViolation,
    EvidenceSet,
    PlanProposal,
    SafeQueryRequest,
    ValidatedProposal,
    Versions,
    validate_artifact,
    validate_plan,
)
from onmaru_ai.contracts.models import ClosedModel, RunArtifact
from onmaru_ai.security.internal_auth import validate_internal_token
from onmaru_ai.security.plan_validator import (
    PlanBinding,
    QueryGrant,
    valid_grant,
    validate_execution,
)


class ExecutionResult(RunArtifact):
    schema_version: Literal["ai-execute-result.v1"]
    proposal: ValidatedProposal | None
    evidence: EvidenceSet | None


class BoundaryError(Exception):
    def __init__(self, code: str, status: int = 409) -> None:
        self.code = code
        self.status = status
        super().__init__(code)


class ErrorResponse(ClosedModel):
    schema_version: Literal["ai-boundary-error.v1"] = "ai-boundary-error.v1"
    code: str


@dataclass(frozen=True)
class TransportContext:
    trace_id: str
    deadline: datetime
    progress_token: str | None = None


def transport_context(request: Request, run_id: str, now: datetime) -> TransportContext:
    if request.headers.get("x-run-id") != run_id:
        raise BoundaryError("RUN_MISMATCH", 422)
    trace = re.fullmatch(
        r"00-([a-f0-9]{32})-([a-f0-9]{16})-([a-f0-9]{2})", request.headers.get("traceparent", "")
    )
    request_id = request.headers.get("x-request-id", "")
    if (
        trace is None
        or int(trace[1], 16) == 0
        or int(trace[2], 16) == 0
        or re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._:-]{0,127}", request_id) is None
    ):
        raise BoundaryError("CORRELATION_INVALID", 422)
    try:
        deadline = datetime.fromisoformat(request.headers.get("x-deadline-at", ""))
        if deadline.tzinfo is None:
            raise ValueError
    except ValueError:
        raise BoundaryError("DEADLINE_INVALID", 422) from None
    if deadline <= now:
        raise BoundaryError("DEADLINE_EXCEEDED", 504)
    progress_token = request.headers.get("x-run-progress-token")
    return TransportContext(
        trace[1],
        min(deadline, now + timedelta(seconds=30)),
        progress_token=progress_token,
    )


class PlanExecuteService:
    """Single-process gate with bounded metadata and no query-text storage.

    Run reservations are not evicted: capacity exhaustion fails closed. The
    execution owner must provide durable cross-process deduplication in W13.
    Process loss means an execute cannot find its plan and cannot regenerate it.
    """

    def __init__(
        self,
        *,
        planner: Callable[[SafeQueryRequest], Awaitable[PlanProposal]],
        executor: (
            Callable[[ApprovedQueryPlan], Awaitable[ExecutionResult]]
            | Callable[[ApprovedQueryPlan, TransportContext], Awaitable[ExecutionResult]]
        ),
        current_versions: Callable[[], Versions],
        verify_grant: Callable[[str], QueryGrant | None],
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
        capacity: int = 10000,
    ) -> None:
        self.planner = planner
        self.executor = executor
        self.current_versions = current_versions
        self.verify_grant = verify_grant
        self.now = now
        self.capacity = capacity
        self._plans: dict[str, PlanBinding | None] = {}

    def remaining(self, deadline: datetime) -> float:
        remaining = (deadline - self.now()).total_seconds()
        if remaining <= 0:
            raise BoundaryError("DEADLINE_EXCEEDED", 504)
        return remaining

    async def plan(self, body: SafeQueryRequest, context: TransportContext) -> PlanProposal:
        if body.run_id in self._plans:
            raise BoundaryError("RUN_ALREADY_PLANNED")
        if len(self._plans) >= self.capacity:
            raise BoundaryError("PLAN_CAPACITY_EXCEEDED", 503)
        if body.versions != self.current_versions():
            raise ContractViolation("VERSION_MISMATCH")
        # Reserve before awaiting; duplicate/concurrent requests cannot replan this run.
        self._plans[body.run_id] = None
        async with asyncio.timeout(self.remaining(context.deadline)):
            proposal = await self.planner(body)
        proposal = PlanProposal.model_validate(proposal.model_dump(by_alias=True))
        self.remaining(context.deadline)
        validate_plan(body, proposal, current_versions=self.current_versions())
        self._plans[body.run_id] = PlanBinding.from_plan(
            proposal,
            context.trace_id,
            context.deadline,
        )
        return proposal

    async def execute(
        self,
        body: ApprovedQueryPlan,
        context: TransportContext,
    ) -> ExecutionResult:
        binding = self._plans.get(body.run_id)
        if binding is None:
            code = "RUN_ALREADY_EXECUTED" if body.run_id in self._plans else "PLAN_NOT_FOUND"
            raise BoundaryError(code)
        if binding.expires_at <= self.now():
            self._plans[body.run_id] = None
            raise BoundaryError("PLAN_NOT_FOUND")
        if context.trace_id != binding.trace_id:
            raise BoundaryError("CORRELATION_MISMATCH", 422)
        validate_execution(binding, body, self.current_versions())
        if body.approved_route == "CLARIFY_OR_SCOPE":
            raise BoundaryError("PLAN_NOT_EXECUTABLE", 422)
        if body.query_grant_id is not None:
            try:
                grant_obj = self.verify_grant(body.query_grant_id, body)  # type: ignore[call-arg]
            except TypeError:
                grant_obj = self.verify_grant(body.query_grant_id)
            if not valid_grant(grant_obj, body, self.now()):
                raise BoundaryError("GRANT_INVALID", 403)
        validate_execution(binding, body, self.current_versions())
        deadline = min(context.deadline, binding.expires_at)
        remaining = self.remaining(deadline)
        # No await between validation and consumption. Failure/timeout never reopens the run.
        self._plans[body.run_id] = None
        async with asyncio.timeout(remaining):
            try:
                result = await self.executor(body, context)  # type: ignore[call-arg]
            except TypeError:
                result = await self.executor(body)  # type: ignore[call-arg]
        self.remaining(deadline)
        result = ExecutionResult.model_validate(result.model_dump(by_alias=True))
        if result.run_id != body.run_id:
            raise ContractViolation("RUN_MISMATCH")
        if result.plan_hash != body.approved_plan_hash:
            raise ContractViolation("PLAN_HASH_MISMATCH")
        current = self.current_versions()
        if result.versions != current or result.versions != body.versions:
            raise ContractViolation("VERSION_MISMATCH")
        if result.evidence is not None:
            validate_artifact(result.evidence, body, current_versions=current)
        if result.proposal is not None:
            validate_artifact(
                result.proposal, body, current_versions=current, evidence_set=result.evidence
            )
        return result


def install_plan_execute(
    app: FastAPI,
    secret_provider: SecretProvider,
    service: PlanExecuteService | None,
) -> None:
    async def dispatch(request: Request, operation: Literal["plan", "execute"]) -> JSONResponse:
        try:
            validate_internal_token(
                request.headers.get("authorization", ""),
                secret_provider,
                required_scope=f"journey.{operation}:write",
            )
            model = SafeQueryRequest if operation == "plan" else ApprovedQueryPlan
            body = model.model_validate(await request.json())
            context = transport_context(
                request, body.run_id, service.now() if service else datetime.now(UTC)
            )
            if service is None:
                raise BoundaryError("AI_SERVICE_UNAVAILABLE", 503)
            if isinstance(body, SafeQueryRequest):
                result: PlanProposal | ExecutionResult = await service.plan(body, context)
            else:
                result = await service.execute(body, context)
            return JSONResponse(
                content=result.model_dump(mode="json", by_alias=True),
                headers={"Cache-Control": "no-store"},
            )
        except HTTPException as error:
            detail = error.detail
            code = str(detail["code"]) if isinstance(detail, dict) else "INTERNAL_AUTH_INVALID"
            return error_response(code, error.status_code)
        except ContractViolation as error:
            return error_response(error.code, 409)
        except BoundaryError as error:
            return error_response(error.code, error.status)
        except (ValidationError, ValueError):
            return error_response("INVALID_PAYLOAD", 422)
        except TimeoutError:
            return error_response("DEADLINE_EXCEEDED", 504)
        except Exception:
            return error_response("AI_SERVICE_UNAVAILABLE", 503)

    @app.post("/internal/v1/journey/plan", response_model=PlanProposal)
    async def plan(request: Request) -> JSONResponse:
        return await dispatch(request, "plan")

    @app.post("/internal/v1/journey/execute", response_model=ExecutionResult)
    async def execute(request: Request) -> JSONResponse:
        return await dispatch(request, "execute")


def error_response(code: str, status: int) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=ErrorResponse(code=code).model_dump(by_alias=True),
        headers={"Cache-Control": "no-store"},
    )
