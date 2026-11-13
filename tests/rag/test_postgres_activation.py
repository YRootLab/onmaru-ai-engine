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
