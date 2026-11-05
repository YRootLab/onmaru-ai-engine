"""Isolated experiment models and promotion gating (W20)."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExperimentError(Exception):
    """Base exception for experiment framework."""


class BudgetExceededError(ExperimentError):
    """Raised when an isolated experiment exceeds allocated resources/time."""


class PromotionRejectedError(ExperimentError):
    """Raised when promotion gate rejects config promotion."""


class ExperimentBudget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    max_duration_seconds: float = 30.0
    max_memory_mb: int = 512


class ExperimentSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    experiment_id: str
    hypothesis: str
    target_variable: str
    candidate_value: Any
    operator_started: bool = False
    budget: ExperimentBudget = Field(default_factory=ExperimentBudget)

    @model_validator(mode="after")
    def single_variable_only(self) -> ExperimentSpec:
        if "," in self.target_variable or " " in self.target_variable.strip():
            raise ValueError("Only one parameter variable may be changed per experiment")
        return self


class ExperimentReport(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    experiment_id: str
    approved_hash: str
    status: Literal["PENDING", "APPROVED", "REJECTED"] = "PENDING"


class ExperimentPromotionGate:
    """Enforces strict hash match between approved experiment artifact and deployed config."""

    def can_promote(self, report: ExperimentReport, config_hash: str) -> bool:
        return report.status == "APPROVED" and report.approved_hash == config_hash

    def validate_promotion(self, report: ExperimentReport, config_hash: str) -> None:
        if report.status != "APPROVED":
            raise PromotionRejectedError(f"Report status is not APPROVED: {report.status}")
        if report.approved_hash != config_hash:
            raise PromotionRejectedError(
                f"Hash mismatch: approved {report.approved_hash} != target {config_hash}"
            )
