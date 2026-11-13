#!/usr/bin/env python3
"""CLI script to ingest approved category places and load into PostgreSQL ai schema.

Usage:
    python scripts/ingest_to_postgres.py --input <places.json> [--dsn <postgres_dsn>] [--activate]
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import UTC, datetime

from onmaru_ai.corpus.batch_ingest import IngestItem, build_corpus_bundle
from onmaru_ai.embedding import E5_SMALL_384, DeterministicHashBackend, EmbeddingService
from onmaru_ai.storage.postgres import PostgresCorpusStore

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("ingest_to_postgres")


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest places into PostgreSQL ai schema.")
    parser.add_argument("--input", required=True, help="Path to input JSON file.")
    parser.add_argument(
        "--dsn",
        default=None,
        help="PostgreSQL connection string (defaults to ONMARU_AI_DB_DSN or ONMARU_DB_URL).",
    )
    parser.add_argument(
        "--revision-id",
        default=None,
        help="Corpus revision ID (defaults to auto-generated timestamp).",
    )
    parser.add_argument(
        "--activate",
        action="store_true",
        help="Activate revision immediately after staging.",
    )
    args = parser.parse_args()

    dsn = args.dsn or os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not dsn:
        logger.error("No PostgreSQL DSN provided. Set --dsn, ONMARU_AI_DB_DSN, or ONMARU_DB_URL.")
        return 1

    input_path = args.input
    if not os.path.exists(input_path):
        logger.error("Input file not found: %s", input_path)
        return 1

    with open(input_path, encoding="utf-8") as f:
        data = json.load(f)

    raw_items = data if isinstance(data, list) else data.get("places", [])
    logger.info("Loaded %d raw records from %s", len(raw_items), input_path)

    def _resolve_region(raw: dict) -> str:
        explicit = str(raw.get("regionCode") or raw.get("region_code") or "").strip()
        if explicit:
            return explicit.upper()
        addr = str(raw.get("address") or raw.get("regionName") or "").strip()
        if addr.startswith("서울"):
            return "KR-11"
        if addr.startswith("부산"):
            return "KR-26"
        if addr.startswith("대구"):
            return "KR-27"
        if addr.startswith("인천"):
            return "KR-28"
        if addr.startswith("광주"):
            return "KR-29"
        if addr.startswith("대전"):
            return "KR-30"
        if addr.startswith("울산"):
            return "KR-31"
        if addr.startswith("세종"):
            return "KR-36"
        if addr.startswith("경기"):
            return "KR-41"
        if addr.startswith("강원"):
            return "KR-42"
        if addr.startswith("충청북도") or addr.startswith("충북"):
            return "KR-43"
        if addr.startswith("충청남도") or addr.startswith("충남"):
            return "KR-44"
        if addr.startswith("전북") or addr.startswith("전라북도"):
            return "KR-45"
        if addr.startswith("전남") or addr.startswith("전라남도"):
            return "KR-46"
        if addr.startswith("경북") or addr.startswith("경상북도"):
            return "KR-47"
        if addr.startswith("경남") or addr.startswith("경상남도"):
            return "KR-48"
        if addr.startswith("제주"):
            return "KR-50"
        return "KR-11"

    items: list[IngestItem] = []
    for raw in raw_items:
        place_id = str(raw.get("placeId") or raw.get("id") or raw.get("place_id"))
        title = str(raw.get("name") or raw.get("title"))
        body = str(
            raw.get("overview") or raw.get("description") or raw.get("body") or raw.get("name")
        )
        region_code = _resolve_region(raw)
        category_code = str(
            raw.get("category") or raw.get("categoryCode") or raw.get("category_code") or ""
        )
        source_type = str(raw.get("sourceType") or raw.get("source_type") or "TOUR_API")
        source_id = str(raw.get("sourceId") or raw.get("source_id") or "src-1")
        source_revision = str(raw.get("sourceRevision") or raw.get("source_revision") or "rev-0")
        license_code = str(raw.get("licenseCode") or raw.get("license_code") or "KOGL-1")

        items.append(
            IngestItem(
                place_id=place_id,
                title=title,
                body=body,
                region_code=region_code,
                category_code=category_code,
                source_type=source_type,
                source_id=source_id,
                source_revision=source_revision,
                license_code=license_code,
            )
        )

    revision_id = args.revision_id or f"rev-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"
    logger.info("Building corpus bundle for revision: %s", revision_id)

    embedding_backend = DeterministicHashBackend()
    embedding_service = EmbeddingService(embedding_backend, profile=E5_SMALL_384)

    result, revision, docs, chunks, embeddings = build_corpus_bundle(
        revision_id=revision_id,
        items=items,
        embedding_service=embedding_service,
    )

    logger.info(
        "Ingestion summary: total_input=%d, accepted_documents=%d, filtered_out=%d, chunks=%d",
        result.total_input,
        result.accepted_documents,
        result.filtered_out_categories,
        result.total_chunks,
    )

    if not docs:
        logger.warning("No documents accepted matching the 12 approved categories. Exiting.")
        return 0

    store = PostgresCorpusStore(dsn)
    logger.info("Staging revision into PostgreSQL ai schema...")
    try:
        staged = store.stage(revision, docs, chunks, embeddings)
        if not staged:
            logger.info("Revision manifest hash already exists; skipped duplicate insertion.")
        else:
            logger.info("Successfully staged revision %s.", revision_id)

        if args.activate:
            logger.info("Activating revision %s...", revision_id)
            store.activate(
                revision.revision_id,
                manifest_hash=revision.manifest_hash,
                expected_active=None,
                expected_revocation_sequence=0,
            )
            logger.info("Successfully activated revision %s as active corpus.", revision_id)

    except Exception as e:
        logger.error("Failed to stage/activate in PostgreSQL: %s", e)
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
