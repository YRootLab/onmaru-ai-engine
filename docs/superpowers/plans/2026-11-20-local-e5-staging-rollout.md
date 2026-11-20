# Local E5 Staging Rollout Implementation Plan

> **For agentic workers:** Execute inline, serially. Steps use checkbox syntax.

**Goal:** Create and stage a 10,000-place local E5 ONNX INT8 corpus revision, apply and validate pg_search BM25, and leave production activation blocked until all launch gates pass.

**Architecture:** Export the pinned model locally, then run one serial ingestion process with a durable SQLite spool and per-place failure manifest. Load the completed revision into staging only, apply bounded-memory BM25 migration plus ANALYZE, and validate retrieval and runtime contracts before any production rollout.

**Tech Stack:** Python 3.12, uv, ONNX Runtime, SQLite spool, PostgreSQL 17, pg_search 0.27.0, psql, GitHub PR checks.

## Global Constraints

- Never mix `multilingual-e5-small-384-onnx-int8@614241f622f5` vectors with the existing FP32 profile.
- Use a new corpus revision; do not overwrite or activate the production revision during the pilot.
- Process serially; no shared or concurrent spool writers.
- Any failed place blocks staging; retry with the same revision/spool and `--resume`.
- Do not insert reviewed facts without human approval.
- Keep `ONMARU_AI_PLAN_EXECUTE_ENABLED=false` until facts, heartbeat, version synchronization, and live E2E gates pass.
- Do not put DSNs or API keys in command arguments or repository files.

## Files and responsibilities

- `scripts/export_e5_onnx.py`: export pinned model and write profile manifest.
- `scripts/ingest_catalog_from_postgres.py`: serial embedding, checkpointing, failure manifest, staging write.
- `migrations/ai/004_pg_search_bm25.sql`: version guard, bounded-memory index creation, statistics refresh.
- `docs/ai-rag/operations/plan-execute-staging-runbook.md`: staging commands and acceptance checks.
- `tests/scripts/test_ingest_catalog_from_postgres.py`: serial retry/failure manifest behavior.

## Tasks

### Task 1: Validate PR and toolchain

- [ ] Check PR #95 mergeability and CI; address conflicts/failures before staging deployment.
- [ ] Confirm the local export environment has the pinned exporter dependencies and sufficient disk.
- [ ] Export to a clean local directory and verify manifest profile, dimensions (384), and dynamic-int8 quantization.

### Task 2: Generate the 10k serial pilot

- [ ] Use a new revision identifier and spool path; configure only catalog read and staging corpus-writer DSNs in the local environment.
- [ ] Run `scripts/ingest_catalog_from_postgres.py --revision-id <new-revision> --limit 10000 --batch-size 16 --spool-path <pilot.sqlite> --dry-run`.
- [ ] Confirm spool counts, manifest hash, and empty `<pilot.sqlite>.failures.jsonl`; if failures exist, rerun with the same args plus `--resume` until empty.
- [ ] Never pass `--hash-only` for a real corpus and do not configure Gemini for embedding.

### Task 3: Load staging and validate counts

- [ ] Back up staging DB and verify writer-role permissions and available disk before write.
- [ ] Rerun the same command without `--dry-run` against staging DSNs.
- [ ] Query revision state/profile and compare document, chunk, embedding counts to spool counts; verify no production active pointer changed.

### Task 4: Apply BM25 and verify search

- [ ] Verify PostgreSQL 17 and `pg_search` version 0.27.0.
- [ ] Apply `migrations/ai/004_pg_search_bm25.sql` with the migration role; stop on any error.
- [ ] Confirm `chunks_search_bm25_idx` exists and `ANALYZE ai.documents; ANALYZE ai.chunks;` completed.
- [ ] Run Korean `한옥` top-20 query and `EXPLAIN (ANALYZE, BUFFERS)` with revision/filter predicates; record index use, latency, and DB peak RSS.

### Task 5: Verify BE contract and launch gates

- [ ] Confirm `AI_QUOTA_EXCEEDED` 429 JSON plus `Retry-After` parses in Spring client; verify `questions-1` matches Spring's expected version.
- [ ] Keep reviewed facts empty until content owners approve exact spans; verify the runtime-version command fails closed while fact count is zero or heartbeat stale.
- [ ] After humans approve facts and BE restores heartbeat, synchronize all four version values and run staging Spring↔Engine E2E including normal completion, quota fallback/failure, and SSE `run.terminal(FAILED)`.
- [ ] Only after these gates, prepare a separate production migration/ingestion change and rollout approval; do not enable production flag in this plan.

## Acceptance

- 10,000-item serial spool has zero unresolved failures and profile manifest matches ONNX INT8 profile.
- Staging counts and profile exactly match the spool manifest.
- BM25 index is present, ANALYZE completed, and Korean top-K/filter query has recorded execution plan and memory evidence.
- All BE contract and pre-open gates are evidenced; production remains unchanged and disabled until separate rollout approval.
