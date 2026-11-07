"""Isolated experiment runner (W20)."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from typing import Any

from onmaru_ai.quality_harness.experiments.models import (
    BudgetExceededError,
    ExperimentReport,
    ExperimentSpec,
)

logger = logging.getLogger(__name__)


class IsolatedExperimentRunner:
    """Executes single-variable experiments in isolation with budget limits."""

    def run(self, spec: ExperimentSpec) -> ExperimentReport:
        if not spec.operator_started:
            raise PermissionError("Operator explicit start required to execute experiment")

        return ExperimentReport(
            experiment_id=spec.experiment_id,
            approved_hash="sha256:dummy",
            status="PENDING",
        )

    def run_with_fn(self, spec: ExperimentSpec, fn: Callable[[], Any]) -> ExperimentReport:
        if not spec.operator_started:
            raise PermissionError("Operator explicit start required to execute experiment")

        start_time = time.monotonic()
        try:
            fn()
        finally:
            elapsed = time.monotonic() - start_time
            if elapsed > spec.budget.max_duration_seconds:
                limit = spec.budget.max_duration_seconds
                raise BudgetExceededError(
                    f"Execution time limit exceeded: {elapsed:.2f}s > {limit}s"
                )

        return ExperimentReport(
            experiment_id=spec.experiment_id,
            approved_hash="sha256:dummy",
            status="PENDING",
        )
