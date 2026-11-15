#!/usr/bin/env python3
"""Ingest active KTO catalog places + TourAPI detail overviews directly from PostgreSQL
into the AI schema (`ai.corpus_revisions`, `ai.documents`, `ai.chunks`, `ai.embeddings`).

Uses Gemini `gemini-embedding-001` (384-D, L2-normalized) by default when an API key is
available, or `--hash-only` for deterministic local dry-runs.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import time
from datetime import UTC, datetime

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.corpus.batch_ingest import IngestItem, build_corpus_bundle
from onmaru_ai.embedding import (
    E5_SMALL_384,
    GEMINI_EMBEDDING_384,
    DeterministicHashBackend,
    EmbeddingBackend,
    EmbeddingService,
    GeminiEmbeddingBackend,
)
from onmaru_ai.storage.postgres import PostgresCorpusStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger("ingest_catalog_from_postgres")

_CATALOG_QUERY = """
SELECT
    public_id.public_id AS public_id,
    version.name AS name,
    version.category AS category,
    COALESCE(version.address, '') AS address,
    COALESCE(region.code, '') AS region_code,
    COALESCE(version.overview, '') AS version_overview,
    COALESCE(snap.payload->>'overview', '') AS detail_overview,
    COALESCE(active.revision_id::text, 'rev-catalog') AS source_revision
FROM onmaru.catalog_active_datasets active
JOIN onmaru.catalog_place_versions version ON version.revision_id = active.revision_id
JOIN onmaru.catalog_place_public_ids public_id ON public_id.place_id = version.place_id
LEFT JOIN onmaru.catalog_regions region ON region.id = version.region_id
LEFT JOIN onmaru.tourapi_detail_snapshots snap
    ON snap.content_id = replace(public_id.public_id, 'p-tourapi-', '')
   AND snap.status = 'OK'
WHERE active.dataset = 'kto-korean-tour'
  AND version.status = 'ACTIVE'
