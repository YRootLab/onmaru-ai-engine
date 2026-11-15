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


_QUERY_REGION_HINTS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("서울", "북촌", "인사동", "경복궁", "창덕궁", "익선동", "종로", "강남", "홍대"), "KR-11"),
    (("부산", "해운대", "자갈치", "국제시장", "태종대", "광안리"), "KR-26"),
    (("대구",), "KR-27"),
    (("인천", "강화"), "KR-28"),
    (("대전",), "KR-30"),
    (("울산",), "KR-31"),
    (("세종",), "KR-36"),
    (("경기", "수원", "파주", "용인", "연천", "가평", "양평"), "KR-41"),
    (("강원", "강릉", "속초", "평창", "춘천", "양양", "오대산"), "KR-42"),
    (("충북", "충청북", "충주", "단양", "제천", "음성"), "KR-43"),
    (("충남", "충청남", "공주", "부여", "서천", "서산", "태안", "보령"), "KR-44"),
    (("전북", "전라북", "전주", "고창", "남원", "군산", "부안"), "KR-45"),
    (("전남", "전라남", "광주", "담양", "순천", "여수", "완도", "보성"), "KR-46"),
    (("경북", "경상북", "경주", "안동", "영주", "봉화", "문경"), "KR-47"),
    (("경남", "경상남", "통영", "거제", "진주", "합천", "하동", "남해"), "KR-48"),
    (("제주", "서귀포"), "KR-50"),
)


def _infer_query_region_code(query: str) -> str | None:
    lowered = query.strip().lower()
    if not lowered:
        return None
    for keywords, region_code in _QUERY_REGION_HINTS:
        if any(kw in lowered for kw in keywords):
            return region_code
    return None


_QUERY_STOPWORDS: frozenset[str] = frozenset(
    {
        "추천", "추천해줘", "여행", "여정", "코스", "일정", "탐방", "산책", "중심",
        "당일치기", "주변", "부근", "명소", "장소", "어울리는", "어우러진", "잇는",
        "있는", "좋은", "조용한", "고즈넉한", "힐링", "힐링하는", "체험", "알려줘",
        "찾아줘", "부탁해", "주세요", "에서", "으로", "함께",
    }
)


def _extract_topic_tokens(clean_query: str) -> list[str]:
    import re

    raw_tokens = re.findall(r"[가-힣A-Za-z0-9]{2,}", clean_query)
    region_words = {kw for kws, _ in _QUERY_REGION_HINTS for kw in kws}
    expanded: list[str] = []
    seen: set[str] = set()
    for tok in raw_tokens:
        candidates = [tok]
        for suffix in (
            "에서", "으로", "과", "와", "의", "에",
            "로", "을", "를", "은", "는", "이", "가",
        ):
            if len(tok) >= len(suffix) + 2 and tok.endswith(suffix):
                candidates.append(tok[: -len(suffix)])
                break
        for cand in candidates:
            if cand in _QUERY_STOPWORDS or cand in region_words or cand in seen:
                continue
            seen.add(cand)
            expanded.append(cand)
    return expanded[:8]


def _score_lexical_rows(
    rows: list[dict[str, object]], tokens: list[str]
) -> list[dict[str, object]]:
    if not rows:
        return []

    def _row_score(row: dict[str, object]) -> tuple[float, int, str]:
        title = str(row.get("title") or "").lower()
        body = str(row.get("chunk_text") or "").lower()
        score = 0.0
        for tok in tokens:
            t_low = tok.lower()
            if t_low in title:
                score += 4.0
            elif t_low in body:
                score += 1.0
        if len(body) > 120:
            score += 0.25
        return (score, len(body), str(row.get("chunk_id") or ""))

    return sorted(rows, key=_row_score, reverse=True)


