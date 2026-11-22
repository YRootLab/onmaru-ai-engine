# Plan/Execute Production Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the AI Engine Plan/Execute pipeline from the 2026-10-21 system briefing deployable on production with real PostgreSQL BM25/vector retrieval, durable source-revocation synchronization, safe reviewed-fact gating, and verified Spring integration.

**Architecture:** Spring remains canonical for publication, authorization, live public eligibility, persistence, and SSE. Spring writes a transactionally ordered revocation outbox at catalog publication/rights transitions and exposes an authenticated snapshot/event feed; AI polls, reconciles atomically, and heartbeats only at the current watermark. AI Plan/Execute composes a real PostgreSQL corpus snapshot and Search Router across lexical, dense, and hybrid routes. Production activation follows migrations, controlled revision readiness, explicit human-reviewed facts, version synchronization, deployment, and observed E2E.

**Tech Stack:** Java/Spring Boot, PostgreSQL 17, Python 3.12, FastAPI, psycopg, pgvector 0.8.7, ParadeDB pg_search 0.27.0 (`pdb.ngram(2,3)`), GitHub Actions digest deployment.

## Global Constraints

- Keep `ONMARU_AI_PLAN_EXECUTE_ENABLED=false` until all production gates pass.
- Do not manufacture, approve, or load `ai.reviewed_facts`; require editorially approved JSONL and explicit operator `--apply`.
- Keep source revocation heartbeat stale unless BE snapshot/event watermark is proven complete and AI has applied exactly through it.
- Preserve the current active corpus revision until a replacement is staged, validated, compared, and activated with rollback details.
- Direct production is the user's chosen route; no staging environment is a prerequisite, but production changes require bounded maintenance windows and recorded measurements.
- Do not expose credentials in terminal output, logs, PRs, or handoff; rotate the previously exposed AI runtime credential before recreating AI Engine.
- Use feature branches and issue-linked PRs; never push directly to shared `develop` or `main`. Require CI and human review before merge, per repository guidance.
- Production application deployment uses the BE GitHub Actions `deploy_ai` workflow and approved image digest; do not build/deploy manually over SSH.
- Read-only audit queries must start with `SET default_transaction_read_only = on;`; database mutation scripts must require an explicit confirmation token and transaction boundaries.

---

## Repository and file map

### OnMaru-backend

- `modules/catalog/.../JdbcTourApiCatalogPublisher.java`: same-transaction outbox events at active revision pointer swap.
- `modules/catalog/...` migration files and migration manifest: durable sequence counter, append-only event table, snapshot support/indexes.
- internal AI controller/service/DTO packages: authenticated watermark, paginated snapshot, and event feed.
- `apps/spring-api/.../AiPlanVersionsProperties.java` and request adapter: dynamic source watermark; pinned other three versions.
- related catalog integration tests and internal auth contract tests.
- `.github/workflows/deploy.yml`: verify the `deploy_ai` required-CI gate against the repository's actual `verify` check name.
- docs/contracts and handoff: publish exact shared fixture/API schema and release sequence.

### OnMaru-AI-engine

- `src/onmaru_ai/corpus/revocation.py`, `storage/postgres.py`, new poller/client module: atomic snapshot bootstrap, ordered events, fresh heartbeat.
- `src/onmaru_ai/composition.py`, `retrieval/`, `storage/`: production DB connection pool, pinned corpus snapshot, lexical/dense/hybrid searcher injection.
- app lifespan/settings/health modules: start one poller, stop it cleanly, expose readiness and low-cardinality lag metrics.
- `migrations/ai/004_pg_search_bm25.sql`: bounded BM25 index DDL and analyze behavior; validate 320MiB postgres memory budget.
- tests: unit, API composition, pgvector+pg_search integration, cross-repo fixture, retrieval quality eval.
- `scripts/runtime-version.py` (or existing canonical script), `scripts/load_reviewed_facts.py`, operator runbooks and handoff.

## Task 1: Verify the two implementation branches and contracts

**Files:** read-only inspection of the cited AI and BE paths plus PR #95–#98 and issues #93/#875.

- [ ] Capture current branches, clean/dirty worktrees, and exact PR head SHAs; preserve existing user modifications.
- [ ] Verify AI document/place/source identity mapping from `build_corpus_bundle()` and existing ingest SQL.
- [ ] Verify BE actual publication/rights mutation paths and list every path that must emit outbox events.
- [ ] Confirm event/bootstrap schema and service auth contract with one versioned shared fixture.
- [ ] Record any mismatch in the spec and BE #875 before coding.

## Task 2: Implement BE durable transactional revocation outbox

**Files:** catalog migration, `JdbcTourApiCatalogPublisher`, all identified rights/publication transitions, repository/service/controller, DTO and tests.

