from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import psycopg
import pytest

from onmaru_ai.rag.activation import RagActivationDecision
from onmaru_ai.rag.postgres_activation import (
    PostgresRagActivationLog,
    PostgresRagEvidenceRetriever,
)


def test_postgres_rag_activation_log_contract() -> None:
    assert PostgresRagActivationLog.durable is True
    log = PostgresRagActivationLog("postgresql://user:pass@localhost:5432/test")
    assert log.durable is True


def test_postgres_rag_evidence_retriever_handles_db_errors_safely() -> None:
    retriever = PostgresRagEvidenceRetriever("postgresql://invalid-user:pass@127.0.0.1:59999/test")
    # Should safely catch exception and return None / () instead of raising
    assert retriever.active_revision_id() is None
    assert retriever.retrieve("test-rev") == ()


def test_postgres_rag_activation_log_handles_db_errors_safely() -> None:
    log = PostgresRagActivationLog("postgresql://invalid-user:pass@127.0.0.1:59999/test")
    decision = RagActivationDecision(
        enabled=True,
        action="ACTIVATE",
        reason="EVAL_GATE_PASSED_WITH_BASELINE_GAIN",
        candidate_policy="v1",
        corpus_revision_id="catalog-rev-1",
        image_digest="sha256:" + "1" * 64,
        embedding_profile="e5-small-384",
        dataset_input_sha256="input-hash",
        dataset_gold_sha256="gold-hash",
        evaluated_at=datetime.now(UTC),
        metric_deltas={"retrievalRecallAt5": 0.1},
        baseline_passed=True,
        candidate_passed=True,
    )
    with pytest.raises(psycopg.Error):
        log.append(decision)


def test_postgres_rag_activation_log_parse_row_and_retrieval() -> None:
    log = PostgresRagActivationLog("postgresql://fake")
    now = datetime(2026, 11, 13, 0, 0, 0, tzinfo=UTC)

    mock_row = {
        "corpus_revision_id": "catalog-rev-1",
        "candidate_policy": "v1",
        "image_digest": "sha256:" + "1" * 64,
        "embedding_profile": "e5-small-384",
        "dataset_input_sha256": "input-sha",
        "dataset_gold_sha256": "gold-sha",
        "enabled": True,
        "action": "ACTIVATE",
        "reason": "EVAL_GATE_PASSED_WITH_BASELINE_GAIN",
        "baseline_passed": True,
        "candidate_passed": True,
        "metric_deltas": '{"ndcgAt3": 0.1}',
        "evaluated_at": now,
    }

    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = mock_row
    mock_conn = MagicMock()
    mock_conn.execute.return_value = mock_cursor
    mock_conn.__enter__.return_value = mock_conn

    with patch("psycopg.connect", return_value=mock_conn):
        decision = log.latest_for_revision("catalog-rev-1")

    assert decision is not None
    assert decision.enabled is True
    assert decision.action == "ACTIVATE"
    assert decision.corpus_revision_id == "catalog-rev-1"
    assert decision.metric_deltas == {"ndcgAt3": 0.1}
    assert decision.baseline_passed is True
    assert decision.candidate_passed is True


def test_postgres_rag_evidence_retriever_mocked() -> None:
    retriever = PostgresRagEvidenceRetriever("postgresql://fake", max_refs=2)

    mock_rev_cursor = MagicMock()
    mock_rev_cursor.fetchone.return_value = {"revision_id": "rev-test-1"}

    mock_chunk_cursor = MagicMock()
    mock_chunk_cursor.fetchall.return_value = [
        {"chunk_id": "c1"},
        {"chunk_id": "c2"},
    ]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn

    def execute_side_effect(sql: str, params: tuple[object, ...] | None = None) -> MagicMock:
        if "active_corpus" in sql:
            return mock_rev_cursor
        return mock_chunk_cursor

    mock_conn.execute.side_effect = execute_side_effect

    with patch("psycopg.connect", return_value=mock_conn):
        active_rev = retriever.active_revision_id()
        chunks = retriever.retrieve("rev-test-1")

    assert active_rev == "rev-test-1"
    assert chunks == ("rev-test-1:chunk:c1", "rev-test-1:chunk:c2")


