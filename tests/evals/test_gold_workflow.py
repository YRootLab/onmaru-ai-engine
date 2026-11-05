"""Tests for W22 gold dataset workflow, validation, quotas, and sealing rules."""

from __future__ import annotations

import pytest

from onmaru_ai.evals.gold_workflow import (
    GoldDatasetQuota,
    GoldWorkflowManager,
    SplitLeakageError,
)


def test_quota_validation_200_dev_100_sealed() -> None:
    # Development: 200 items, Sealed: 100 items. Minimum 30 per route across dev, 15 across sealed.
    quota = GoldDatasetQuota(dev_count=200, sealed_count=100)
    assert quota.total_count == 300
    assert quota.dev_count == 200
    assert quota.sealed_count == 100


def test_dual_review_and_adjudication_required() -> None:
    manager = GoldWorkflowManager()
    # A case without two reviews must fail validation
    case_data = {
        "queryId": "q-1",
        "split": "development",
        "goldRoute": "HYBRID",
        "reviews": [{"reviewerId": "r1", "decision": "ACCEPT"}],
        "adjudication": {"status": "PENDING", "decision": "ACCEPT"},
    }
    with pytest.raises(ValueError, match="two distinct independent reviewers"):
        manager.validate_review_integrity(case_data)


def test_source_place_split_leakage_detector() -> None:
    manager = GoldWorkflowManager()
    dev_cases = [
        {"queryId": "q-dev-1", "placeId": "place-A", "sourceId": "src-1", "sourceRevision": "rev-1"}
    ]
    sealed_cases = [
        {
            "queryId": "q-seal-1",
            "placeId": "place-A",
            "sourceId": "src-2",
            "sourceRevision": "rev-1",
        }
    ]
    with pytest.raises(SplitLeakageError, match="Leakage detected for place:place-A"):
        manager.check_split_leakage(dev_cases, sealed_cases)


def test_sealing_procedure_and_dataset_hash() -> None:
    manager = GoldWorkflowManager()
    dataset_content = {
        "schemaVersion": "rag-gold-dataset.v1",
        "datasetVersion": "v1.0",
        "cases": [],
    }
    manifest = manager.seal_dataset(dataset_content, sealed_by="lead_evaluator")
    assert manifest.dataset_hash.startswith("sha256:")
    assert manifest.sealed_by == "lead_evaluator"
    assert manifest.is_sealed is True