ORDER BY public_id.public_id ASC
"""

_REGION_PATTERNS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("경기도", "경기 "), "KR-41"),
    (("서울특별시", "서울시", "서울 "), "KR-11"),
    (("부산광역시", "부산광역", "부산시", "부산 "), "KR-26"),
    (("대구광역시", "대구시", "대구 "), "KR-27"),
    (("인천광역시", "인천시", "인천 "), "KR-28"),
    (("광주광역시", "광주특별시", "광주시 "), "KR-29"),
    (("대전광역시", "대전시", "대전 "), "KR-30"),
    (("울산광역시", "울산시", "울산 "), "KR-31"),
    (("세종특별자치시", "세종시", "세종 "), "KR-36"),
    (("강원특별자치도", "강원도", "강원 "), "KR-42"),
    (("충청북도", "충북"), "KR-43"),
    (("충청남도", "충남"), "KR-44"),
    (("전북특별자치도", "전라북도", "전북", "김제시"), "KR-45"),
    (("전라남도", "전남광주", "전남"), "KR-46"),
    (("경상북도", "경북"), "KR-47"),
    (("경상남도", "경남"), "KR-48"),
    (("제주특별자치도", "제주특별자치", "제주도", "제주 "), "KR-50"),
)


def resolve_region_code(explicit_code: str, address: str) -> str:
    explicit = explicit_code.strip().upper()
    if explicit:
        return explicit
    clean_addr = " ".join(address.split())
    if clean_addr.startswith("닫기 "):
        clean_addr = clean_addr[3:].strip()
    for prefixes, code in _REGION_PATTERNS:
        if any(clean_addr.startswith(p.strip()) for p in prefixes):
            return code
    for prefixes, code in _REGION_PATTERNS:
        if any(p.strip() in clean_addr for p in prefixes):
            return code
    return "KR-11"


class _RetryingBackend:
    def __init__(self, inner: EmbeddingBackend, max_retries: int = 5) -> None:
        self._inner = inner
        self._max_retries = max_retries
        self.model_id = inner.model_id
        self.model_commit = inner.model_commit
        self.dimensions = inner.dimensions

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        delay = 1.0
        for attempt in range(1, self._max_retries + 1):
            try:
                encoded = self._inner.encode(texts)
                return tuple(tuple(float(v) for v in vec) for vec in encoded)
            except Exception as exc:
                if attempt == self._max_retries:
                    raise
                logger.warning(
                    "Embedding batch attempt %d/%d failed (%s); retrying in %.1fs...",
                    attempt,
                    self._max_retries,
                    type(exc).__name__,
                    delay,
                )
                time.sleep(delay)
                delay = min(delay * 2.0, 20.0)
        raise RuntimeError("unreachable")


def fetch_catalog_items(dsn: str, *, limit: int | None = None) -> list[IngestItem]:
    query = _CATALOG_QUERY if limit is None else f"{_CATALOG_QUERY}\nLIMIT {int(limit)}"
    items: list[IngestItem] = []
    with psycopg.connect(dsn, row_factory=dict_row) as conn:
        rows = conn.execute(query).fetchall()
    for row in rows:
        public_id = str(row["public_id"]).strip()
        name = str(row["name"]).strip()
        category = str(row["category"]).strip()
        address = str(row["address"]).strip()
        region_code = resolve_region_code(str(row["region_code"] or ""), address)
        detail_ov = str(row["detail_overview"] or "").strip()
        version_ov = str(row["version_overview"] or "").strip()

        parts = [name]
        if address:
            parts.append(f"위치: {address}")
        if detail_ov:
            parts.append(detail_ov)
        if version_ov and version_ov not in detail_ov:
            parts.append(version_ov)
        body = "\n".join(parts)

        items.append(
            IngestItem(
                place_id=public_id,
                title=name,
                body=body,
                region_code=region_code,
                category_code=category,
                source_type="TOUR_API",
                source_id=public_id,
                source_revision=str(row["source_revision"] or "rev-catalog"),
                license_code="KOGL-1",
            )
        )
    return items


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest production KTO catalog into ai schema.")
    parser.add_argument("--dsn", default=None, help="PostgreSQL DSN with ai write privileges.")
    parser.add_argument(
        "--catalog-dsn",
        default=None,
        help="Optional separate PostgreSQL DSN for reading onmaru catalog tables.",
    )
    parser.add_argument("--revision-id", default=None, help="Corpus revision ID.")
    parser.add_argument("--gemini-api-key", default=None, help="Gemini API key.")
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Use deterministic hash backend instead of Gemini semantic embeddings.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional max rows to read.")
    parser.add_argument("--batch-size", type=int, default=100, help="Embedding batch size (<=100).")
    parser.add_argument("--activate", action="store_true", help="Activate revision after staging.")
    parser.add_argument("--dry-run", action="store_true", help="Skip Postgres write.")
    args = parser.parse_args()

    dsn = args.dsn or os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn:
        logger.error("No PostgreSQL DSN provided. Set --dsn, ONMARU_AI_DB_DSN, or ONMARU_DB_URL.")
        return 1
    catalog_dsn = args.catalog_dsn or dsn

    batch_size = max(1, min(100, args.batch_size))
    revision_id = args.revision_id or f"rev-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    logger.info("Reading active KTO catalog from PostgreSQL...")
    items = fetch_catalog_items(catalog_dsn, limit=args.limit)
    logger.info("Loaded %d active KTO catalog items.", len(items))
    if not items:
        logger.warning("No catalog items found.")
        return 0

    api_key = (
        args.gemini_api_key
        or os.environ.get("ONMARU_SECRET_GEMINI_API_KEY_CURRENT")
        or os.environ.get("GEMINI_API_KEY")
        or ""
    ).strip()

    if args.hash_only or not api_key:
        if not args.hash_only and not api_key:
            logger.warning("No Gemini API key found; falling back to DeterministicHashBackend.")
        backend: EmbeddingBackend = DeterministicHashBackend()
        profile = E5_SMALL_384
    else:
        backend = _RetryingBackend(
            GeminiEmbeddingBackend(api_key, task_type="RETRIEVAL_DOCUMENT", timeout_seconds=30.0)
        )
        profile = GEMINI_EMBEDDING_384

    logger.info(
        "Building corpus bundle revision=%s profile=%s batch_size=%d...",
        revision_id,
        profile.profile_id,
        batch_size,
    )
    embedding_service = EmbeddingService(
        backend,
        profile=profile,
        max_batch_size=batch_size,
        timeout_seconds=120.0,
    )

    started = time.perf_counter()
    result, revision, docs, chunks, embeddings = build_corpus_bundle(
        revision_id=revision_id,
        items=items,
        embedding_service=embedding_service,
        embed_batch_size=batch_size,
    )
    elapsed = time.perf_counter() - started
    logger.info(
        "Built bundle in %.1fs: input=%d accepted=%d filtered=%d chunks=%d embeddings=%d",
        elapsed,
        result.total_input,
        result.accepted_documents,
        result.filtered_out_categories,
        result.total_chunks,
        result.total_embeddings,
    )

    if args.dry_run:
        logger.info("Dry run enabled; skipping Postgres staging.")
        return 0

    store = PostgresCorpusStore(dsn)
    logger.info("Staging revision %s into ai schema...", revision_id)
    staged = store.stage(revision, docs, chunks, embeddings)
    logger.info("Stage complete (inserted=%s, manifest_hash=%s).", staged, revision.manifest_hash)

    if args.activate:
        with psycopg.connect(dsn, row_factory=dict_row) as conn:
            active_row = conn.execute(
                "SELECT revision_id FROM ai.active_corpus WHERE id=1"
            ).fetchone()
            rev_seq_row = conn.execute(
                "SELECT sequence FROM ai.revocation_state WHERE id=1"
            ).fetchone()
        expected_active = (
            str(active_row["revision_id"])
            if active_row and active_row["revision_id"]
            else None
        )
        expected_seq = int(rev_seq_row["sequence"]) if rev_seq_row else 0
        logger.info(
            "Activating %s (expected_active=%s, expected_revocation_sequence=%d)...",
            revision_id,
            expected_active,
            expected_seq,
        )
        store.activate(
            revision.revision_id,
            manifest_hash=revision.manifest_hash,
            expected_active=expected_active,
            expected_revocation_sequence=expected_seq,
        )
        logger.info("Activated corpus revision %s!", revision_id)

    return 0


if __name__ == "__main__":
    sys.exit(main())