- [ ] Write integration tests proving a failed publication rolls back both active pointer and outbox; a committed withdrawal writes events atomically.
- [ ] Write concurrent publisher tests proving no duplicate or missing committed sequence values using a locked transactional counter row.
- [ ] Compare old/new active public IDs and emit only withdrawn prior `(TOUR_API, public_id, old_dataset_revision_uuid)` tuples. Never emit withdrawal for an ID still in new active set.
- [ ] Define canonical AI `PLACE` UUID mapping in the contract: UUID5 DNS namespace of `place:<public_id>`, matching `build_corpus_bundle()`; test exact values cross-repository.
- [ ] Implement append-only event storage and event page API with `afterSequence`, bounded `limit`, stable ordering, `hasMore`, and watermark captured consistently with returned page.
- [ ] Implement snapshot session/page API pinned to `snapshotId` and a committed watermark; include all active public identities and complete revocation baseline needed to reconcile every AI `LIVE` revision.
- [ ] Require existing private service authentication; reject anonymous/browser identity; exclude catalog text, member data, provider payloads, and secrets.
- [ ] Ensure every publishing/rights-change path is instrumented or explicitly blocked from changing canonical eligibility without an outbox event.
- [ ] Add BE docs and contract fixture; run focused repository tests and required `verify` CI.
- [ ] Open/link issue-specific BE PR; do not merge without human review and passing CI.

## Task 3: Implement AI Engine snapshot bootstrap and ordered poller

**Files:** revocation ledger API, Postgres transaction methods, Spring HTTP client, poller/lifespan, settings/metrics, tests.

- [ ] Add a failing test for bootstrap watermark advancement; confirm current `apply()` rejects jumps, so implement `bootstrap(snapshot, watermark)` as a dedicated atomic operation.
- [ ] Stage fetched snapshot pages durably by snapshot ID; validate stable watermark, page sequence/count, checksum, scope, and canonical identities before DB publication.
- [ ] Atomically reconcile `PLACE` and `SOURCE_REVISION` blocklists against every AI `LIVE` revision and install bootstrap cursor; fail closed on partial fetch/write or regression.
- [ ] Poll events at 10-second intervals, ordered by contiguous sequence and bounded pages, serialized by the shared corpus write lock.
- [ ] Apply idempotently; heartbeat only after independently confirming source watermark equals applied AI cursor. Never use the static BE property or wall clock as proof.
- [ ] On timeout/auth/gap/restore mismatch, leave heartbeat stale and readiness closed; log only low-cardinality reason codes.
- [ ] Add one managed poller per process with graceful cancellation and bounded request/DB timeouts.
- [ ] Test duplicate delivery, gap, event rollback, pagination, page checksum mismatch, source regression, DB restore, auth failure, transient BE outage, and heartbeat expiry.
- [ ] Publish the same cross-repo fixture tests in both repositories; run AI tests, lint, typing, and CI.

## Task 4: Make source watermark live in Plan/Execute contract

**Files:** BE versions adapter/request DTO, AI request validation/snapshot, contract schemas and tests.

- [ ] Derive `SOURCE_REVOCATION_SEQUENCE` from BE outbox watermark on every Plan/Execute request; remove static configuration as its source of truth.
- [ ] Fail to safe baseline/explicit unavailable response if BE cannot read the watermark.
- [ ] Keep `CORPUS_REVISION`, `CONFIG_HASH`, and `QUESTION_DICTIONARY_VERSION` pinned.
- [ ] Require AI request watermark to equal fresh AI applied watermark and active corpus revocation sequence before retrieval.
- [ ] Extend contract tests for equal, stale, ahead, missing, and unreadable watermark cases; verify HTTP 429 quota response remains compatible with BE parser.

## Task 5: Connect the production Search Router to PostgreSQL

**Files:** AI `composition.py`, retrieval adapters/coordinator, DB pool/lifespan, integration tests.

- [ ] Write failing composition tests proving production currently does not inject real lexical/dense searchers or a DB-backed `CorpusSnapshot`.
- [ ] Create bounded psycopg pool and request-scoped consistent snapshot capturing active revision, profile, dictionary/config hashes, and revocation cursor.
- [ ] Wire lexical BM25 and dense vector searchers to the same DB snapshot and hard filters; HYBRID uses current sequential BM25 → vector execution until measured otherwise.
- [ ] Keep all five routes: `SQL_ONLY`, `LEXICAL_ONLY`, `DENSE_ONLY`, `HYBRID`, `SQL_PLUS_RETRIEVAL`; SQL remains Spring typed lookup only when an approved grant exists.
- [ ] Preserve safe baseline and explicit retrieval errors; no dummy snapshot or silent empty result in production composition.
- [ ] Add Testcontainers/pg_search 0.27.0 + pgvector integration tests for Korean query, filters, top-K, empty result, revocation blocklists, dimension mismatch, and fallback behavior.
- [ ] Add fixed Korean query eval and report Recall@10/nDCG@10 per lexical/vector/hybrid route against the correct 23,573-place revision. Keep stale 23,600 union spool excluded.
- [ ] Run focused/full tests, lint/types, container integration, and record resource measurements.

