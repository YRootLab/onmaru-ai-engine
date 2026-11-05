"""Tests for W11 lightweight reranker and diversity EvidenceSet selector."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

from onmaru_ai.contracts.models import CandidateSet
from onmaru_ai.retrieval.evidence import (
    ChunkSpanLookup,
    EvidenceSelector,
)
from onmaru_ai.retrieval.rerank import (
    rerank_candidates,
)


def _load_sample_candidate_set(stage: str = "FUSION") -> CandidateSet:
    fixture_path = (
        Path(__file__).parent.parent.parent
        / "contracts"
        / "fixtures"
        / "accepted-candidateset.json"
    )
    with open(fixture_path, encoding="utf-8") as f:
        data = json.load(f)
    payload = dict(data["payload"])
    payload["stage"] = stage
    return CandidateSet.model_validate(payload)


def test_reranker_reorders_by_relevance_score() -> None:
    candidates = [
        {
            "chunk_id": "c1",
            "place_id": "p1",
            "source_id": "s1",
            "source_revision": "r1",
            "rank": 1,
            "score": 0.5,
        },
        {
            "chunk_id": "c2",
            "place_id": "p2",
            "source_id": "s2",
            "source_revision": "r2",
            "rank": 2,
            "score": 0.4,
        },
    ]
    # Model scores c2 higher than c1
    scorer = MagicMock(return_value=[0.2, 0.9])
    reranked = rerank_candidates("한옥 추천", candidates, scorer=scorer)

    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
    assert reranked[0]["rank"] == 1
    assert reranked[1]["chunk_id"] == "c1"
    assert reranked[1]["rank"] == 2


def test_reranker_fallback_on_timeout_or_nan() -> None:
    candidates = [
        {
            "chunk_id": "c1",
            "place_id": "p1",
            "source_id": "s1",
            "source_revision": "r1",
            "rank": 1,
            "score": 0.5,
        },
        {
            "chunk_id": "c2",
            "place_id": "p2",
            "source_id": "s2",
            "source_revision": "r2",
            "rank": 2,
            "score": 0.4,
        },
    ]
    # Scorer raises Timeout
    scorer_timeout = MagicMock(side_effect=TimeoutError("Reranker timed out"))
    fallback_res = rerank_candidates(
        "query", candidates, scorer=scorer_timeout, fallback_on_error=True
    )
    # Should deterministically fall back to original candidate order
    assert [c["chunk_id"] for c in fallback_res] == ["c1", "c2"]

    # Scorer returns NaN
    scorer_nan = MagicMock(return_value=[float("nan"), 0.5])
    fallback_nan = rerank_candidates("query", candidates, scorer=scorer_nan, fallback_on_error=True)
    assert [c["chunk_id"] for c in fallback_nan] == ["c1", "c2"]


def test_evidence_selector_enforces_diversity_caps() -> None:
    # Max 2 chunks per place, max 12 total evidence items
    candidates: list[dict[str, Any]] = []
    # 3 places, each with 4 chunks
    for p_idx in (1, 2, 3):
        for c_idx in range(1, 5):
            candidates.append(
                {
                    "chunk_id": f"c_{p_idx}_{c_idx}",
                    "place_id": f"place-{p_idx}",
                    "source_id": f"s-{p_idx}",
                    "source_revision": "r1",
                    "rank": len(candidates) + 1,
                    "score": 1.0 - 0.05 * len(candidates),
                }
            )

    chunk_lookup = MagicMock(spec=ChunkSpanLookup)
    chunk_lookup.get_span.side_effect = lambda cid: (0, 100)

    selector = EvidenceSelector(chunk_lookup=chunk_lookup, max_total=12, max_per_place=2)
    candidate_set = _load_sample_candidate_set()
    evidence_set = selector.select_evidence(candidate_set, candidates)

    assert len(evidence_set.evidence) <= 12
    # Place distribution: place-1 has 2, place-2 has 2, place-3 has 2 (total 6)
    from collections import Counter

    counts = Counter(e.place_id for e in evidence_set.evidence)
    for _p, count in counts.items():
        assert count <= 2
    assert set(evidence_set.allowed_place_ids) == set(counts.keys())
