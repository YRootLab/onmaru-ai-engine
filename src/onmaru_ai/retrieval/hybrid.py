"""W10: Hybrid retrieval combining lexical (BM25) and dense (vector) candidates via RRF."""

from __future__ import annotations

import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any
from uuid import UUID

from onmaru_ai.contracts.models import (
    ApprovedQueryPlan,
    Candidate,
    CandidateSet,
    RetrievalStatus,
)
from onmaru_ai.storage.postgres import CorpusSnapshot

logger = logging.getLogger(__name__)

RRF_K_DEFAULT = 60
STAGE_LIMIT_SINGLE = 20
STAGE_LIMIT_HYBRID = 30


@dataclass(frozen=True, slots=True)
class HybridCandidateRecord:
    chunk_id: str
    place_id: str
    source_id: str
    source_revision: str
    lexical_rank: int | None = None
    dense_rank: int | None = None
    lexical_score: float | None = None
    dense_score: float | None = None
    rrf_score: float = 0.0


def rrf_combine(
    lexical_candidates: Sequence[Mapping[str, Any]],
    dense_candidates: Sequence[Mapping[str, Any]],
    *,
    k: int = RRF_K_DEFAULT,
    max_candidates: int = STAGE_LIMIT_HYBRID,
) -> list[dict[str, Any]]:
    """
    Combines ranked candidate items using Reciprocal Rank Fusion (RRF).
    Formula: score(c) = sum(1 / (k + rank_i))
    Tie-breaking: descending score, then ascending chunk_id.
    """
    records: dict[str, dict[str, Any]] = {}

    for item in lexical_candidates[:STAGE_LIMIT_SINGLE]:
        chunk_id = str(item["chunk_id"])
        rank = int(item["rank"])
        records[chunk_id] = {
            "chunk_id": chunk_id,
            "place_id": str(item["place_id"]),
            "source_id": str(item["source_id"]),
            "source_revision": str(item["source_revision"]),
            "lexical_rank": rank,
            "dense_rank": None,
            "score": 1.0 / (k + rank),
        }

    for item in dense_candidates[:STAGE_LIMIT_SINGLE]:
        chunk_id = str(item["chunk_id"])
        rank = int(item["rank"])
        rrf_val = 1.0 / (k + rank)
        if chunk_id in records:
            records[chunk_id]["dense_rank"] = rank
            records[chunk_id]["score"] += rrf_val
        else:
            records[chunk_id] = {
                "chunk_id": chunk_id,
                "place_id": str(item["place_id"]),
                "source_id": str(item["source_id"]),
                "source_revision": str(item["source_revision"]),
                "lexical_rank": None,
                "dense_rank": rank,
                "score": rrf_val,
            }

    # Deterministic sorting: highest score first, then smallest chunk_id lexicographically
    sorted_records = sorted(
        records.values(),
        key=lambda r: (-float(r["score"]), str(r["chunk_id"])),
    )

    out: list[dict[str, Any]] = []
    for rank, rec in enumerate(sorted_records[:max_candidates], start=1):
        item_copy = dict(rec)
        item_copy["rank"] = rank
        out.append(item_copy)

    return out


@dataclass(frozen=True, slots=True)
class HybridSearchRequest:
    plan: ApprovedQueryPlan
    clock_ns: Callable[[], int] = time.monotonic_ns


