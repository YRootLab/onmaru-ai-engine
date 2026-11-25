"""Verification tests for 300-case gold evaluation suite (200 Dev + 100 Sealed) (Issue #76)."""

from __future__ import annotations

import json
from pathlib import Path

from jsonschema import Draft202012Validator

from onmaru_ai.evals.runner import evaluate_document

ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = ROOT / "evals" / "input.schema.json"
DEV_PATH = ROOT / "evals" / "journey-eval-gold-dev-200.json"
SEALED_PATH = ROOT / "evals" / "journey-eval-gold-sealed-100.json"


def test_schema_validates_both_dev_and_sealed_datasets() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    validator = Draft202012Validator(schema)

    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    sealed_data = json.loads(SEALED_PATH.read_text(encoding="utf-8"))

    # Both documents must validate cleanly against input.schema.json
    validator.validate(dev_data)
    validator.validate(sealed_data)

    assert len(dev_data["cases"]) == 200, "Development set must contain exactly 200 cases"
    assert len(sealed_data["cases"]) == 100, "Sealed set must contain exactly 100 cases"


def test_zero_leakage_between_dev_and_sealed_splits() -> None:
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    sealed_data = json.loads(SEALED_PATH.read_text(encoding="utf-8"))

    dev_ids = {c["id"] for c in dev_data["cases"]}
    sealed_ids = {c["id"] for c in sealed_data["cases"]}
    assert not (dev_ids & sealed_ids), "Case IDs must not overlap between dev and sealed sets"

    dev_queries = {c["gold"]["query"] for c in dev_data["cases"]}
    sealed_queries = {c["gold"]["query"] for c in sealed_data["cases"]}
    assert not (dev_queries & sealed_queries), (
        "Queries must not overlap between dev and sealed sets"
    )


def test_eval_runner_passes_all_threshold_gates() -> None:
    dev_data = json.loads(DEV_PATH.read_text(encoding="utf-8"))
    sealed_data = json.loads(SEALED_PATH.read_text(encoding="utf-8"))

    dev_report = evaluate_document(dev_data)
    sealed_report = evaluate_document(sealed_data)

    assert dev_report.overall_passed, f"Dev report gates failed: {dev_report.gates}"
    assert sealed_report.overall_passed, f"Sealed report gates failed: {sealed_report.gates}"

    assert dev_report.metrics.retrieval_recall_at_5.value >= 0.8
    assert dev_report.metrics.ndcg_at_3 >= 0.75
    assert dev_report.metrics.claim_support.value >= 0.85
    assert dev_report.metrics.safety.value >= 1.0

    assert sealed_report.metrics.retrieval_recall_at_5.value >= 0.8
    assert sealed_report.metrics.ndcg_at_3 >= 0.75
    assert sealed_report.metrics.claim_support.value >= 0.85
    assert sealed_report.metrics.safety.value >= 1.0
