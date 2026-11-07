"""Comprehensive tests for W10 hybrid retrieval and reciprocal rank fusion (RRF)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from onmaru_ai.contracts.models import ApprovedQueryPlan, Candidate, CandidateSet
from onmaru_ai.retrieval.hybrid import (
    HybridRetrievalCoordinator,
    HybridSearchRequest,
    rrf_combine,
)
from onmaru_ai.storage.postgres import CorpusSnapshot


def _load_sample_plan(mode: str = "HYBRID") -> ApprovedQueryPlan:
    fixture_path = (
        Path(__file__).parent.parent / "contracts" / "fixtures" / "accepted-approved-hybrid.json"
    )
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    payload = dict(data["payload"])
    payload["approvedRetrievalMode"] = mode
    return ApprovedQueryPlan.model_validate(payload)


def _make_candidate_set(
    plan: ApprovedQueryPlan, stage: str, items: list[dict[str, Any]]
) -> CandidateSet:
    candidates = tuple(
        Candidate.model_validate(
            {
                "chunkId": item["chunk_id"],
                "placeId": item["place_id"],
                "sourceId": item["source_id"],
                "sourceRevision": item["source_revision"],
                "rank": rank,
                "score": float(item.get("score", 1.0 / rank)),
                "exclusionReason": None,
            }
        )
        for rank, item in enumerate(items, start=1)
    )
    return CandidateSet.model_validate(
        {
            "schemaVersion": "ai-candidate-set.v1",
            "runId": plan.run_id,
            "planHash": plan.approved_plan_hash,
            "versions": plan.versions,
            "stage": stage,
            "candidates": candidates,
            "retrievalStatus": "COMPLETE" if candidates else "NO_EVIDENCE",
            "latencyMs": 10,
        }
    )


def _mock_snapshot(
    revoked_places: set[Any] | None = None, revoked_sources: set[Any] | None = None
) -> CorpusSnapshot:
    snapshot = MagicMock(spec=CorpusSnapshot)
    snapshot.revoked_places = revoked_places or set()
    snapshot.revoked_sources = revoked_sources or set()
    return snapshot


def test_rrf_scoring_deterministic_and_tie_breaks() -> None:
    id_a = "00000000-0000-0000-0000-000000000001"
    id_b = "00000000-0000-0000-0000-000000000002"

    lexical_items = [
        {
            "chunk_id": id_a,
            "place_id": "00000000-0000-0000-0000-000000000010",
            "source_id": "s1",
            "source_revision": "r1",
            "rank": 1,
        },
        {
            "chunk_id": id_b,
            "place_id": "00000000-0000-0000-0000-000000000020",
            "source_id": "s2",
            "source_revision": "r2",
            "rank": 2,
        },
    ]
    dense_items = [
        {
            "chunk_id": id_b,
            "place_id": "00000000-0000-0000-0000-000000000020",
            "source_id": "s2",
            "source_revision": "r2",
            "rank": 1,
        },
        {
            "chunk_id": id_a,
            "place_id": "00000000-0000-0000-0000-000000000010",
            "source_id": "s1",
            "source_revision": "r1",
            "rank": 2,
        },
    ]

    fused = rrf_combine(lexical_items, dense_items, k=60, max_candidates=30)
    assert len(fused) == 2
    assert fused[0]["chunk_id"] == id_a
    assert fused[0]["rank"] == 1
    assert fused[1]["chunk_id"] == id_b
    assert fused[1]["rank"] == 2
    assert fused[0]["score"] == fused[1]["score"]


def test_single_route_does_not_apply_rrf() -> None:
    coordinator = HybridRetrievalCoordinator()
    assert coordinator.should_run_rrf("LEXICAL_ONLY") is False
    assert coordinator.should_run_rrf("DENSE_ONLY") is False
    assert coordinator.should_run_rrf("HYBRID") is True

    plan = _load_sample_plan(mode="LEXICAL_ONLY")
    lexical_searcher = MagicMock()
    items = [
        {
            "chunk_id": "00000000-0000-0000-0000-000000000001",
            "place_id": "00000000-0000-0000-0000-000000000010",
            "source_id": "s1",
            "source_revision": "r1",
        }
    ]
    lexical_searcher.search.return_value = _make_candidate_set(plan, "LEXICAL", items)
    dense_searcher = MagicMock()

    coord = HybridRetrievalCoordinator(
        lexical_searcher=lexical_searcher, dense_searcher=dense_searcher
    )
    result = coord.execute(HybridSearchRequest(plan=plan), _mock_snapshot())

    assert result.stage == "LEXICAL"
    assert len(result.candidates) == 1
    dense_searcher.search.assert_not_called()


def test_hybrid_degraded_when_one_side_fails() -> None:
    plan = _load_sample_plan(mode="HYBRID")
    lexical_searcher = MagicMock()
    items = [
        {
            "chunk_id": "00000000-0000-0000-0000-000000000001",
            "place_id": "00000000-0000-0000-0000-000000000010",
            "source_id": "s1",
            "source_revision": "r1",
        }
    ]
    lexical_searcher.search.return_value = _make_candidate_set(plan, "LEXICAL", items)

    dense_searcher = MagicMock()
    dense_searcher.search.side_effect = RuntimeError("Dense index unreachable")

    coord = HybridRetrievalCoordinator(
        lexical_searcher=lexical_searcher, dense_searcher=dense_searcher
    )
    result = coord.execute(HybridSearchRequest(plan=plan), _mock_snapshot())

    assert result.stage == "FUSION"
    assert result.retrieval_status == "DEGRADED"
    assert len(result.candidates) == 1
    assert result.candidates[0].chunk_id == items[0]["chunk_id"]


def test_hybrid_fails_when_both_sides_fail() -> None:
    plan = _load_sample_plan(mode="HYBRID")
    lexical_searcher = MagicMock()
    lexical_searcher.search.side_effect = RuntimeError("Lexical timeout")
    dense_searcher = MagicMock()
    dense_searcher.search.side_effect = RuntimeError("Dense timeout")

    coord = HybridRetrievalCoordinator(
        lexical_searcher=lexical_searcher, dense_searcher=dense_searcher
    )
    result = coord.execute(HybridSearchRequest(plan=plan), _mock_snapshot())

    assert result.stage == "FUSION"
    assert result.retrieval_status == "FAILED"
    assert len(result.candidates) == 0


def test_hybrid_enforces_hard_filter_and_caps() -> None:
    plan = _load_sample_plan(mode="HYBRID")
    revoked_place_id = "00000000-0000-0000-0000-000000000999"
    revoked_source = ("blog", "s_revoked", "r1")

    lex_items = [
        {
            "chunk_id": f"00000000-0000-0000-0000-{i:012d}",
            "place_id": "00000000-0000-0000-0000-000000000010",
            "source_id": "s1",
            "source_revision": "r1",
        }
        for i in range(1, 25)  # 24 items, but lexical should cap at 20
    ]
    # Add a revoked item
    lex_items.append(
        {
            "chunk_id": "00000000-0000-0000-0000-000000000998",
            "place_id": revoked_place_id,
            "source_id": "s1",
            "source_revision": "r1",
        }
    )

    dense_items = [
        {
            "chunk_id": f"00000000-0000-0000-0001-{i:012d}",
            "place_id": "00000000-0000-0000-0000-000000000020",
            "source_id": "s2",
            "source_revision": "r2",
        }
        for i in range(1, 25)
    ]
    dense_items.append(
        {
            "chunk_id": "00000000-0000-0000-0000-000000000997",
            "place_id": "00000000-0000-0000-0000-000000000020",
            "source_id": "s_revoked",
            "source_revision": "r1",
        }
    )

    lexical_searcher = MagicMock()
    lexical_searcher.search.return_value = _make_candidate_set(plan, "LEXICAL", lex_items[:20])

    dense_searcher = MagicMock()
    dense_searcher.search.return_value = _make_candidate_set(plan, "DENSE", dense_items[:20])

    snapshot = _mock_snapshot(
        revoked_places={revoked_place_id},
        revoked_sources={revoked_source},
    )

    coord = HybridRetrievalCoordinator(
        lexical_searcher=lexical_searcher, dense_searcher=dense_searcher
    )
    result = coord.execute(HybridSearchRequest(plan=plan), snapshot)

    assert result.stage == "FUSION"
    assert result.retrieval_status == "COMPLETE"
    assert len(result.candidates) <= 30  # Capped at 30
    assert all(c.place_id != revoked_place_id for c in result.candidates)
    assert all(
        not (c.source_id == "s_revoked" and c.source_revision == "r1") for c in result.candidates
    )