class PostgresRagEvidenceRetriever:
    """Retrieves active corpus evidence refs & contexts via Hybrid Vector + Lexical RRF."""

    def __init__(
        self,
        dsn: str,
        max_refs: int = 12,
        *,
        query_embedder: object | None = None,
        query_embedding_profile_id: str = "gemini-embedding-001-384@v1",
    ) -> None:
        self._dsn = dsn
        self._max_refs = max_refs
        self._query_embedder = query_embedder
        self._query_embedding_profile_id = query_embedding_profile_id

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
        refs, _ = self.retrieve_context(corpus_revision_id)
        return refs

    def _embed_query_safe(self, query: str) -> str | None:
        if self._query_embedder is None or not callable(self._query_embedder):
            return None
        try:
            vec = self._query_embedder(query)
            vals = [float(x) for x in vec]
            if len(vals) != 384:
                return None
            return json.dumps(vals, allow_nan=False)
        except Exception as e:
            logger.warning("hybrid query embedding fallback to lexical-only: %s", e)
            return None

    def retrieve_context(
        self,
        corpus_revision_id: str,
        *,
        query: str = "",
        candidate_refs: tuple[str, ...] | list[str] = (),
    ) -> tuple[tuple[str, ...], tuple[dict[str, str], ...]]:
        from uuid import NAMESPACE_DNS, uuid5

        uuid_to_ref = {
            str(uuid5(NAMESPACE_DNS, f"place:{ref}")): ref
            for ref in candidate_refs
            if isinstance(ref, str) and ref.strip()
        }
        candidate_uuids = list(uuid_to_ref.keys())
        clean_query = query.strip()
        inferred_region = _infer_query_region_code(clean_query)

        try:
            with psycopg.connect(self._dsn, row_factory=dict_row) as conn:
                rev_row = conn.execute(
                    "SELECT embedding_profile_id FROM ai.corpus_revisions WHERE revision_id = %s",
                    (corpus_revision_id,),
                ).fetchone()
                rev_profile = (
                    str(rev_row["embedding_profile_id"])
                    if rev_row is not None and rev_row.get("embedding_profile_id")
                    else ""
                )

                anchor_rows: list[dict[str, object]] = []
                if candidate_uuids:
                    anchor_rows = [
                        dict(r)
                        for r in conn.execute(
                            """
                            SELECT
                                c.chunk_id,
                                d.place_id,
                                d.source_id,
                                d.title,
                                d.region_code,
                                d.category_code,
                                c.chunk_text
                            FROM ai.chunks c
                            JOIN ai.documents d USING (revision_id, document_id)
                            WHERE c.revision_id = %s
                              AND d.eligibility_status = 'PUBLIC'
                              AND d.place_id = ANY(%s::uuid[])
                              AND NOT EXISTS (
                                  SELECT 1 FROM ai.place_revocations pr
                                  WHERE pr.place_id = d.place_id
                              )
                            ORDER BY c.ordinal ASC, c.chunk_id ASC
                            LIMIT %s
                            """,
                            (corpus_revision_id, candidate_uuids, self._max_refs),
                        ).fetchall()
                    ]

                vector_rows: list[dict[str, object]] = []
                if (
                    clean_query
                    and self._query_embedder is not None
                    and rev_profile == self._query_embedding_profile_id
                ):
                    vec_json = self._embed_query_safe(clean_query)
                    if vec_json is not None:
                        vector_rows = [
                            dict(r)
                            for r in conn.execute(
                                """
                                SELECT
                                    c.chunk_id,
                                    d.place_id,
                                    d.source_id,
                                    d.title,
                                    d.region_code,
                                    d.category_code,
                                    c.chunk_text
                                FROM ai.embeddings e
                                JOIN ai.chunks c USING (revision_id, chunk_id)
                                JOIN ai.documents d USING (revision_id, document_id)
                                WHERE e.revision_id = %s
                                  AND e.embedding_profile_id = %s
                                  AND d.eligibility_status = 'PUBLIC'
                                  AND NOT EXISTS (
                                      SELECT 1 FROM ai.place_revocations pr
                                      WHERE pr.place_id = d.place_id
                                  )
                                ORDER BY e.embedding <=> %s::vector ASC, c.chunk_id ASC
                                LIMIT 20
                                """,
                                (corpus_revision_id, rev_profile, vec_json),
                            ).fetchall()
                        ]

                lexical_rows: list[dict[str, object]] = []
                if clean_query:
                    topic_tokens = _extract_topic_tokens(clean_query)
                    if not topic_tokens:
                        import re

                        topic_tokens = [
                            t for t in re.findall(r"[가-힣A-Za-z0-9]{2,}", clean_query)
                            if t not in _QUERY_STOPWORDS
                        ][:6]
                    like_patterns = [f"%{tok}%" for tok in topic_tokens]

                    if inferred_region and like_patterns:
                        raw_lex = [
                            dict(r)
                            for r in conn.execute(
                                """
                                SELECT
                                    c.chunk_id,
                                    d.place_id,
                                    d.source_id,
                                    d.title,
                                    d.region_code,
                                    d.category_code,
                                    c.chunk_text
                                FROM ai.documents d
                                JOIN ai.chunks c USING (revision_id, document_id)
                                WHERE d.revision_id = %s
                                  AND d.region_code = %s
                                  AND d.eligibility_status = 'PUBLIC'
                                  AND NOT EXISTS (
                                      SELECT 1 FROM ai.place_revocations pr
                                      WHERE pr.place_id = d.place_id
                                  )
                                  AND c.search_text ILIKE ANY(%s)
                                LIMIT 120
                                """,
                                (corpus_revision_id, inferred_region, like_patterns),
                            ).fetchall()
                        ]
                        lexical_rows = _score_lexical_rows(raw_lex, topic_tokens)[:20]

                    if not lexical_rows and like_patterns:
                        raw_lex = [
                            dict(r)
                            for r in conn.execute(
                                """
                                SELECT
                                    c.chunk_id,
                                    d.place_id,
                                    d.source_id,
                                    d.title,
                                    d.region_code,
                                    d.category_code,
                                    c.chunk_text
                                FROM ai.chunks c
                                JOIN ai.documents d USING (revision_id, document_id)
                                WHERE c.revision_id = %s
                                  AND d.eligibility_status = 'PUBLIC'
                                  AND NOT EXISTS (
                                      SELECT 1 FROM ai.place_revocations pr
                                      WHERE pr.place_id = d.place_id
                                  )
                                  AND (
                                      c.search_tsv @@ plainto_tsquery('simple', %s)
                                      OR c.search_text ILIKE ANY(%s)
                                  )
                                LIMIT 120
                                """,
                                (corpus_revision_id, clean_query, like_patterns),
                            ).fetchall()
                        ]
                        lexical_rows = _score_lexical_rows(raw_lex, topic_tokens)[:20]

                    if not lexical_rows and inferred_region:
                        lexical_rows = [
                            dict(r)
                            for r in conn.execute(
                                """
                                SELECT
                                    c.chunk_id,
                                    d.place_id,
                                    d.source_id,
                                    d.title,
                                    d.region_code,
                                    d.category_code,
                                    c.chunk_text
                                FROM ai.documents d
                                JOIN ai.chunks c USING (revision_id, document_id)
                                WHERE d.revision_id = %s
                                  AND d.region_code = %s
                                  AND d.eligibility_status = 'PUBLIC'
                                  AND NOT EXISTS (
                                      SELECT 1 FROM ai.place_revocations pr
                                      WHERE pr.place_id = d.place_id
                                  )
                                LIMIT 20
                                """,
                                (corpus_revision_id, inferred_region),
                            ).fetchall()
                        ]

                # Deterministic RRF merge: anchor candidates lead, followed by Vector+Lexical RRF
                rrf_k = 60
                by_chunk: dict[str, dict[str, object]] = {}
                scores: dict[str, float] = {}

                for rank, row in enumerate(anchor_rows, start=1):
                    cid = str(row["chunk_id"])
                    by_chunk[cid] = row
                    scores[cid] = scores.get(cid, 0.0) + 10.0 + (1.0 / (rrf_k + rank))

                for rank, row in enumerate(vector_rows, start=1):
                    cid = str(row["chunk_id"])
                    by_chunk.setdefault(cid, row)
                    scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

                for rank, row in enumerate(lexical_rows, start=1):
                    cid = str(row["chunk_id"])
                    by_chunk.setdefault(cid, row)
                    scores[cid] = scores.get(cid, 0.0) + (1.0 / (rrf_k + rank))

                if inferred_region:
                    for cid, row in by_chunk.items():
                        if str(row.get("region_code") or "").upper() == inferred_region:
                            scores[cid] = scores.get(cid, 0.0) + 0.01

                merged_rows = [
                    by_chunk[cid]
                    for cid, _ in sorted(
                        scores.items(),
                        key=lambda item: (-item[1], item[0]),
                    )
                ]

                if not merged_rows and not candidate_uuids:
                    merged_rows = [
                        dict(r)
                        for r in conn.execute(
                            """
                            SELECT
                                c.chunk_id,
                                d.place_id,
                                d.source_id,
                                d.title,
                                d.region_code,
                                d.category_code,
                                c.chunk_text
                            FROM ai.chunks c
                            JOIN ai.documents d USING (revision_id, document_id)
                            WHERE c.revision_id = %s
                              AND d.eligibility_status = 'PUBLIC'
                              AND NOT EXISTS (
                                  SELECT 1 FROM ai.place_revocations pr
                                  WHERE pr.place_id = d.place_id
                              )
                            ORDER BY c.ordinal ASC, c.chunk_id ASC
                            LIMIT %s
                            """,
                            (corpus_revision_id, self._max_refs),
                        ).fetchall()
                    ]

                refs: list[str] = []
                contexts: list[dict[str, str]] = []
                for row in merged_rows[: self._max_refs]:
                    chunk_id = str(row["chunk_id"])
                    ref = f"{corpus_revision_id}:chunk:{chunk_id}"
                    refs.append(ref)
                    place_uuid = str(row.get("place_id") or "")
                    source_id = str(row.get("source_id") or "")
                    ctx: dict[str, str] = {
                        "evidenceRef": ref,
                        "title": str(row.get("title") or ""),
                        "regionCode": str(row.get("region_code") or ""),
                        "categoryCode": str(row.get("category_code") or ""),
                        "excerpt": str(row.get("chunk_text") or "")[:300],
                    }
                    if place_uuid in uuid_to_ref:
                        ctx["placeRef"] = uuid_to_ref[place_uuid]
                    elif source_id.startswith("p-"):
                        ctx["placeRef"] = source_id
                    contexts.append(ctx)
                return tuple(refs), tuple(contexts)
        except Exception as e:
            logger.warning("failed to retrieve evidence refs from postgres: %s", e)
            return (), ()
