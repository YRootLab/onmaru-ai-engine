from __future__ import annotations

import json
import logging
from datetime import UTC
from typing import cast

import psycopg
from psycopg.rows import dict_row
from psycopg.types.json import Jsonb

from onmaru_ai.rag.activation import (
    RagActivationAction,
    RagActivationDecision,
    RagActivationReason,
)

logger = logging.getLogger(__name__)


class PostgresRagActivationLog:
    """Durable PostgreSQL storage for RAG activation evaluation decisions."""

    durable = True

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn

    def append(self, decision: RagActivationDecision) -> None:
        evaluated_at = decision.evaluated_at
        if evaluated_at.tzinfo is None:
            evaluated_at = evaluated_at.replace(tzinfo=UTC)

        with psycopg.connect(self._dsn, row_factory=dict_row) as conn, conn.transaction():
            conn.execute(
                    """
                    INSERT INTO ai.rag_activation_decisions (
                        corpus_revision_id,
                        candidate_policy,
                        image_digest,
                        embedding_profile,
                        dataset_input_sha256,
                        dataset_gold_sha256,
                        enabled,
                        action,
                        reason,
                        baseline_passed,
                        candidate_passed,
                        metric_deltas,
                        evaluated_at
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    """,
                    (
                        decision.corpus_revision_id,
                        decision.candidate_policy,
                        decision.image_digest,
                        decision.embedding_profile,
                        decision.dataset_input_sha256,
                        decision.dataset_gold_sha256,
                        decision.enabled,
                        decision.action,
                        decision.reason,
                        decision.baseline_passed,
                        decision.candidate_passed,
                        Jsonb(decision.metric_deltas),
                        evaluated_at,
                    ),
                )

    def latest_for_revision(self, corpus_revision_id: str) -> RagActivationDecision | None:
        with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
            row = conn.execute(
                """
                SELECT
                    corpus_revision_id,
                    candidate_policy,
                    image_digest,
                    embedding_profile,
                    dataset_input_sha256,
                    dataset_gold_sha256,
                    enabled,
                    action,
                    reason,
                    baseline_passed,
                    candidate_passed,
                    metric_deltas,
                    evaluated_at
                FROM ai.rag_activation_decisions
                WHERE corpus_revision_id = %s
                ORDER BY evaluated_at DESC, id DESC
                LIMIT 1
                """,
                (corpus_revision_id,),
            ).fetchone()

        if row is None:
            return None

        metric_deltas = row["metric_deltas"]
        if isinstance(metric_deltas, str):
            metric_deltas = json.loads(metric_deltas)
        elif not isinstance(metric_deltas, dict):
            metric_deltas = {}

        return RagActivationDecision(
            enabled=bool(row["enabled"]),
            action=cast(RagActivationAction, row["action"]),
            reason=cast(RagActivationReason, row["reason"]),
            candidate_policy=str(row["candidate_policy"]),
            corpus_revision_id=str(row["corpus_revision_id"]),
            image_digest=str(row["image_digest"]),
            embedding_profile=str(row["embedding_profile"]),
            dataset_input_sha256=str(row["dataset_input_sha256"]),
            dataset_gold_sha256=str(row["dataset_gold_sha256"]),
            evaluated_at=row["evaluated_at"],
            metric_deltas=metric_deltas,
            baseline_passed=bool(row["baseline_passed"]),
            candidate_passed=bool(row["candidate_passed"]),
        )


class PostgresRagEvidenceRetriever:
    """Retrieves verified active corpus evidence refs from PostgreSQL ai schema."""

    def __init__(self, dsn: str, max_refs: int = 12) -> None:
        self._dsn = dsn
        self._max_refs = max_refs

    def active_revision_id(self) -> str | None:
        try:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                row = conn.execute(
                    """
                    SELECT a.revision_id
                    FROM ai.active_corpus a
                    JOIN ai.corpus_revisions r USING (revision_id)
                    WHERE a.id = 1
                      AND r.state = 'ACTIVE'
                      AND r.gc_state = 'LIVE'
                    """
                ).fetchone()
                if row is not None and row["revision_id"]:
                    return str(row["revision_id"])
        except Exception as e:
            logger.warning("failed to fetch active revision id from postgres: %s", e)
        return None

    def retrieve(self, corpus_revision_id: str) -> tuple[str, ...]:
        try:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                rows = conn.execute(
                    """
                    SELECT c.chunk_id
                    FROM ai.chunks c
                    JOIN ai.documents d USING (revision_id, document_id)
                    WHERE c.revision_id = %s
                      AND d.eligibility_status = 'PUBLIC'
                    ORDER BY c.ordinal ASC, c.chunk_id ASC
                    LIMIT %s
                    """,
                    (corpus_revision_id, self._max_refs),
                ).fetchall()
                return tuple(f"{corpus_revision_id}:chunk:{row['chunk_id']}" for row in rows)
        except Exception as e:
            logger.warning("failed to retrieve evidence refs from postgres: %s", e)
            return ()