def test_postgres_rag_evidence_retriever_context_matching() -> None:
    from uuid import NAMESPACE_DNS, uuid5

    retriever = PostgresRagEvidenceRetriever("postgresql://fake", max_refs=3)
    place_ref = "p-tourapi-1005548"
    place_uuid = str(uuid5(NAMESPACE_DNS, f"place:{place_ref}"))

    mock_cand_cursor = MagicMock()
    mock_cand_cursor.fetchall.return_value = [
        {
            "chunk_id": "c-cand",
            "place_id": place_uuid,
            "title": "충주 최응성 고가",
            "region_code": "KR-43",
            "category_code": "HANOK",
            "chunk_text": "충청북도 충주시 살미면 소재 한옥 고택",
        }
    ]

    mock_lex_cursor = MagicMock()
    mock_lex_cursor.fetchall.return_value = [
        {
            "chunk_id": "c-lex",
            "place_id": "00000000-0000-0000-0000-000000000099",
            "title": "북촌 한옥마을",
            "region_code": "KR-11",
            "category_code": "HANOK",
            "chunk_text": "서울 종로구 북촌 한옥마을 산책로",
        }
    ]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn

    def execute_side_effect(sql: str, params: tuple[object, ...] | None = None) -> MagicMock:
        if "d.place_id = ANY" in sql:
            return mock_cand_cursor
        return mock_lex_cursor

    mock_conn.execute.side_effect = execute_side_effect

    with patch("psycopg.connect", return_value=mock_conn):
        refs, contexts = retriever.retrieve_context(
            "rev-test-1",
            query="조용한 한옥 코스",
            candidate_refs=[place_ref],
        )

    assert refs == ("rev-test-1:chunk:c-cand", "rev-test-1:chunk:c-lex")
    assert len(contexts) == 2
    assert contexts[0]["placeRef"] == place_ref
    assert contexts[0]["title"] == "충주 최응성 고가"
    assert contexts[0]["regionCode"] == "KR-43"
    assert "placeRef" not in contexts[1]
    assert contexts[1]["title"] == "북촌 한옥마을"


def test_postgres_rag_evidence_retriever_hybrid_rrf_and_region_inference() -> None:
    from onmaru_ai.rag.postgres_activation import _infer_query_region_code

    assert _infer_query_region_code("경주 불국사와 석굴암 당일치기") == "KR-47"
    assert _infer_query_region_code("부산 해운대 바다 산책") == "KR-26"
    assert _infer_query_region_code("테마 없는 일반 여행") is None

    def ok_embedder(text: str) -> tuple[float, ...]:
        return (1.0,) + (0.0,) * 383

    retriever = PostgresRagEvidenceRetriever(
        "postgresql://fake",
        max_refs=3,
        query_embedder=ok_embedder,
        query_embedding_profile_id="gemini-embedding-001-384@v1",
    )

    mock_rev_cursor = MagicMock()
    mock_rev_cursor.fetchone.return_value = {
        "embedding_profile_id": "gemini-embedding-001-384@v1"
    }

    mock_vec_cursor = MagicMock()
    mock_vec_cursor.fetchall.return_value = [
        {
            "chunk_id": "c-vec-1",
            "place_id": "00000000-0000-0000-0000-000000000001",
            "source_id": "p-tourapi-vec1",
            "title": "경주 불국사",
            "region_code": "KR-47",
            "category_code": "HISTORIC_SITE",
            "chunk_text": "경주 토함산 자락의 신라 사찰",
        },
        {
            "chunk_id": "c-shared",
            "place_id": "00000000-0000-0000-0000-000000000002",
            "source_id": "p-tourapi-shared",
            "title": "경주 양동마을",
            "region_code": "KR-47",
            "category_code": "FOLK_VILLAGE",
            "chunk_text": "유네스코 세계문화유산 한옥 마을",
        },
    ]

    mock_lex_cursor = MagicMock()
    mock_lex_cursor.fetchall.return_value = [
        {
            "chunk_id": "c-shared",
            "place_id": "00000000-0000-0000-0000-000000000002",
            "source_id": "p-tourapi-shared",
            "title": "경주 양동마을",
            "region_code": "KR-47",
            "category_code": "FOLK_VILLAGE",
            "chunk_text": "유네스코 세계문화유산 한옥 마을",
        }
    ]

    mock_conn = MagicMock()
    mock_conn.__enter__.return_value = mock_conn

    def execute_side_effect(sql: str, params: tuple[object, ...] | None = None) -> MagicMock:
        if "SELECT embedding_profile_id" in sql:
            return mock_rev_cursor
        if "FROM ai.embeddings e" in sql:
            return mock_vec_cursor
        return mock_lex_cursor

    mock_conn.execute.side_effect = execute_side_effect

    with patch("psycopg.connect", return_value=mock_conn):
        refs, contexts = retriever.retrieve_context("rev-vec-1", query="경주 한옥과 유적")

    # c-shared appears in BOTH vector and lexical results, so RRF ranks it first!
    assert refs == ("rev-vec-1:chunk:c-shared", "rev-vec-1:chunk:c-vec-1")
    assert contexts[0]["placeRef"] == "p-tourapi-shared"
    assert contexts[1]["placeRef"] == "p-tourapi-vec1"