class HybridRetrievalCoordinator:
    """
    Coordinates single-route and hybrid lexical+vector retrieval.
    Enforces:
    - Never run RRF on single route.
    - Max 20 for single routes, max 30 for hybrid.
    - Fail-closed hard filters (public only, non-revoked places and sources).
    - Degraded status when one route fails; FAILED when both fail.
    """

    def __init__(
        self,
        *,
        lexical_searcher: Any | None = None,
        dense_searcher: Any | None = None,
        rrf_k: int = RRF_K_DEFAULT,
        clock_ns: Callable[[], int] = time.monotonic_ns,
    ) -> None:
        self._lexical_searcher = lexical_searcher
        self._dense_searcher = dense_searcher
        self._rrf_k = rrf_k
        self._clock_ns = clock_ns

    def should_run_rrf(self, mode: str) -> bool:
        return mode.upper() == "HYBRID"

    def execute(
        self,
        request: HybridSearchRequest,
        snapshot: CorpusSnapshot,
    ) -> CandidateSet:
        plan = request.plan
        mode = plan.approved_retrieval_mode.upper()
        started = request.clock_ns()

        if mode not in ("LEXICAL_ONLY", "DENSE_ONLY", "HYBRID"):
            raise ValueError(f"Unsupported retrieval mode: {plan.approved_retrieval_mode}")

        lexical_set: CandidateSet | None = None
        dense_set: CandidateSet | None = None
        lexical_error = False
        dense_error = False

        if mode in ("LEXICAL_ONLY", "HYBRID"):
            try:
                if self._lexical_searcher is not None:
                    from onmaru_ai.retrieval.lexical import LexicalRequest
                    filters = plan.approved_filters
                    region_codes = None if filters.region_codes is None else tuple(
                        _corpus_region(code) for code in filters.region_codes
                    )
                    lexical_filters = filters.model_copy(update={"region_codes": region_codes})
                    lexical_set = self._lexical_searcher.search(
                        LexicalRequest.model_validate({
                            "runId": plan.run_id, "planHash": plan.approved_plan_hash,
                            "versions": plan.versions,
                            "query": plan.semantic_query or " ",
                            "filters": lexical_filters,
                            "indexVersion": "ko-bm25-v1",
                        }), snapshot
                    )
            except Exception as e:
                logger.warning("Lexical search error: %s", e)
                lexical_error = True

        if mode in ("DENSE_ONLY", "HYBRID"):
            try:
                if self._dense_searcher is not None:
                    dense_set = self._dense_candidates(plan, snapshot)
            except Exception as e:
                logger.warning("Dense search error: %s", e)
                dense_error = True

        elapsed_ms = max(0, (request.clock_ns() - started) // 1_000_000)

        # Single route branch: No RRF allowed
        if mode == "LEXICAL_ONLY":
            if lexical_error or lexical_set is None:
                return self._build_empty_set(plan, "LEXICAL", "FAILED", elapsed_ms)
            return self._filtered(lexical_set, plan, snapshot, "LEXICAL")

        if mode == "DENSE_ONLY":
            if dense_error or dense_set is None:
                return self._build_empty_set(plan, "DENSE", "FAILED", elapsed_ms)
            return self._filtered(dense_set, plan, snapshot, "DENSE")

        # Hybrid route branch
        if lexical_error and dense_error:
            return self._build_empty_set(plan, "FUSION", "FAILED", elapsed_ms)

        if lexical_error:
            # Degraded, dense candidates only
            assert dense_set is not None
            return self._convert_to_fusion(
                self._filtered(dense_set, plan, snapshot, "DENSE"),
                "DEGRADED",
                elapsed_ms,
                limit=STAGE_LIMIT_HYBRID,
            )

        if dense_error:
            # Degraded, lexical candidates only
            assert lexical_set is not None
            return self._convert_to_fusion(
                self._filtered(lexical_set, plan, snapshot, "LEXICAL"),
                "DEGRADED",
                elapsed_ms,
                limit=STAGE_LIMIT_HYBRID,
            )

        # Both succeeded: run RRF
        lexical_candidates = self._post_filter(
            lexical_set.candidates if lexical_set else (), plan, snapshot
        )
        dense_candidates = self._post_filter(
            dense_set.candidates if dense_set else (), plan, snapshot
        )
        lex_items = [
            {
                "chunk_id": str(c.chunk_id),
                "place_id": str(c.place_id),
                "source_id": str(c.source_id),
                "source_revision": str(c.source_revision),
                "rank": c.rank,
                "score": c.score,
            }
            for c in lexical_candidates
        ]
        dense_items = [
            {
                "chunk_id": str(c.chunk_id),
                "place_id": str(c.place_id),
                "source_id": str(c.source_id),
                "source_revision": str(c.source_revision),
                "rank": c.rank,
                "score": c.score,
            }
            for c in dense_candidates
        ]

        fused = rrf_combine(
            lex_items, dense_items, k=self._rrf_k, max_candidates=STAGE_LIMIT_HYBRID
        )
        candidates = tuple(
            Candidate.model_validate(
                {
                    "chunkId": item["chunk_id"],
                    "placeId": item["place_id"],
                    "sourceId": item["source_id"],
                    "sourceRevision": item["source_revision"],
                    "rank": item["rank"],
                    "score": item["score"],
                    "exclusionReason": None,
                }
            )
            for item in fused
        )

        status: RetrievalStatus = "COMPLETE" if candidates else "NO_EVIDENCE"
        return CandidateSet.model_validate(
            {
                "schemaVersion": "ai-candidate-set.v1",
                "runId": plan.run_id,
                "planHash": plan.approved_plan_hash,
                "versions": plan.versions,
                "stage": "FUSION",
                "candidates": candidates,
                "retrievalStatus": status,
                "latencyMs": elapsed_ms,
            }
        )

    def _approved(self, candidate: Candidate, plan: ApprovedQueryPlan) -> bool:
        f = plan.approved_filters
        place = str(candidate.place_id)
        return (
            (f.place_ids is None or place in f.place_ids)
            and place not in f.excluded_place_ids
        )

    def _post_filter(
        self, candidates: Sequence[Candidate], plan: ApprovedQueryPlan, snapshot: CorpusSnapshot
    ) -> tuple[Candidate, ...]:
        connection = getattr(snapshot, "connection", None)
        corpus_places: dict[str, UUID] = {}
        if connection is not None and candidates:
            try:
                chunk_ids = [UUID(candidate.chunk_id) for candidate in candidates]
                rows = connection.execute(
                    """SELECT c.chunk_id, d.place_id FROM ai.chunks c
                         JOIN ai.documents d USING (revision_id, document_id)
                        WHERE c.revision_id=%s AND c.chunk_id=ANY(%s)
                          AND d.eligibility_status='PUBLIC'
                          AND NOT EXISTS (
                              SELECT 1 FROM ai.place_revocations pr
                              WHERE pr.place_id=d.place_id
                          )
                          AND NOT EXISTS (
                              SELECT 1 FROM ai.source_revocations sr WHERE
                              (sr.source_type,sr.source_id,sr.source_revision)=
                              (d.source_type,d.source_id,d.source_revision)
                          )""",
                    (snapshot.versions.corpus_revision, chunk_ids),
                ).fetchall()
                corpus_places = {str(row["chunk_id"]): UUID(str(row["place_id"])) for row in rows}
            except Exception:
                return ()
        revoked_sources = {
            (source_id, revision)
            for _, source_id, revision in snapshot.revoked_sources
        }
        revoked_place_ids = {str(place_id) for place_id in snapshot.revoked_places}
        return tuple(
            candidate
            for candidate in candidates
            if self._approved(candidate, plan)
            and (
                (connection is None and str(candidate.place_id) not in revoked_place_ids)
                or (
                    connection is not None
                    and candidate.chunk_id in corpus_places
                    and corpus_places[candidate.chunk_id] not in snapshot.revoked_places
                )
            )
            and (candidate.source_id, candidate.source_revision) not in revoked_sources
        )

    def _filtered(self, result: CandidateSet, plan: ApprovedQueryPlan,
                  snapshot: CorpusSnapshot, stage: str) -> CandidateSet:
        candidates = self._post_filter(result.candidates, plan, snapshot)
        return CandidateSet.model_validate({
            "schemaVersion": "ai-candidate-set.v1", "runId": plan.run_id,
            "planHash": plan.approved_plan_hash, "versions": plan.versions,
            "stage": stage, "candidates": candidates,
            "retrievalStatus": "COMPLETE" if candidates else "NO_EVIDENCE",
            "latencyMs": result.latency_ms,
        })

    def _dense_candidates(
        self, plan: ApprovedQueryPlan, snapshot: CorpusSnapshot
    ) -> CandidateSet:
        assert self._dense_searcher is not None
        from onmaru_ai.retrieval.vector import VectorSearchFilters
        filters = plan.approved_filters
        region_codes = None if filters.region_codes is None else frozenset(
            _corpus_region(code) for code in filters.region_codes
        )
        vector_filters = VectorSearchFilters(
            place_ids=None if filters.place_ids is None else frozenset(filters.place_ids),
            region_codes=region_codes,
            category_codes=(
                None if filters.category_codes is None else frozenset(filters.category_codes)
            ),
            excluded_place_ids=frozenset(filters.excluded_place_ids),
        )
        rows = self._dense_searcher.search(
            snapshot, plan.semantic_query or " ", filters=vector_filters, limit=STAGE_LIMIT_SINGLE
        )
        if isinstance(rows, CandidateSet):
            return rows
        candidates = tuple(Candidate.model_validate({
            "chunkId": str(row.chunk_id), "placeId": str(row.place_id),
            "sourceId": row.source_id, "sourceRevision": row.source_revision,
            "rank": row.rank, "score": row.score, "exclusionReason": None,
        }) for row in rows)
        return CandidateSet.model_validate({
            "schemaVersion": "ai-candidate-set.v1", "runId": plan.run_id,
            "planHash": plan.approved_plan_hash, "versions": plan.versions,
            "stage": "DENSE", "candidates": candidates,
            "retrievalStatus": "COMPLETE" if candidates else "NO_EVIDENCE", "latencyMs": 0,
        })
    def _convert_to_fusion(
        self,
        base_set: CandidateSet,
        status: RetrievalStatus,
        elapsed_ms: int,
        limit: int,
    ) -> CandidateSet:
        candidates = tuple(
            Candidate.model_validate(
                {
                    "chunkId": c.chunk_id,
                    "placeId": c.place_id,
                    "sourceId": c.source_id,
                    "sourceRevision": c.source_revision,
                    "rank": i,
                    "score": c.score,
                    "exclusionReason": None,
                }
            )
            for i, c in enumerate(base_set.candidates[:limit], start=1)
        )
        return CandidateSet.model_validate(
            {
                "schemaVersion": "ai-candidate-set.v1",
                "runId": base_set.run_id,
                "planHash": base_set.plan_hash,
                "versions": base_set.versions,
                "stage": "FUSION",
                "candidates": candidates,
                "retrievalStatus": status if candidates else "NO_EVIDENCE",
                "latencyMs": elapsed_ms,
            }
        )

    def _build_empty_set(
        self,
        plan: ApprovedQueryPlan,
        stage: str,
        status: RetrievalStatus,
        elapsed_ms: int,
    ) -> CandidateSet:
        return CandidateSet.model_validate(
            {
                "schemaVersion": "ai-candidate-set.v1",
                "runId": plan.run_id,
                "planHash": plan.approved_plan_hash,
                "versions": plan.versions,
                "stage": stage,
                "candidates": (),
                "retrievalStatus": status,
                "latencyMs": elapsed_ms,
            }
        )


def _corpus_region(code: str) -> str:
    normalized = code.strip().lower()
    return normalized[:5] if len(normalized) > 5 and normalized.startswith("kr-") else normalized
