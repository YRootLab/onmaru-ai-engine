"""Tests for W20 operator-selected investigation, isolated experiments, and promotion gating."""

from __future__ import annotations

import pytest

from onmaru_ai.quality_harness.experiments.models import (
    BudgetExceededError,
    ExperimentBudget,
    ExperimentPromotionGate,
    ExperimentReport,
    ExperimentSpec,
    PromotionRejectedError,
)
from onmaru_ai.quality_harness.experiments.runner import IsolatedExperimentRunner


def test_investigation_requires_explicit_operator_start() -> None:
    runner = IsolatedExperimentRunner()
    # If operator_started=False, runner must refuse to execute
    spec = ExperimentSpec(
        experiment_id="exp-001",
        hypothesis="Increase BM25 b parameter from 0.75 to 0.85",
        target_variable="bm25_b",
        candidate_value=0.85,
        operator_started=False,
    )
    with pytest.raises(PermissionError, match="Operator explicit start required"):
        runner.run(spec)


def test_experiment_modifies_only_one_variable_at_a_time() -> None:
    with pytest.raises(
        ValueError, match="Only one parameter variable may be changed per experiment"
    ):
        ExperimentSpec(
            experiment_id="exp-invalid",
            hypothesis="Change b and k1 together",
            target_variable="bm25_b,bm25_k1",
            candidate_value=0.85,
            operator_started=True,
        )


def test_experiment_budget_limits_cpu_memory_and_time() -> None:
    runner = IsolatedExperimentRunner()
    budget = ExperimentBudget(max_duration_seconds=0.1, max_memory_mb=50)

    spec = ExperimentSpec(
        experiment_id="exp-budget",
        hypothesis="Test timeout budget enforcement",
        target_variable="bm25_b",
        candidate_value=0.85,
        operator_started=True,
        budget=budget,
    )

    def slow_exec() -> None:
        import time

        time.sleep(0.3)

    with pytest.raises(BudgetExceededError, match="Execution time limit exceeded"):
        runner.run_with_fn(spec, slow_exec)


def test_promotion_gate_requires_matching_artifact_hash() -> None:
    gate = ExperimentPromotionGate()
    report = ExperimentReport(
        experiment_id="exp-001",
        approved_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        status="APPROVED",
    )
    # When deployed config hash matches approved_hash, promotion succeeds
    assert (
        gate.can_promote(
            report,
            config_hash="sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
        )
        is True
    )

    # When hash differs, promotion is rejected
    with pytest.raises(PromotionRejectedError, match="Hash mismatch"):
        gate.validate_promotion(
            report,
            config_hash="sha256:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb",
        )
