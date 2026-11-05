from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
from typing import Any

from onmaru_ai.evals.rag import evaluate_rag_replay

ROOT = Path(__file__).resolve().parents[3]
GOLD = ROOT / "tests/evals/rag_gold/fixtures/valid-development.json"


def replay() -> dict[str, Any]:
    return {
        "schemaVersion": "rag-replay.v1",
        "corpusRevision": "synthetic-corpus-1",
        "configHash": "sha256:" + "c" * 64,
        "dataset": json.loads(GOLD.read_text()),
        "runs": [
            {
                "queryId": "synthetic-q1",
                "actualRoute": "HYBRID",
                "stages": {
                    "BM25": ["chunk-x", "chunk-1"],
                    "VECTOR": ["chunk-1"],
                    "RRF": ["chunk-1"],
                    "RERANK": ["chunk-1"],
                    "EVIDENCE": ["chunk-1"],
                },
                "selectedPlaceIds": ["place-1"],
                "claims": [{"claimId": "claim-1", "decision": "SUPPORTED"}],
            }
        ],
    }


def test_reports_stage_metrics_route_claims_and_deterministic_hash() -> None:
    first = evaluate_rag_replay(replay())
    second = evaluate_rag_replay(replay())

    assert first.report_hash == second.report_hash
    assert first.route_confusion == {"HYBRID->HYBRID": 1}
    assert first.stages[0].stage == "BM25"
    assert first.stages[0].recall_at_k.value == 1.0
    assert first.stages[0].mrr.value == 0.5
    assert first.stages[-1].ndcg_at_k.value == 1.0
    assert first.place_recall_at_5.value == 1.0
    assert first.place_ndcg_at_5.value == 1.0
    assert first.claims.supported == 1
    assert first.claims.held == 0
    assert first.first_gold_loss == {}
    assert first.promotion_eligible is False  # development data never promotes


def test_first_loss_and_any_hard_violation_block_gate() -> None:
    value = replay()
    run = value["runs"][0]
    run["stages"]["RERANK"] = []
    run["stages"]["EVIDENCE"] = []
    run["selectedPlaceIds"] = ["place-9"]
    report = evaluate_rag_replay(value)

    assert report.first_gold_loss == {"RERANK": 1}
    assert report.hard_violations == 1
    assert report.gates["safety"] is False
    assert report.overall_passed is False


def test_hash_changes_with_results_but_not_mapping_order() -> None:
    original = replay()
    reordered = deepcopy(original)
    reordered["runs"][0]["stages"] = dict(
        reversed(list(reordered["runs"][0]["stages"].items()))
    )
    changed = deepcopy(original)
    changed["runs"][0]["actualRoute"] = "DENSE_ONLY"

    assert evaluate_rag_replay(original).report_hash == evaluate_rag_replay(reordered).report_hash
    assert evaluate_rag_replay(original).report_hash != evaluate_rag_replay(changed).report_hash


def test_missing_or_duplicate_run_fails_closed() -> None:
    value = replay()
    value["runs"] = []
    try:
        evaluate_rag_replay(value)
    except ValueError as error:
        assert "run" in str(error).lower()
    else:
        raise AssertionError("missing run accepted")

    value = replay()
    value["runs"].append(deepcopy(value["runs"][0]))
    try:
        evaluate_rag_replay(value)
    except ValueError as error:
        assert "run" in str(error).lower()
    else:
        raise AssertionError("duplicate run accepted")


def test_self_reported_support_for_unknown_claim_is_a_safety_violation() -> None:
    value = replay()
    value["runs"][0]["claims"] = [{"claimId": "invented", "decision": "SUPPORTED"}]

    report = evaluate_rag_replay(value)

    assert report.claims.supported == 0
    assert report.claims.held == 1
    assert report.hard_violations == 1
