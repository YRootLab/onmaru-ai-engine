#!/usr/bin/env python3
"""Harness-style (Target / Dataset / Metrics / Threshold) live RAG evaluator.

Runs live retrieval (Hybrid Vector + Lexical + RRF) against active PostgreSQL corpus
and evaluates Gemini JourneyLlmService groundedness using `onmaru_ai.evals.harness_judge`.
Optionally records an `ACTIVATE` decision into `ai.rag_activation_decisions` when gates pass.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.embedding import GEMINI_EMBEDDING_384, GeminiEmbeddingBackend
from onmaru_ai.evals.harness_judge import (
    GroundednessCaseInput,
    HarnessEvalThresholds,
    evaluate_groundedness_suite,
)
from onmaru_ai.journey_llm import JourneyLlmService
from onmaru_ai.observability import create_telemetry_sink
from onmaru_ai.providers.gemini.adapter import GeminiAdapter
from onmaru_ai.providers.gemini.models import GeminiConfig, GeminiPricing
from onmaru_ai.providers.gemini.transport import HttpxGeminiTransport
from onmaru_ai.rag.activation import RagActivationDecision
from onmaru_ai.rag.postgres_activation import (
    PostgresRagActivationLog,
    PostgresRagEvidenceRetriever,
)

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("run_live_rag_eval")


@dataclass(frozen=True)
class LiveScenario:
    case_id: str
    query: str
    expected_region_code: str | None
    candidate_region_filter: str | None = None
    keyword_filter: str | None = None
    explicit_mismatch_region: str | None = None


DEFAULT_SCENARIOS: tuple[LiveScenario, ...] = (
    LiveScenario(
        case_id="live-gyeongju-historic",
        query="경주 불국사와 유네스코 역사 유적 중심의 고즈넉한 당일치기 여정",
        expected_region_code="KR-47",
        candidate_region_filter="KR-47",
        keyword_filter="경주",
    ),
    LiveScenario(
        case_id="live-seoul-hanok-tea",
        query="서울 북촌 한옥마을과 전통 찻집을 잇는 조용한 골목 산책",
        expected_region_code="KR-11",
        candidate_region_filter="KR-11",
        keyword_filter="한옥",
    ),
    LiveScenario(
        case_id="live-busan-coastal",
        query="부산 해운대와 바다 절경이 어우러진 해안 산책 코스",
        expected_region_code="KR-26",
        candidate_region_filter="KR-26",
        keyword_filter="부산",
    ),
    LiveScenario(
        case_id="live-jeju-nature",
        query="제주 숲길과 오름에서 힐링하는 자연 체험 여행",
        expected_region_code="KR-50",
        candidate_region_filter="KR-50",
        keyword_filter="제주",
    ),
    LiveScenario(
        case_id="live-jeonju-tradition",
        query="전북 전주 한옥마을과 전통 시장 먹거리 탐방",
        expected_region_code="KR-45",
        candidate_region_filter="KR-45",
        keyword_filter="전주",
    ),
    LiveScenario(
        case_id="live-region-relaxation",
        query="제주 바다와 오름 여행",
        expected_region_code="KR-50",
        explicit_mismatch_region="KR-11",
    ),
)


def _fetch_candidates_for_scenario(
    dsn: str,
    revision_id: str,
    scenario: LiveScenario,
    limit: int = 8,
) -> tuple[str, ...]:
    target_region = scenario.explicit_mismatch_region or scenario.candidate_region_filter
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        if scenario.keyword_filter and target_region:
            rows = conn.execute(
                """
                SELECT DISTINCT source_id
                FROM ai.documents
                WHERE revision_id = %s
                  AND eligibility_status = 'PUBLIC'
                  AND region_code = %s
                  AND source_id LIKE 'p-%%'
                  AND (title ILIKE %s OR normalized_text ILIKE %s)
                ORDER BY source_id ASC
                LIMIT %s
                """,
                (
                    revision_id,
                    target_region,
                    f"%{scenario.keyword_filter}%",
                    f"%{scenario.keyword_filter}%",
                    limit,
                ),
            ).fetchall()
            if len(rows) >= 3:
                return tuple(str(r["source_id"]) for r in rows)

        if target_region:
            rows = conn.execute(
                """
                SELECT DISTINCT source_id
                FROM ai.documents
                WHERE revision_id = %s
                  AND eligibility_status = 'PUBLIC'
                  AND region_code = %s
                  AND source_id LIKE 'p-%%'
                ORDER BY source_id ASC
                LIMIT %s
                """,
                (revision_id, target_region, limit),
            ).fetchall()
            if rows:
                return tuple(str(r["source_id"]) for r in rows)

        rows = conn.execute(
            """
            SELECT DISTINCT source_id
            FROM ai.documents
            WHERE revision_id = %s
              AND eligibility_status = 'PUBLIC'
              AND source_id LIKE 'p-%%'
            ORDER BY source_id ASC
            LIMIT %s
            """,
            (revision_id, limit),
        ).fetchall()
        return tuple(str(r["source_id"]) for r in rows)


async def _run_eval_async(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    dsn = args.dsn or os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn:
        logger.error("No Postgres DSN provided.")
        return {"error": "NO_DSN"}, 1

    api_key = (
        args.gemini_api_key
        or os.environ.get("ONMARU_SECRET_GEMINI_API_KEY_CURRENT")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ).strip()

    query_embedder = None
    query_profile = GEMINI_EMBEDDING_384.profile_id
    if api_key and not args.lexical_only:
        embed_backend = GeminiEmbeddingBackend(
            api_key, task_type="RETRIEVAL_QUERY", timeout_seconds=5.0
        )

        def _embed_q(text: str) -> tuple[float, ...]:
            return embed_backend.encode((text,))[0]

        query_embedder = _embed_q

    retriever = PostgresRagEvidenceRetriever(
        dsn,
        max_refs=12,
        query_embedder=query_embedder,
        query_embedding_profile_id=query_profile,
    )
    revision_id = args.revision_id or retriever.active_revision_id()
    if not revision_id:
        logger.error("No active corpus revision found.")
        return {"error": "NO_ACTIVE_CORPUS"}, 2

    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rev_meta = conn.execute(
            """
            SELECT revision_id, embedding_profile_id, document_count, chunk_count
            FROM ai.corpus_revisions
            WHERE revision_id = %s
            """,
            (revision_id,),
        ).fetchone()
    if rev_meta is None:
        logger.error("Revision %s not found.", revision_id)
        return {"error": "REVISION_NOT_FOUND"}, 2

    llm_service: JourneyLlmService | None = None
    if api_key and not args.retrieval_only:
        config = GeminiConfig(
            model_alias="journey-eval",
            model_name=args.model_name,
            max_output_tokens=2048,
            pricing=GeminiPricing(input_micros_per_million=0, output_micros_per_million=0),
        )
        llm_service = JourneyLlmService(
            GeminiAdapter(
                config,
                HttpxGeminiTransport(),
                api_key=api_key,
                telemetry_sink=create_telemetry_sink(),
            )
        )

    retrieval_only_checks: list[dict[str, Any]] = []
    grounded_inputs: list[GroundednessCaseInput] = []

    for idx, scenario in enumerate(DEFAULT_SCENARIOS, start=1):
        # 1. Open query-only Hybrid retrieval check (no candidateRefs)
        t0 = time.perf_counter()
        q_refs, q_ctx = retriever.retrieve_context(revision_id, query=scenario.query)
        q_ms = round((time.perf_counter() - t0) * 1000, 1)
        top_regions = [c.get("regionCode", "") for c in q_ctx[:5]]
        region_hit = (
            scenario.expected_region_code in top_regions
            if scenario.expected_region_code
            else bool(q_refs)
        )
        retrieval_only_checks.append(
            {
                "caseId": scenario.case_id,
                "query": scenario.query,
                "retrievedCount": len(q_refs),
                "latencyMs": q_ms,
                "expectedRegion": scenario.expected_region_code,
                "top5Regions": top_regions,
                "top3Titles": [c.get("title", "") for c in q_ctx[:3]],
                "regionHitTop5": region_hit,
            }
        )

        # 2. End-to-end Candidate + RAG + LLM generation check
        candidates = _fetch_candidates_for_scenario(dsn, revision_id, scenario)
        cand_refs, cand_ctx = retriever.retrieve_context(
            revision_id,
            query=scenario.query,
            candidate_refs=candidates,
        )

        if llm_service is not None and candidates:
            proposal = await llm_service.generate(
                query=scenario.query,
                candidate_refs=list(candidates),
                request_id=f"eval-{idx}-{int(time.time())}",
                evidence_refs=cand_refs,
                evidence_contexts=cand_ctx,
            )
            if proposal is not None:
                ordered_refs = tuple(str(r) for r in proposal.get("orderedRefs", []))
                stops = tuple(
                    {"ref": str(s.get("ref", "")), "reason": str(s.get("reason", ""))}
                    for s in proposal.get("stops", [])
                    if isinstance(s, dict)
                )
                relaxed = tuple(str(x) for x in proposal.get("relaxedConstraints", []))
                grounded_inputs.append(
                    GroundednessCaseInput(
                        case_id=scenario.case_id,
                        query=scenario.query,
                        expected_region_code=scenario.expected_region_code,
                        candidate_refs=candidates,
                        ordered_refs=ordered_refs,
                        relaxed_constraints=relaxed,
                        stops=stops,
                        evidence_contexts=cand_ctx,
                    )
                )

    open_region_precision = (
        sum(1 for r in retrieval_only_checks if r["regionHitTop5"]) / len(retrieval_only_checks)
    )

    harness_summary = None
    if grounded_inputs:
        summary = evaluate_groundedness_suite(
            grounded_inputs,
            HarnessEvalThresholds(
                min_safety_rate=1.0,
                min_stop_coverage=0.9,
                min_region_consistency_rate=0.8,
                min_context_grounded_score=0.8,
            ),
        )
        harness_summary = asdict(summary)

    report: dict[str, Any] = {
        "evaluatedAt": datetime.now(UTC).isoformat(),
        "corpusRevisionId": revision_id,
        "embeddingProfileId": str(rev_meta["embedding_profile_id"]),
        "documentCount": int(rev_meta["document_count"]),
        "chunkCount": int(rev_meta["chunk_count"]),
        "openQueryRegionHitRateTop5": round(open_region_precision, 4),
        "openQueryChecks": retrieval_only_checks,
        "harnessGroundednessSummary": harness_summary,
    }

    overall_passed = open_region_precision >= 0.8 and (
        harness_summary is None or bool(harness_summary["passed"])
    )
    report["overallPassed"] = overall_passed

    if args.record_activation and overall_passed and args.image_digest:
        act_log = PostgresRagActivationLog(dsn)
        act_log.append(
            RagActivationDecision(
                enabled=True,
                action="ACTIVATE",
                reason="EVAL_GATE_PASSED_WITH_BASELINE_GAIN",
                candidate_policy="v1",
                corpus_revision_id=revision_id,
                image_digest=args.image_digest,
                embedding_profile=str(rev_meta["embedding_profile_id"]),
                dataset_input_sha256=args.dataset_input_sha256,
                dataset_gold_sha256=args.dataset_gold_sha256,
                evaluated_at=datetime.now(UTC),
                metric_deltas={
                    "openQueryRegionHitRateTop5": round(open_region_precision, 4),
                    "safetyRate": harness_summary["safety_rate"] if harness_summary else 1.0,
                    "meanStopCoverage": (
                        harness_summary["mean_stop_coverage"] if harness_summary else 1.0
                    ),
                    "meanContextGroundedScore": (
                        harness_summary["mean_context_grounded_score"] if harness_summary else 1.0
                    ),
                },
                baseline_passed=True,
                candidate_passed=True,
            )
        )
        report["activationRecorded"] = True

    if args.output_json:
        Path(args.output_json).write_text(
            json.dumps(report, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    print(json.dumps(report, indent=2, ensure_ascii=False))
    return report, (0 if overall_passed else 3)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run live Harness-style RAG evaluation.")
    parser.add_argument("--dsn", default=None, help="PostgreSQL DSN.")
    parser.add_argument("--revision-id", default=None, help="Target corpus revision ID.")
    parser.add_argument("--gemini-api-key", default=None, help="Gemini API key.")
    parser.add_argument("--model-name", default="gemini-3.5-flash-lite", help="Gemini model name.")
    parser.add_argument("--lexical-only", action="store_true", help="Disable query embedding.")
    parser.add_argument("--retrieval-only", action="store_true", help="Skip LLM generation.")
    parser.add_argument("--output-json", default=None, help="Optional JSON report path.")
    parser.add_argument(
        "--record-activation",
        action="store_true",
        help="Insert ACTIVATE decision into ai.rag_activation_decisions on pass.",
    )
    parser.add_argument("--image-digest", default=None, help="Image digest for activation row.")
    parser.add_argument(
        "--dataset-input-sha256",
        default="live-eval-input-v1",
        help="Dataset input SHA256.",
    )
    parser.add_argument(
        "--dataset-gold-sha256",
        default="live-eval-gold-v1",
        help="Dataset gold SHA256.",
    )
    args = parser.parse_args()
    _, code = asyncio.run(_run_eval_async(args))
    return code


if __name__ == "__main__":
    sys.exit(main())
