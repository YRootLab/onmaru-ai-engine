# Handoff

Current follow-up (BE canary role-boundary correction, 2026-11-17):
- Share the paired target design and implementation diagnosis with BE: 2026-10-21 system briefing and 2026-11-17 canary role-boundary report. Both are listed in `docs/ai-rag/reports/README.md` and the AI-RAG index.
- Documentation handoff is published for review in [PR #83](https://github.com/YRootLab/onmaru-ai-engine/pull/83), branch `feature/ai-rag-canary-role-boundary-handoff`.
- Remaining implementation work is outside this documentation PR: BE should track removal of Spring's arbitrary top-12 shortlist for general recommendations while preserving explicit targets and authority bounds. AI plan/execute production corpus wiring remains tracked by [#76](https://github.com/YRootLab/onmaru-ai-engine/issues/76); this PR does not close it.
- No runtime code or production configuration changed. Keep the 2026-10-21 briefing available as a temporary target-pipeline reference; the user plans to remove it in a later cleanup.

Current follow-up (Plan/Execute staging readiness, 2026-11-18):
- Related issue: [#76](https://github.com/YRootLab/onmaru-ai-engine/issues/76) remains open for staging/production validation.
- Merged PRs: AI Engine [#84](https://github.com/YRootLab/onmaru-ai-engine/pull/84), merge commit `b517891`; BE [#862](https://github.com/YRootLab/OnMaru-backend/pull/862), merge commit `ccefb5c`.
- Shipped: production Plan/Execute Postgres, lexical/vector retrieval and authority filters; exact reviewed-fact generation; SQL_PLUS_RETRIEVAL lookup-to-corpus evidence binding; failed-plan reservation cleanup; fail-closed Gemini ingestion; separate confirmation-gated corpus activation; and a read-only-by-default transactional reviewed-fact loader.
- Next: verify staging DB/profile and Compose/secrets wiring, stage a Gemini-profile corpus revision, apply `003_reviewed_facts.sql` with the migration role, obtain human-approved facts, load and inspect them, then run the Spring↔AI live HTTP route suite and rollback checks. Keep both staging and production feature flags false until the runbook gates and separate rollout approval are satisfied.
- Safety: no staging/production migration, reindex, activation, fact import, Gemini API call, live HTTP E2E, or flag change was performed. The Gemini key in chat was not used and must be revoked/replaced before staging.
- Verification: `uv run pytest -q` → 1099 passed, 43 skipped; focused data-preparation tests → 31 passed, 1 skipped; disposable local Postgres migration/import/rollback test → 1 passed; Ruff, mypy (170 source files), `git diff --check`, Docker image build, and bundled CLI checks pass.

Current ad hoc request (journey RAG activation evaluation implementation):
- Issue: implementation follow-up [#76](https://github.com/YRootLab/onmaru-ai-engine/issues/76); existing PRD work was recorded above and remains linked from `docs/ai-rag/README.md`.
- Changes: AI request accepts optional `candidatePolicy` (omitted means `v1`; unsupported values return 422), caps candidate refs at 12, and handles `useRag=true` without requiring a caller-supplied corpus revision. The server selects the active revision, returns it when retrieval is attempted, and records policy/revision provenance in logs and eval reports. Eval comparisons reject policy or corpus mismatches. `/ready` returns 503 if RAG is enabled without a durable activation log and retriever. Empty `candidateRefs` now returns `NO_RESULTS`/`NO_CANDIDATES` even when `candidateCount` is stale and positive; request schema assertions pin the backend-facing field limits/defaults. The v0.1.2 integration guide now documents the request/response contract and deployment ordering.
- Evidence/docs: Operational deployment verified on AWS Lightsail. `002_rag_activation.sql` applied to production PostgreSQL; `ai.rag_activation_decisions` table created. AI Engine container rewired with database network access, Postgres RAG activation log, and chunk evidence retriever. Gemini model updated from obsolete `gemini-2.5-flash` to active `gemini-3.5-flash-lite`, producing grounded Korean journey proposals with 12 RAG evidence refs (`rev-20261109045951:chunk:...`). `/ready` endpoint returns 200 OK from inside Spring Blue.
- Evaluation provenance: CLI schema `1.2` verified with 100-case gold dataset ([`evals/journey-eval-gold-100-v1.json`](evals/journey-eval-gold-100-v1.json)). Evaluated via `scripts/generate_gold_eval_reports.py` with baseline report ([`evals/baseline-report.json`](evals/baseline-report.json)) and challenger report ([`evals/rag-report.json`](evals/rag-report.json)). Both baseline (recall 0.833, NDCG 0.837) and challenger (recall 1.0, NDCG 1.0) pass thresholds, demonstrating positive delta (recall delta +0.167, NDCG delta +0.163). Approved activation decision recorded in production `ai.rag_activation_decisions` (id=2).
- Operator DB artifact: Production PostgreSQL query confirmed 1,080 documents, 1,080 chunks, and 1,080 embeddings for active revision `rev-20261109045951` (profile `multilingual-e5-small-384@614241f622f5`). Case-insensitive filter in [`docs/ai-rag/sql/embedding-inventory.sql`](docs/ai-rag/sql/embedding-inventory.sql) confirmed all 1,080 rows are tagged with `KR-11` (Seoul).
- Eval gate hardening: `--compare` still reports metric deltas, but marks reports incompatible if either baseline or challenger fails its own gates. Thus a failed baseline cannot be treated as activation evidence. Synthetic fixture and hand-reviewed gold remain distinct.
- Injection contract: `RagActivationLog` is a structural protocol with both in-memory and PostgreSQL implementations. `PostgresRagActivationLog` (`durable=True`) persists and reads evaluation decisions to/from `ai.rag_activation_decisions` (`migrations/ai/002_rag_activation.sql`). `PostgresRagEvidenceRetriever` reads verified chunk references from `ai.chunks` and `ai.documents` for the active revision in `ai.active_corpus`. `create_app()` automatically wires these PostgreSQL adapters when `ONMARU_AI_DB_DSN` or `ONMARU_DB_URL` is set, allowing `/ready` to pass when `ONMARU_RAG_ENABLED=true`.
- Evidence generation binding: `journey_llm` now receives `evidence_refs` from the RAG retrieval gate and injects them into the prompt's `data_block`, enabling grounded recommendation generation.
- Verification: final `uv run pytest -q` → 1043 passed, 42 skipped; `uv run mypy` passes; Ruff passes on all changed Python implementation/test files; local links in eight entry/operational docs resolve; `git diff --check` passes. Full repository Ruff remains noisy in pre-existing generated report scripts and was not used as a gate.

Current work (journey prompt relaxation):
- Branch: `feature/journey-prompt-relaxation` from `develop`.
- Changes: prompt `journey-gemini-v3` treats region as a preference, relaxes theme → category → region when matches are weak, and records `relaxedConstraints`; `NO_RESULTS` is reserved for empty or fully unrelated candidates and split into `NO_CANDIDATES` / `NO_RELEVANT_CANDIDATES` (replaces `LLM_NO_VALID_REFS`); legacy response adds `candidateCount` and `relaxedConstraints`. Contract doc §3.5 updated.
- Backend handoff: no new Issue. The backend reads the contract doc §3.5; the Spring client ignores unknown fields (tested in `HttpAiProposalClientTests` in OnMaruBE). Spring work (region 0-result re-query, invalid region → 400, reason logging) is tracked on the backend side.
- Verification: `tests/test_journey_relaxation.py` 6 passed; `tests/test_internal_auth.py`, `tests/providers/gemini`, `tests/proposal` 194 passed, 1 skipped.
- Open: production smoke (region 11 and no-region, one each) after image digest; decide whether `relaxedConstraints` is shown in the product UI.

Previous work (v0.1.2 contract alignment):
- Issue: [#73](https://github.com/YRootLab/onmaru-ai-engine/issues/73), follow-up of closed [#59](https://github.com/YRootLab/onmaru-ai-engine/issues/59). The PR references #73 and does not close it: RAG/Gemini runtime wiring and the lookup auth change remain open.
- Branch: `fix/v012-contract-alignment-legacy-refs` from `develop`.
- Changes: legacy proposal path returns real candidate refs or explicit `NO_RESULTS` with `degradedReason` (no `place:NNN` placeholders); v0.1.2 integration doc corrected to code; README documents runtime defaults, RAG/Gemini activation reality, and pgvector check SQL; grounded contract fixture tests added.
- Verification: `uv run pytest` 1009 passed, 42 skipped; `ruff check` and `mypy` pass.
- Open decisions: lookup auth sends the raw secret as Bearer (needs Spring agreement); release line for v0.4.0 vs `v0.1.x`; digest and production embedding stats need main merge and production DB access.

Previous work:
- Summary: W14 private progress sink and bounded Spring callback adapter implemented from the reviewed W0 head.
- Issue: [W14 #15](https://github.com/YRootLab/onmaru-ai-engine/issues/15), under AI-RAG Root Issue #3; dependencies [W0 #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4) and [W8 #8](https://github.com/YRootLab/onmaru-ai-engine/issues/8).
- Branch: `feature/ai-rag-w14`, isolated worktree `.worktrees/feature-ai-rag-w14`.

Touched files:
- `src/onmaru_ai/progress/`: explicit major-stage sink protocol, deterministic in-memory fake, and bounded best-effort Spring callback adapter.
- `tests/progress/`: skipped-stage behavior, stable retry ordinal/payload, correlation validation, timeout/retry caps, client rejection, and delivery-failure isolation.
- `docs/ai-rag/integration/progress-event-contract.md`: W14 implementation boundary and W13 integration handoff.

Verification:
- TDD RED: focused test collection initially failed because `onmaru_ai.progress` did not exist.
- GREEN: 8 focused W14 tests pass; full `uv run pytest -q` → 625 passed, 1 skipped; Ruff, strict mypy, and `git diff --check` pass.
- Self-review checks exact W0 payload reuse, actual-entry-only semantics, stable retry ordinal, bounded delivery, serialization under concurrent calls, and secret/text exclusion.

Next step:
- Review W14 and integrate through its issue-linked PR into `develop` after W0/W8.
- W13 should inject one sink per approved execute run and call `enter` only after each route actually reaches a major stage.

Open risk or decision:
- Spring still needs to implement and authenticate the proposed receiver path and own terminal/duplicate/out-of-order handling.
- W13 orchestration integration is intentionally absent; this adapter cannot infer stages and therefore cannot emit a stage that a route did not explicitly enter.
- Callback outcomes are available for low-cardinality telemetry, but no event contains question text, source text, document names, model drafts, or bearer credentials.

Ad hoc requests captured this session:
- Implement W14/#15 with strict TDD, actual-stage-only emission, stable retry ordinal, bounded failure isolation, focused/full checks, self-review, and a reviewable commit.

Historical status at 2026-11-19 (updated by operational results below):
- Related Issue: [#94](https://github.com/YRootLab/onmaru-ai-engine/issues/94), retitled and rewritten for local E5 ONNX CPU embeddings; Gemini remains the grounded answer-generation provider.
- Direction: use the pinned `intfloat/multilingual-e5-small` weights, dynamic-int8 ONNX for query and passage vectors, a separate embedding profile ID, and a build-pinned artifact. Existing Gemini-profile corpus remains untouched; new revision and reviewed-fact span review are required before activation.
- Work branch: `feature/local-e5-embeddings` in `.worktrees/feature/local-e5-embeddings`.
- Environment limitation: this workspace has no AI corpus/catalog DSN, so no corpus was read, embedded, staged, activated, or uploaded. Do not change feature flags.
- Implemented in `.worktrees/feature/local-e5-embeddings`: pinned multilingual-E5-small export to dynamic-int8 ONNX during image build, SentencePiece runtime tokenization with HF token-ID remap, local passage/query backend, distinct revision profile, and wiring for catalog ingestion, legacy retrieval, Plan/Execute, live evaluation, activation profile checks, and operator docs. Gemini remains generation-only.
- Verification: Docker image builds (747MB); under `docker run --memory=512m --cpus=1`, one query returns 384 normalized dimensions in 21.4ms and process RSS is 262,480KB. Focused tests: 14 passed; Ruff passes for touched Python code. The artifact build downloads pinned upstream model files during image build; runtime performs no model download.
- Still incomplete: SQLite staging spool is added but not connected to ingestion/Postgres streaming, and the current catalog ingest still materializes the full bundle in memory. Do not start the 23,573-place load until bounded/resumable staging and activation validation are addressed and measured. Current workspace has no `ONMARU_AI_DB_DSN` or `ONMARU_AI_CATALOG_READ_DSN`; no live corpus was read, embedded, uploaded, staged, or activated. Existing corpus profile mismatch remains until a new revision is staged and later activated.
- Next: connect streaming catalog iteration, per-item E5 embedding/checkpoint spool, and batched Postgres inserts; bound activation validation; then run a full production-like dry run and upload only once DB access is provisioned. Keep feature flags off until reviewed facts and the four Spring version values are reconciled.

Current ad hoc request (Plan/Execute first-open preparation, 2026-11-20):
- Branch: `feature/local-e5-embeddings` in `.worktrees/feature/local-e5-embeddings`; implementation work is isolated from `develop`.
- Direction recorded: use pinned local E5 ONNX INT8 for both query and corpus vectors; keep Gemini for grounded evidence-based generation. Do not re-embed with Gemini. First open can defer cross-encoder and use Hybrid+RRF. Quota policy: Plan/Execute returns 429 `AI_QUOTA_EXCEEDED` (+ bounded `Retry-After`); Spring should return baseline with `degradedReason=AI_QUOTA_EXCEEDED` and UI banner when a safe baseline exists; otherwise fail explicitly. SSE reports terminal error event because headers are already 200.
- Implemented: local E5 CPU packaging and wiring; durable SQLite per-place spool with resume/source-revision binding; bounded Postgres staging and activation validation; ParadeDB `pg_search` 0.27.0 `pdb.ngram(2,3)` BM25 migration and SQL top-K/filter pushdown; catalog region normalization; Gemini quota propagation through non-stream, streaming, retrieval, and embedding paths; candidate JSONL export marked for human review; active versions/heartbeat/fact gate command. Runbook documents ordering and operational commands. No automatic fact approval was added.
- Human gate/order: stage E5 corpus → apply/verify BM25 migration → activate revision → export candidate facts → human review and load via existing reviewed-fact loader → verify heartbeat and nonzero approved facts → copy the four exact version values from `scripts/print_active_runtime_versions.py` to Spring `.env` → exercise E2E → only then separately enable the feature flag. Cross-encoder remains deferred pending measured quality/latency/memory evidence.
- Verification: full `uv run --group dev pytest -q` → 1125 passed, 43 skipped; `uv run --group dev mypy src/onmaru_ai` clean; touched-file Ruff and `git diff --check` clean. Docker image built (`onmaru-ai-engine:local-e5-full`, 202,077,553 bytes). Under `--memory=512m --cpus=1`, cold first query returned 384 normalized dimensions in 1,131ms with peak RSS 315,464KB. Candidate-export and runtime-version CLI help commands both run in the image. Exact pg_search image integration and production DB tasks remain unverified/unavailable as stated.
- External limit: this workspace has no AI catalog/runtime DB DSNs. No production catalog scan, vector generation/upload, migration, activation, reviewed-fact import, Spring `.env` update, or flag change was performed. Production work remains a gated operator step after credentials/connectivity are provisioned. pg_search SQL has not been executed against the exact production 0.27.0 image in this workspace.

## Historical handoff — initial 10k local ONNX pilot plan (2026-11-20; superseded below)

- PR: [#95](https://github.com/YRootLab/onmaru-ai-engine/pull/95), branch `feature/local-e5-embeddings`, latest pushed commit `40e9101` (follow-up plan commit is already on branch; check current PR head before continuing). PR is open and reported mergeable; do not assume it is merged or CI-clean without refreshing GitHub.
- User intent: use the existing Lightsail `onmaru` catalog as the source, perform embedding inference on the local workstation with the pinned E5 ONNX INT8 artifact, then stage vectors into the AI schema. The user said staging is not necessary for this pilot; still use a new revision and do not switch the active pointer until explicit readiness gates pass.
- Confirmed role split: `ONMARU_AI_CATALOG_READ_DSN` uses `onmaru_readonly_login` for the five catalog tables; `ONMARU_AI_DB_DSN` must use the AI corpus writer/migration role for corpus staging, never the runtime role. These DSNs are not present in this local session. Lightsail Compose hostname `postgres:5432` is private to its Compose network; AWS auth and local SSH config were absent, and Postgres has no host port published. Never put DSN/password values in this file or chat.
- Existing production corpus is FP32 profile `multilingual-e5-small-384@614241f622f5`; local ONNX INT8 profile is distinct (`multilingual-e5-small-384-onnx-int8@614241f622f5`). Do not mix vectors or append to the active revision. Local seed has only 1,080 records and is not a substitute for the requested 10,000 catalog rows.
- ONNX artifact has been built with Docker and copied to `/tmp/onmaru-e5-onnx-int8` on the current workstation. Manifest checks and query/passage sample inference passed (384 dimensions, unit norm). This artifact is temporary and is not committed; regenerate with `docker build --target model-builder -t onmaru-e5-export:local .` and extract `/opt/onmaru/e5` if it is missing.
- Added in PR #95: `scripts/export_catalog_jsonl.py` (bounded read-only catalog export), `--input-jsonl --spool-only` in `scripts/ingest_catalog_from_postgres.py` (local inference without DB connections), `scripts/stage_corpus_spool.py` (read-only validation by default; DB write requires `--apply`), and local transfer instructions in the Plan/Execute runbook. Latest validation after these additions: `uv run pytest -q` → 1128 passed, 43 skipped; `uv run ruff check src scripts tests` passed; `git diff --check` passed.

### Exact continuation sequence

1. Refresh PR #95 state, checks, and head SHA. Merge/release the approved code before relying on the new scripts in an AI Engine image. Keep AI Plan/Execute flag false.
2. On Lightsail, use the repo's approved Compose environment and one-off AI Engine container to export exactly 10,000 rows with read-only catalog access. Set the secret-backed environment variables from host `.env` without printing them:

   ```bash
   export ONMARU_AI_CATALOG_READ_DSN="postgresql://${ONMARU_DB_READONLY_USER}:${ONMARU_DB_READONLY_PASSWORD}@postgres:5432/${ONMARU_POSTGRES_DB}"
   docker compose --profile ai-engine run --rm -e ONMARU_AI_CATALOG_READ_DSN \
     -v "$CORPUS_TRANSFER_DIR:/transfer" "$AI_ENGINE_SERVICE" \
     python scripts/export_catalog_jsonl.py --limit 10000 \
       --output /transfer/catalog-10000.jsonl
   ```

   Require exporter exit 0 and exactly 10,000 JSONL lines. Transfer the file to the workstation using the organization's approved secure file transfer. If current deployed image lacks this PR's exporter, use a reviewed one-off image built from the PR head; do not add the read-only credential to the long-running service.

3. On the workstation, use a new unique revision (example `rev-local-e5-pilot-20261120a`) and the JSONL snapshot. Do not set Gemini credentials for embedding:

   ```bash
   ONMARU_E5_ONNX_DIR=/tmp/onmaru-e5-onnx-int8 \
     uv run python scripts/ingest_catalog_from_postgres.py \
       --input-jsonl ./catalog-10000.jsonl --spool-only \
       --revision-id "$PILOT_REVISION" --batch-size 16 \
       --spool-path "./$PILOT_REVISION.sqlite"
   ```

   If command exits 3, inspect `<spool>.failures.jsonl`, rerun with the same input/revision/spool plus `--resume`, and require zero outstanding failures. Check counts, profile ID, source revision consistency, and manifest hash. Never stage a partial spool.

4. Transfer the closed SQLite spool to Lightsail. With the one-off corpus-writer DSN (`onmaru_ai_migration_login`) and the reviewed image, validate first (no write), inspect printed revision/profile/counts/hash, then stage only after matching the local spool evidence:

   ```bash
   docker compose --profile ai-engine run --rm -e ONMARU_AI_DB_DSN \
     -v "$CORPUS_TRANSFER_DIR:/transfer:ro" "$AI_ENGINE_SERVICE" \
     python scripts/stage_corpus_spool.py --revision-id "$PILOT_REVISION" \
       --spool-path "/transfer/$PILOT_REVISION.sqlite"
   ```

   Approved write command adds `--apply` to the same invocation. Verify DB revision state, exact profile, and document/chunk/embedding counts against spool before continuing. The staging command must not activate the revision.

5. Apply `migrations/ai/004_pg_search_bm25.sql` as migration role only after reviewing 320MB DB headroom/backup/lock plan; migration pins `maintenance_work_mem=32MB` and runs `ANALYZE ai.documents; ANALYZE ai.chunks;`. Verify pg_search 0.27.0, index definition, Korean `한옥` top-K, SQL filter pushdown, EXPLAIN plan, RSS, and runtime. Do not infer production safety from the memory setting alone.

6. Launch remains blocked by the user's production facts: `ai.reviewed_facts=0` and `ai.revocation_state.heartbeat_at` stale at 2026-11-09. Content owner must review/approve exact facts before `scripts/load_reviewed_facts.py --apply`; BE/source-revocation owner must restore its heartbeat. Then run `scripts/print_active_runtime_versions.py`, synchronize all four values (`CORPUS_REVISION`, `CONFIG_HASH`, `QUESTION_DICTIONARY_VERSION`, `SOURCE_REVOCATION_SEQUENCE`) into staging Spring, verify quota 429/Retry-After parsing and SSE terminal failure, and run live Spring↔Engine E2E. Never enable production flag until those gates and a separate rollout approval pass.

- Historical status when this section was written: no catalog export, embedding run, AI schema stage, BM25 migration, ANALYZE, corpus activation, reviewed-fact import, Spring env update, or feature-flag change had occurred. This plan's 10,000-row scope and transferred-snapshot prerequisite are superseded by the full-catalog operation below.

## Active handoff — full Lightsail catalog export and local ONNX embedding (2026-11-20)

- Related Issue/PR: #94 / [PR #95](https://github.com/YRootLab/onmaru-ai-engine/pull/95), branch `feature/local-e5-embeddings`. Latest verified pre-review follow-up head was `c7aa99a`, CI verify passed, PR was open and unmerged. This PR still groups exporter, search, and migration changes and is held for decomposition before merge.
- Accessed Lightsail `13.125.191.16` as `ubuntu` using the configured SSH key and verified container `onmaru-lightsail-postgres-1`. PostgreSQL connected as `onmaru_bootstrap` for initial inspection; catalog export then used `SET ROLE onmaru_readonly_login`. Every SQL session began with `SET default_transaction_read_only = on`. No production writes, schema changes, migrations, activation, or ANALYZE were executed.
- Count reconciliation: raw `status='ACTIVE'` distinct-place union is 23,600 across two revisions. The current source pointer contains 23,573 places; the other 27 are ACTIVE only in old revision `e3362d30-f668-41da-8496-ff84e58afa30`, outside current pointer `ffda4e5f-3315-4f25-8a8c-d8825ba69ae0`. The 27 IDs are recorded in `/tmp/onmaru-obsolete-active-revision-27-20261120.jsonl` (SHA-256 `0f21a4aeef113d23e3d50beec43856208fc711c238460f42e01b5dcf75e19014`). The correct ingestion target matching active dataset semantics is 23,573, not the stale 23,600 union.
- A 23,600-row union JSONL `/tmp/onmaru-active-catalog-20261120.jsonl` (SHA-256 `8a4530c95ffc7c77df60d8f8542971db091cd71c9328d71d486955a31395208b`) and its 23,600-row ONNX spool `/tmp/onmaru-rev-local-e5-20261120-full.sqlite` (SHA-256 `83b62b68bc333eb2dd14d2ad8d844645423377ee9d76e19e1a09541465df39e2`; manifest `sha256:14967dc815dd2fb726eee65b8a8b87cfef771d400c58f6b263079b82fb7a0d13`) include the 27 obsolete-pointer rows and MUST NOT be staged.
- Local inference completed for the reconciled current-pointer 23,573 rows in `/tmp/onmaru-rev-local-e5-20261120.sqlite`, profile `multilingual-e5-small-384-onnx-int8@614241f622f5`, with 23,573 documents/chunks/embeddings/checkpoints, zero filtered/failures, 384 dimensions, and unit-norm vectors. A newer 23,600 row union spool exists but is invalid for staging due to the 27 stale revision rows.
- Production reports 25,733 embedding rows tagged `multilingual-e5-small-384@614241f622f5`; active revision `rev-20261115025249` has 23,573. The 23,573 current-pointer export ID set exactly equals production active revision's public document ID set and the first local spool's IDs (all set differences zero). The newly generated spool has not been staged or activated.
- The first-pass spool `/tmp/onmaru-rev-local-e5-20261120.sqlite` contains the reconciled 23,573 active-pointer places. Its source IDs exactly equal both `/tmp/onmaru-active-pointer-catalog-20261120.jsonl` (SHA-256 `7d2a9cb8de745aa18a60b77a75e14ea8e6bdb971beac2fc85f7f016199d383c9`) and public document IDs in production active revision `rev-20261115025249` (set difference 0). This is the candidate spool for a later staging review; it remains un-staged.
- Code change in this branch: `iter_catalog_jsonl` now accepts the raw catalog export schema (`public_id`, title/category/address/overview fields) as well as normalized `IngestItem` JSONL. Focused script tests: 9 passed; touched-file Ruff and `git diff --check` passed. At the inspected PR #95 head `1a462ce`, CI `mypy` failed because `tests/corpus/test_staging_spool.py` was resolved under two module names. Added test package boundaries, corrected the now-explicit test import, annotated strict-test fixture paths, fixed a stale type ignore, and guarded the optional writer DSN. Local checks now pass: pytest 1,129 passed / 43 skipped, Ruff, mypy (179 files), and `scripts/test/run-ai-evals.test.sh`. These fixes are committed in follow-ups; a subsequent CI pass exposed platform-dependent ONNX optional-tokenizer typing, now changed to lazy dynamic imports with an `Any` tokenizer handle. Local pytest (1,129 passed / 43 skipped), Ruff, mypy (179 files), and eval harness pass. Hosted CI passed the full verify job (including Docker build) at head `290d2cd`; PR #95 remains open against `develop` and has not been merged.
- Profile decision: use INT8 only as a separate profile and revision (`multilingual-e5-small-384-onnx-int8@614241f622f5`); never mix it with existing rows. Rationale: deployed AI Engine image revision `c51530249b5098f9a6aeae7198633f29cfd06c81` embeds queries using `gemini-embedding-001-384@v1`, while the active DB revision is tagged E5 FP32. In a read-only diagnostic, E5 ONNX passage vectors for 120 exact stored chunk texts had cosine similarity to stored vectors median `-0.0012`, p90 `0.0412` (min `-0.1016`, max `0.0898`). This strongly rejects assuming the profile label proves E5 provenance; do not regenerate FP32 based on that label. Exact historical vector provenance remains unknown.
- Staging blocker: no staging DSN, DB snapshot/backup, or compatible pg_search image is available locally; the only running local PostgreSQL is `pgvector/pgvector:pg17` without pg_search. Added gated DB integration coverage at `tests/storage/test_pg_search_route_integration.py` for Korean lexical, dense, hybrid/router modes, filters, top-K order, empty results, and bad query dimensions. It requires a disposable `ONMARU_TEST_POSTGRES_DSN`, applies 004, and is destructive to the `ai` schema; local run skipped all 7 cases because no compatible DSN/image is provisioned. These tests do not claim quality evidence; real-corpus evaluation still requires a staging restore. Do not run 004 against production. Production read-only check: pg_search 0.27.0 exists, `chunks_search_bm25_idx` does not; active embeddings remain tagged FP32. `ai.reviewed_facts=0` and stale heartbeat are still launch blockers. The catalog read-only role cannot read `ai`; AI inventory was queried as `onmaru_ai_runtime_login`/bootstrap under `default_transaction_read_only=on`. Hybrid currently runs lexical then vector sequentially; architecture, lifecycle, observability, and telemetry docs now reflect this and defer parallelization until 2GB p95/CPU/connection measurements.
