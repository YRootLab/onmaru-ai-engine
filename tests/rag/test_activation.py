from __future__ import annotations

import json
import logging
from copy import deepcopy
from pathlib import Path
from typing import Any, cast

from pytest import LogCaptureFixture

from onmaru_ai.evals import EvalReport, compare_reports, evaluate_document
from onmaru_ai.rag.activation import (
    InMemoryRagActivationLog,
    RagActivationPolicy,
    RagActivationThresholds,
    RagRetrievalGate,
)

EVAL_ROOT = Path(__file__).parents[2] / "evals"
FIXTURE_PATH = EVAL_ROOT / "journey-eval-contract-fixture-v1.json"


class CountingRetriever:
    def __init__(self) -> None:
        self.calls = 0

    def retrieve(self) -> tuple[str, ...]:
        self.calls += 1
        return ("evidence:001",)


def fixture_document() -> dict[str, Any]:
    return cast(dict[str, Any], json.loads(FIXTURE_PATH.read_text(encoding="utf-8")))


def failing_rag_report() -> EvalReport:
    document = fixture_document()
    document["corpusRevision"] = "catalog-rev-2026-09-17"
    document["versions"]["model"] = "rag-challenger-v1"
    document["versions"]["ranking"] = "rag-ranking-v1"
    document["cases"][0]["actual"]["retrievedRefs"] = []
    return evaluate_document(document)


def passing_rag_report_with_gain() -> EvalReport:
    baseline_document = fixture_document()
    baseline_document["corpusRevision"] = "catalog-rev-2026-09-17"
    rag_document = deepcopy(baseline_document)
    rag_document["versions"]["model"] = "rag-challenger-v1"
    rag_document["versions"]["ranking"] = "rag-ranking-v1"
    rag_document["cases"][1]["actual"]["retrievedRefs"] = ["place-c", "place-d"]

    baseline = evaluate_document(baseline_document)
    rag_report = evaluate_document(rag_document)
    return rag_report.model_copy(update={"comparison": compare_reports(rag_report, baseline)})


def test_gate_failure_records_revision_pinned_rollback_and_skips_retrieval() -> None:
    log = InMemoryRagActivationLog()
    report = failing_rag_report()

    decision = RagActivationPolicy(log=log).evaluate(
        report,
        corpus_revision_id="catalog-rev-2026-09-17",
    )
    retriever = CountingRetriever()
    result = RagRetrievalGate(log).retrieve_if_active(
        corpus_revision_id="catalog-rev-2026-09-17",
        retrieve=retriever.retrieve,
    )

    assert decision.enabled is False
    assert decision.action == "ROLLBACK"
    assert decision.reason == "EVAL_GATE_FAILED"
    assert decision.corpus_revision_id == "catalog-rev-2026-09-17"
    assert log.records == (decision,)
    assert result == ()
    assert retriever.calls == 0


def test_activation_fails_closed_when_report_corpus_revision_does_not_match() -> None:
    report = failing_rag_report().model_copy(
        update={"corpus_revision": "stale-corpus-revision"}
    )

    decision = RagActivationPolicy().evaluate(
        report, corpus_revision_id="catalog-rev-2026-09-17"
    )

    assert decision.enabled is False
    assert decision.reason == "CORPUS_REVISION_MISMATCH"


def test_activation_fails_closed_for_unrecognized_candidate_policy() -> None:
    report = passing_rag_report_with_gain().model_copy(update={"candidate_policy": "v2"})

    decision = RagActivationPolicy().evaluate(
        report, corpus_revision_id="catalog-rev-2026-09-17"
    )

    assert decision.enabled is False
    assert decision.reason == "CANDIDATE_POLICY_UNSUPPORTED"


def test_activation_requires_compatible_baseline_gain_and_records_corpus_revision() -> None:
    log = InMemoryRagActivationLog()
    report = passing_rag_report_with_gain()

    decision = RagActivationPolicy(
        thresholds=RagActivationThresholds(min_ndcg_at_3_delta=0.05),
        log=log,
    ).evaluate(report, corpus_revision_id="catalog-rev-2026-09-17")
    retriever = CountingRetriever()
    result = RagRetrievalGate(log).retrieve_if_active(
        corpus_revision_id="catalog-rev-2026-09-17",
        retrieve=retriever.retrieve,
    )

    assert report.overall_passed is True
    assert decision.enabled is True
    assert decision.action == "ACTIVATE"
    assert decision.reason == "EVAL_GATE_PASSED_WITH_BASELINE_GAIN"
    assert decision.corpus_revision_id == "catalog-rev-2026-09-17"
    assert decision.dataset_gold_sha256 == report.dataset.gold_sha256
    assert result == ("evidence:001",)
    assert retriever.calls == 1


def test_activation_rejects_baseline_report_that_failed_its_own_gate() -> None:
    baseline_document = fixture_document()
    baseline_document["corpusRevision"] = "catalog-rev-2026-09-17"
    baseline_document["cases"][0]["actual"]["retrievedRefs"] = []
    current_document = deepcopy(baseline_document)
    current_document["versions"]["model"] = "rag-challenger-v1"
    current_document["cases"][0]["actual"]["retrievedRefs"] = ["place-a", "place-b"]
    current_document["cases"][0]["actual"]["outcome"] = "PROPOSE_BOARD"
    current_document["cases"][0]["actual"]["orderedRefs"] = ["place-a"]
    current_document["cases"][0]["actual"]["reasons"] = [
        {
            "ref": "place-a",
            "evidenceIds": ["evidence-a"],
            "summary": "검수된 근거만 사용합니다.",
            "humanClaimSupported": True,
        }
    ]
    baseline = evaluate_document(baseline_document)
    candidate = evaluate_document(current_document)
    report = candidate.model_copy(update={"comparison": compare_reports(candidate, baseline)})

    decision = RagActivationPolicy().evaluate(
        report,
        corpus_revision_id="catalog-rev-2026-09-17",
    )

    assert baseline.overall_passed is False
    assert report.overall_passed is True
    assert decision.enabled is False
    assert decision.reason == "EVAL_GATE_FAILED"
    assert decision.baseline_passed is False
    assert decision.candidate_passed is True


def test_feature_flag_disabled_rolls_back_even_when_eval_passes() -> None:
    log = InMemoryRagActivationLog()
    report = passing_rag_report_with_gain()

    decision = RagActivationPolicy(
        thresholds=RagActivationThresholds(min_ndcg_at_3_delta=0.05),
        feature_enabled=False,
        log=log,
    ).evaluate(report, corpus_revision_id="catalog-rev-2026-09-17")

    assert decision.enabled is False
    assert decision.action == "ROLLBACK"
    assert decision.reason == "FEATURE_FLAG_DISABLED"


def test_activation_decision_logs_safe_revision_pinned_operational_event(
    caplog: LogCaptureFixture,
) -> None:
    log = InMemoryRagActivationLog()
    report = failing_rag_report()

    with caplog.at_level(logging.INFO, logger="onmaru_ai.rag.activation"):
        RagActivationPolicy(log=log).evaluate(
            report,
            corpus_revision_id="catalog-rev-2026-09-17",
        )

    assert "rag.activation.decision" in caplog.text
    assert "action=ROLLBACK" in caplog.text
    assert "reason=EVAL_GATE_FAILED" in caplog.text
    assert "corpus_revision_id=catalog-rev-2026-09-17" in caplog.text
    assert report.dataset.gold_sha256 in caplog.text
    assert "검수된 한옥과 시장 근거를 연결합니다." not in caplog.text
    assert "place-a" not in caplog.text
    assert "evidence-a" not in caplog.text
