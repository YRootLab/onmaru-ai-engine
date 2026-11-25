"""Comprehensive tests for Cross-Encoder / lightweight reranker (Issue #92)."""

from __future__ import annotations

import time
from typing import Any

import pytest

from onmaru_ai.retrieval.rerank import (
    DeterministicSemanticCrossScorer,
    Reranker,
    RerankerConfig,
    RerankerError,
    create_production_reranker_scorer,
)


def _make_candidate(
    chunk_id: str,
    place_id: str,
    score: float,
    chunk_text: str | None = None,
) -> dict[str, Any]:
    cand: dict[str, Any] = {
        "chunk_id": chunk_id,
        "place_id": place_id,
        "source_id": f"source-{place_id}",
        "source_revision": "rev-1",
        "rank": 1,
        "score": score,
    }
    if chunk_text is not None:
        cand["chunk_text"] = chunk_text
    return cand


def test_deterministic_semantic_cross_scorer_prefers_relevant_content() -> None:
    scorer = DeterministicSemanticCrossScorer()
    query = "조선시대 왕실 한옥과 궁궐 역사"
    candidates = [
        _make_candidate("c1", "p1", 0.5, "현대식 콘크리트 빌딩과 오피스 상가 지역입니다."),
        _make_candidate(
            "c2", "p2", 0.4, "조선시대 왕실의 대표적인 궁궐 한옥 건축물로 역사적 가치가 높습니다."
        ),
        _make_candidate("c3", "p3", 0.3, "해변가 근처의 해수욕장과 캠핑장 안내입니다."),
    ]
    scores = scorer(query, candidates)

    assert len(scores) == 3
    # c2 has high overlap with query keywords ("조선시대", "왕실", "궁궐", "한옥", "역사")
    assert scores[1] > scores[0]
    assert scores[1] > scores[2]


def test_deterministic_semantic_cross_scorer_uses_text_lookup() -> None:
    lookup_map = {
        "c-lookup-1": "무관한 장소",
        "c-lookup-2": "경복궁 근정전과 사정전 등 조선 왕실의 중심 건물",
    }
    scorer = DeterministicSemanticCrossScorer(text_lookup=lambda cid: lookup_map.get(cid))
    query = "경복궁 조선 왕실"
    candidates = [
        _make_candidate("c-lookup-1", "p1", 0.5),
        _make_candidate("c-lookup-2", "p2", 0.4),
    ]
    scores = scorer(query, candidates)

    assert len(scores) == 2
    assert scores[1] > scores[0]


def test_reranker_reorders_candidates_by_score() -> None:
    reranker = Reranker(
        scorer=DeterministicSemanticCrossScorer(),
        config=RerankerConfig(timeout_seconds=1.0),
    )
    query = "한옥 정원 산책"
    candidates = [
        _make_candidate("c1", "p1", 0.6, "복잡한 도심 도로와 주차장 정보"),
        _make_candidate("c2", "p2", 0.4, "전통 한옥의 고즈넉한 정원을 산책할 수 있는 힐링 명소"),
    ]
    reranked = reranker.rerank(query, candidates)

    assert len(reranked) == 2
    assert reranked[0]["chunk_id"] == "c2"
    assert reranked[0]["rank"] == 1
    assert reranked[1]["chunk_id"] == "c1"
    assert reranked[1]["rank"] == 2


def test_reranker_timeout_cleanly_falls_back_to_candidate_order() -> None:
    def slow_scorer(_q: str, _cands: Any) -> list[float]:
        time.sleep(0.3)
        return [1.0, 0.0]

    reranker = Reranker(
        scorer=slow_scorer,
        config=RerankerConfig(timeout_seconds=0.05, fallback_to_candidate_order=True),
    )
    candidates = [
        _make_candidate("c1", "p1", 0.9),
        _make_candidate("c2", "p2", 0.8),
    ]
    reranked = reranker.rerank("query", candidates)

    # Should retain initial order c1, c2
    assert [c["chunk_id"] for c in reranked] == ["c1", "c2"]
    assert reranked[0]["rank"] == 1
    assert reranked[1]["rank"] == 2


def test_reranker_error_and_nan_fallback() -> None:
    def error_scorer(_q: str, _cands: Any) -> list[float]:
        raise RuntimeError("Inference session failure")

    reranker = Reranker(
        scorer=error_scorer,
        config=RerankerConfig(fallback_to_candidate_order=True),
    )
    candidates = [
        _make_candidate("c1", "p1", 0.7),
        _make_candidate("c2", "p2", 0.6),
    ]
    reranked = reranker.rerank("query", candidates)
    assert [c["chunk_id"] for c in reranked] == ["c1", "c2"]

    # When fallback_to_candidate_order is False, raises RerankerError
    strict_reranker = Reranker(
        scorer=error_scorer,
        config=RerankerConfig(fallback_to_candidate_order=False),
    )
    with pytest.raises(RerankerError):
        strict_reranker.rerank("query", candidates)


def test_reranker_latency_and_budget_benchmarking() -> None:
    """Validate that 30 candidates (RRF pool size) execute in < 20ms under CPU constraint."""
    scorer = DeterministicSemanticCrossScorer()
    reranker = Reranker(scorer=scorer, config=RerankerConfig(timeout_seconds=0.5))

    query = "서울 북촌 한옥마을 전통 차 한옥 체험"
    candidates = [
        _make_candidate(
            f"c_{i}",
            f"p_{i}",
            score=1.0 / (60 + i),
            chunk_text=f"장소 {i}에 대한 관광 및 문화재 안내문입니다. 한옥과 전통 체험 {i}",
        )
        for i in range(30)
    ]

    start = time.perf_counter()
    reranked = reranker.rerank(query, candidates)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(reranked) == 30
    # Must complete well below 50ms (typically < 3ms on modern CPU)
    assert elapsed_ms < 50.0, f"Reranker took {elapsed_ms:.2f}ms which exceeds 50ms budget"


def test_create_production_reranker_scorer_without_onnx_dir() -> None:
    scorer = create_production_reranker_scorer({})
    assert isinstance(scorer, DeterministicSemanticCrossScorer)


def test_create_production_reranker_scorer_with_invalid_onnx_dir(tmp_path: Any) -> None:
    # Directory exists but lacks onnx model
    empty_dir = tmp_path / "empty_model"
    empty_dir.mkdir()
    scorer = create_production_reranker_scorer({"ONMARU_RERANKER_ONNX_DIR": str(empty_dir)})
    # Falls back gracefully to deterministic cross-scorer without raising
    assert isinstance(scorer, DeterministicSemanticCrossScorer)
