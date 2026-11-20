#!/usr/bin/env python3
"""Ingest active KTO catalog places + TourAPI detail overviews directly from PostgreSQL
into the AI schema (`ai.corpus_revisions`, `ai.documents`, `ai.chunks`, `ai.embeddings`).

Uses a locally provisioned, pinned E5 ONNX artifact for corpus embeddings. A missing
ONMARU_E5_ONNX_DIR is an error.
`--hash-only` is reserved for local dry-runs and cannot stage or activate a corpus revision.
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections.abc import Iterator
from datetime import UTC, datetime
from pathlib import Path

import psycopg
from psycopg.rows import dict_row

from onmaru_ai.corpus.batch_ingest import IngestItem, build_corpus_bundle
from onmaru_ai.corpus.embedding_selection import select_embedding_backend
from onmaru_ai.corpus.staging_spool import CorpusStagingSpool
from onmaru_ai.embedding import (
    EmbeddingService,
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
        suffix = explicit.removeprefix("KR-DATALAB-")
        if suffix == explicit:
            suffix = explicit.removeprefix("KR-")
        if len(suffix) == 5 and suffix.isdigit():
            prefix = suffix[:2]
            return f"KR-{'42' if prefix == '51' else prefix}"
        if len(suffix) == 2 and suffix.isdigit():
            return f"KR-{'42' if suffix == '51' else suffix}"
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


def _item_from_row(row: dict[str, object]) -> IngestItem:
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
    return IngestItem(
        place_id=public_id,
        title=name,
        body="\n".join(parts),
        region_code=region_code,
        category_code=category,
        source_type="TOUR_API",
        source_id=public_id,
        source_revision=str(row["source_revision"] or "rev-catalog"),
        license_code="KOGL-1",
    )


def iter_catalog_items(
    dsn: str, *, limit: int | None = None, fetch_size: int = 256
) -> Iterator[IngestItem]:
    query = _CATALOG_QUERY if limit is None else f"{_CATALOG_QUERY}\nLIMIT {int(limit)}"
    with (
        psycopg.connect(dsn, row_factory=dict_row) as conn,
        conn.cursor(name="onmaru_catalog_stream") as cursor,
    ):
        cursor.execute(query)
        while rows := cursor.fetchmany(max(1, fetch_size)):
            for row in rows:
                yield _item_from_row(row)


def fetch_catalog_items(dsn: str, *, limit: int | None = None) -> list[IngestItem]:
    """Compatibility helper for small local/test inventories."""
    items = list(iter_catalog_items(dsn, limit=limit))
    return items


def iter_catalog_jsonl(path: Path) -> Iterator[IngestItem]:
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, start=1):
            if not line.strip():
                continue
            try:
                yield IngestItem(**json.loads(line))
            except (TypeError, ValueError, json.JSONDecodeError) as error:
                raise ValueError(f"invalid catalog JSONL at line {line_number}") from error


def main() -> int:
    parser = argparse.ArgumentParser(description="Ingest production KTO catalog into ai schema.")
    parser.add_argument("--revision-id", default=None, help="Corpus revision ID.")
    parser.add_argument(
        "--hash-only",
        action="store_true",
        help="Use deterministic hash backend instead of Gemini semantic embeddings.",
    )
    parser.add_argument("--limit", type=int, default=None, help="Optional max rows to read.")
    parser.add_argument(
        "--input-jsonl",
        type=Path,
        default=None,
        help="Use a catalog JSONL snapshot instead of a database read.",
    )
    parser.add_argument(
        "--spool-only",
        action="store_true",
        help="Generate local embeddings and spool without PostgreSQL access.",
    )
    parser.add_argument("--batch-size", type=int, default=16, help="Embedding batch size (<=100).")
    parser.add_argument("--spool-path", type=Path, default=None, help="Disk-backed resume spool.")
    parser.add_argument(
        "--resume", action="store_true", help="Resume an existing spool for this revision."
    )
    parser.add_argument(
        "--failure-manifest",
        type=Path,
        default=None,
        help="JSONL file tracking per-place failures; resume retries failed places.",
    )
    parser.add_argument("--dry-run", action="store_true", help="Skip Postgres write.")
    args = parser.parse_args()

    dsn = os.environ.get("ONMARU_AI_DB_DSN") or os.environ.get("ONMARU_DB_URL")
    if not args.spool_only and not args.dry_run and not dsn:
        logger.error("No PostgreSQL DSN provided. Set ONMARU_AI_DB_DSN or ONMARU_DB_URL.")
        return 1
    catalog_dsn = os.environ.get("ONMARU_AI_CATALOG_READ_DSN")
    if args.input_jsonl is None:
        catalog_dsn = catalog_dsn or dsn
        if not catalog_dsn:
            logger.error("Set ONMARU_AI_CATALOG_READ_DSN or pass --input-jsonl.")
            return 1

    batch_size = max(1, min(100, args.batch_size))
    revision_id = args.revision_id or f"rev-{datetime.now(UTC).strftime('%Y%m%d%H%M%S')}"

    model_dir = os.environ.get("ONMARU_E5_ONNX_DIR", "").strip()

    try:
        backend, profile = select_embedding_backend(
            model_dir=model_dir,
            hash_only=args.hash_only,
            dry_run=args.dry_run,
        )
    except ValueError as exc:
        logger.error("%s", exc)
        return 2

    embedding_service = EmbeddingService(
        backend,
        profile=profile,
        max_batch_size=batch_size,
        timeout_seconds=120.0,
    )

    spool_path = args.spool_path or Path(".onmaru-corpus-staging") / f"{revision_id}.sqlite"
    if spool_path.exists() != args.resume:
        logger.error("Spool existence must match --resume; no database writes were made.")
        return 2

    started = time.perf_counter()
    accepted = filtered = 0
    processed = 0
    failure_manifest = args.failure_manifest or spool_path.with_suffix(
        spool_path.suffix + ".failures.jsonl"
    )
    with CorpusStagingSpool(spool_path, revision_id) as spool:
        logger.info(
            "Streaming catalog revision=%s profile=%s batch_size=%d checkpointed=%d...",
            revision_id,
            profile.profile_id,
            batch_size,
            spool.counts()[0],
        )
        source_items = (
            iter_catalog_jsonl(args.input_jsonl)
            if args.input_jsonl is not None
            else iter_catalog_items(str(catalog_dsn), limit=args.limit)
        )
        for item in source_items:
            processed += 1
            spool.bind_catalog_revision(item.source_revision)
            if spool.has_place(item.place_id):
                continue
            try:
                result, item_revision, documents, chunks, embeddings = build_corpus_bundle(
                    revision_id=revision_id,
                    items=[item],
                    embedding_service=embedding_service,
                    now=spool.run_timestamp,
                    embed_batch_size=batch_size,
                )
                accepted += result.accepted_documents
                filtered += result.filtered_out_categories
                if documents:
                    spool.append(item.place_id, item_revision, documents, chunks, embeddings)
                _remove_failure(failure_manifest, item.place_id)
            except Exception as exc:
                _record_failure(failure_manifest, item.place_id, exc)
                logger.exception(
                    "Skipping failed catalog place %s; recorded in %s",
                    item.place_id,
                    failure_manifest,
                )
            if processed % 250 == 0:
                logger.info("Scanned=%d checkpointed_places=%d", processed, spool.counts()[0])

        documents_count, chunks_count, embeddings_count = spool.counts()
        outstanding = _failure_count(failure_manifest)
        if outstanding:
            logger.error(
                "%d catalog places remain failed; rerun with --resume to retry. "
                "No DB staging performed. Manifest: %s",
                outstanding,
                failure_manifest,
            )
            return 3
        if documents_count == 0:
            logger.warning("No catalog items were accepted; nothing to stage.")
            return 0
        revision = spool.revision()
        elapsed = time.perf_counter() - started
        logger.info(
            "Spool ready in %.1fs: scanned=%d accepted=%d filtered=%d chunks=%d embeddings=%d",
            elapsed,
            processed,
            documents_count,
            filtered,
            chunks_count,
            embeddings_count,
        )
        if args.dry_run or args.spool_only:
            logger.info("Spool-only mode enabled; PostgreSQL staging skipped.")
            return 0

        store = PostgresCorpusStore(dsn)
        logger.info("Streaming staged revision %s into ai schema...", revision_id)
        staged = store.stage_spool(spool)
        logger.info(
            "Stage complete (inserted=%s, manifest_hash=%s).", staged, revision.manifest_hash
        )

    return 0


def _failure_count(path: Path) -> int:
    if not path.exists():
        return 0
    return sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())


def _record_failure(path: Path, place_id: str, error: Exception) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    failures: dict[str, dict[str, str]] = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                record = json.loads(line)
                failures[str(record["place_id"])] = record
    failures[place_id] = {"place_id": place_id, "error_type": type(error).__name__}
    serialized = "".join(
        json.dumps(row, ensure_ascii=False) + "\n" for row in failures.values()
    )
    path.write_text(serialized, encoding="utf-8")


def _remove_failure(path: Path, place_id: str) -> None:
    if not path.exists():
        return
    rows = [line for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    kept = [line for line in rows if str(json.loads(line).get("place_id")) != place_id]
    if kept:
        path.write_text("\n".join(kept) + "\n", encoding="utf-8")
    else:
        path.unlink()


if __name__ == "__main__":
    sys.exit(main())
