# Plan/Execute Data Preparation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to execute this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make Gemini-profile corpus preparation fail safe and provide a review-only, transactional loader for approved facts.

**Architecture:** Keep corpus embedding selection in the ingestion script and represent hash-only output with a non-semantic profile that cannot match Plan/Execute. Put fact row parsing/validation in a small library module and keep PostgreSQL I/O in a CLI that validates first, defaults to dry-run, and applies all rows atomically only with `--apply`.

**Tech Stack:** Python 3.12, Pydantic v2, psycopg 3, pytest, Ruff, mypy.

## Global Constraints

- Never output secret values or include DB credentials in command logs.
- Never use the migration role in the AI Engine runtime container.
- Never activate a corpus revision from the ingestion CLI.
- Never infer approval or generate reviewed facts in the loader.
- Do not contact staging/production DBs or change feature flags.

---

### Task 1: Make ingestion profile selection fail closed

**Files:**
- Create: `src/onmaru_ai/corpus/embedding_selection.py`
- Modify: `src/onmaru_ai/embedding/service.py`
- Modify: `scripts/ingest_catalog_from_postgres.py`, `scripts/ingest_to_postgres.py`
- Test: `tests/scripts/test_ingest_catalog_from_postgres.py`

**Interfaces:**
- Add immutable `DETERMINISTIC_HASH_384` profile with a non-semantic profile ID.
- Add a pure selector returning `(EmbeddingBackend, EmbeddingProfile)` and make both ingest CLIs stage only.

- [x] Add tests: missing key fails by default; Gemini key selects Gemini; `--hash-only` selects deterministic profile; hash-only plus activation is rejected.
- [x] Run focused tests and observe the expected failures.
- [x] Implement the minimal profile and CLI selection changes.
- [x] Run focused tests, Ruff, and mypy.

### Task 2: Add reviewed-fact input validation

**Files:**
- Create: `src/onmaru_ai/corpus/reviewed_facts.py`
- Create: `tests/corpus/test_reviewed_facts.py`

**Interfaces:**
- Parse JSONL records into a strict model containing revision/chunk/place IDs, exact offsets/text, kind/support/time/relation, and reviewer/approval timestamp.
- Reject blank IDs, duplicate `(revision_id, fact_id)`, non-approved records, bad relations, invalid offsets, and unsupported fields.

- [x] Add failing parser/model tests for valid records and malformed/unapproved/duplicate records.
- [x] Run the focused tests and confirm they fail for missing implementation.
- [x] Implement strict parsing and record-level validation.
- [x] Run focused tests, Ruff, and mypy.

### Task 3: Add safe Postgres validation and explicit transactional apply

**Files:**
- Create: `scripts/load_reviewed_facts.py`
- Create: `tests/scripts/test_load_reviewed_facts.py`

**Interfaces:**
- CLI arguments: `--input`, `--dsn` (or `ONMARU_AI_DB_DSN`), default dry-run, explicit `--apply`.
- Before writing, validate every row against the specified corpus revision, document public source ID, public eligibility, chunk/document ownership, chunk bounds, and exact Unicode source substring.
- With `--apply`, insert all rows in a single transaction; any mismatch or SQL failure rolls back every row.

- [x] Add failing tests for dry-run no writes, stale revision, invalid place/source mapping, invalid spans, and apply rollback.
- [x] Run focused tests and confirm expected failures.
- [x] Implement the CLI with injected connection factory for deterministic tests.
- [x] Run focused tests, Ruff, and mypy.

### Task 4: Separate corpus activation from ingestion

**Files:**
- Create: `scripts/activate_corpus_revision.py`
- Test: `tests/scripts/test_activate_corpus_revision.py`

**Interfaces:**
- CLI defaults to read-only inspection; `--apply` and an exact repeated `--confirm-revision` are both required to activate.
- Validate Gemini profile, staged state, live revision, corpus/document/chunk/embedding counts, and current revocation heartbeat before calling the existing optimistic activation.

- [x] Add failing tests for read-only default, incorrect confirmation, profile mismatch, inconsistent counts, revocation mismatch, and allowed activation.
- [x] Run the focused tests and confirm the expected failures.
- [x] Implement the CLI as a read/check wrapper over `PostgresCorpusStore.activate`.
- [x] Run focused tests, Ruff, and mypy.

### Task 5: Document operator workflow and verify repository

**Files:**
- Modify: `docs/ai-rag/operations/plan-execute-staging-runbook.md`
- Modify: `docs/ai-rag/data/aws-ingestion-guide.md`, `README.md`
- Modify: `handoff.md`

- [x] Document Gemini-key requirement, hash-only restrictions, dry-run/apply commands, one-off write-role grants, and verification queries.
- [x] Focused tests: 31 passed, 1 skipped; disposable local Postgres migration/import/rollback: 1 passed.
- [x] `uv run pytest -q`: 1096 passed, 43 skipped; Ruff passed; mypy passed (170 source files); Docker build and bundled CLI checks passed; `git diff --check` passed.
- [ ] Record actual results and push the follow-up commit to the existing PR branch.