## Task 6: BM25 migration and production database runbook

**Files:** `migrations/ai/004_pg_search_bm25.sql`, migration tests, operator SQL/runbook.

- [ ] Confirm pg_search 0.27.0 DDL uses `USING bm25` and tokenizer `pdb.ngram(2,3)` on `ai.chunks.search_text` with required revision/document/chunk metadata.
- [ ] Make index build bounded for PostgreSQL's 320MiB cgroup memory budget; record chosen `maintenance_work_mem`, parallel workers, `lock_timeout`, `statement_timeout`, and cancellation/rollback commands.
- [ ] Run `ANALYZE ai.documents; ANALYZE ai.chunks;` after index build and test expected plan/filter pushdown/top-K.
- [ ] Provide exact preflight read-only inventory, disk/RSS observation commands, backup confirmation, migration apply, post-check, and rollback/disable procedure.
- [ ] Do not run the production migration until implementation PR is reviewed/merged and a production maintenance window is authorized.

## Task 7: Corpus and reviewed-fact production readiness

**Files:** ingestion/runtime version scripts, reviewed-fact loader docs, corpus runbook, runtime-version output.

- [ ] Compare active 23,573-place FP32 corpus against local 23,573-place ONNX INT8 spool; do not merge profile vectors. Keep current active revision until explicit profile decision and eval.
- [ ] Use existing public catalog data to build a candidate inactive revision only after choosing profile, exact source pointer, stable input manifest, and rollback pointer.
- [ ] Verify local revision counts, vector dimension/norm, duplicate/missing IDs, revision UUID source IDs, manifest checksums, and hash-only profile exclusion.
- [ ] Do not import reviewed facts. Prepare template/validation command and request editorially approved JSONL; run dry-run only until approval is present.
- [ ] Ensure runtime-version emits exactly `CORPUS_REVISION`, `CONFIG_HASH`, `QUESTION_DICTIONARY_VERSION`, `SOURCE_REVOCATION_SEQUENCE`; verify dictionary is `questions-1` or update BE default gate with explicit compatibility tests.

## Task 8: Production release, deployment, and observed E2E

**Files:** release evidence, deployment docs, GitHub workflows only if required gate mismatch is proven.

- [ ] Repair BE `deploy_ai` verify gate through an issue-linked PR if master CI check naming prevents a passing deploy; do not loosen to accept arbitrary/failed checks.
- [ ] Rotate the exposed AI runtime login credential without printing it; update only the required production secret and recreate only AI Engine via approved workflow.
- [ ] Merge each PR only after successful CI and human review; publish/record immutable AI image digest.
- [ ] Take verified database backup and confirm rollback digest/pointer before schema migration.
- [ ] Apply BM25 migration within measured production memory/time bounds, gather RSS/disk/plan/query results, and verify Korean sample search/filter/top-K.
- [ ] Bootstrap outbox snapshot, run poller catch-up, observe stable heartbeat and watermark agreement over at least 10 minutes.
- [ ] Require editorially approved facts count >=1; otherwise keep Plan/Execute disabled.
- [ ] Synchronize three pinned versions and dynamic source watermark; verify current production image/config.
- [ ] Run signed-off production E2E for all five routes, authorization denial, Spring final eligibility recheck, completed Gemini recommendation, quota 429 + `Retry-After`, baseline/error behavior, SSE `run.terminal(COMPLETED|FAILED)`, and rollback.
- [ ] Enable `ONMARU_AI_PLAN_EXECUTE_ENABLED=true` only after every gate is green, then verify health/metrics and revert immediately if any gate regresses.

## Final acceptance checklist

- [ ] BE outbox transactionality, completeness, authentication, snapshot, paging, and dynamic watermark proven in CI/integration tests.
- [ ] AI bootstrap/poller heartbeat never advances on stale, incomplete, or mismatched source state.
- [ ] Real active-revision BM25/vector/hybrid retrieval is connected and tested; Korean fixed set results and hard-filter correctness recorded.
- [ ] Production DB BM25 index and statistics are verified within measured resource limits.
- [ ] Human-reviewed fact exists and is auditable; no facts were generated or approved by automation.
- [ ] Exact runtime versions match and production app digest/config are recorded.
- [ ] Production E2E verifies plan→authority→execute→search→evidence→Spring recheck→SSE, quota failure, safe fallback, and rollback.
- [ ] Only after all checks pass is the feature flag on; final handoff includes issue/PR links, digests, SQL results, evaluation, resource data, and rollback commands.
