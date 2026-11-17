# Handoff

Current ad hoc request (production journey pipeline architecture review, 2026-11-17):
- Scope: compare the backend `develop` E2E report [`journey_e2e_data_flow.md`](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/journey_e2e_data_flow.md) with backend and AI-engine code; user wants AI-engine to own query interpretation and retrieval rather than Spring preselecting a small catalog candidate set.
- Report: [`2026-11-17-canary-role-boundary-review.md`](docs/ai-rag/reports/2026-11-17-canary-role-boundary-review.md) is indexed from `docs/ai-rag/README.md`. It documents the target pipeline, legacy candidate limitation, `useRag` request discrepancy, AI plan/execute retrieval wiring gap, ownership correction, P0 remediation sequence, and evidence needed before release.
- Confirmed backend `develop` behavior: legacy `HttpAiProposalClient` receives candidates before AI generation. `JdbcJourneyCandidateProvider` calls `ApprovedPlaceReader` with limit 12; its SQL applies region/category filters and orders by place name/public ID, with no query relevance scoring. AI and Spring validators prohibit output refs outside that allowlist.
- Contract discrepancy: the E2E report says `useRag=true`, but backend `HttpAiProposalClient.requestBody()` omits it; AI `JourneyProposalRequest.use_rag` defaults false. This source pairing skips legacy retrieval. Reconcile run ID, raw request, source/image digests, environment flags, active corpus and RAG logs before attributing the 2026-11-16 recommendations to RAG.
- Separate target-path gap: backend plan/execute is opt-in (`onmaru.ai.plan-execute-enabled`, default false). In this AI checkout, `create_production_plan_execute_service()` passes `DummyCorpusSnapshot` and constructs `HybridRetrievalCoordinator()` without lexical/dense searchers; its `ProductionGenerator` is deterministic. Switching endpoint alone cannot deliver independent production RAG.
- Current status: analysis/report only; no production runtime or service code changed. Related issue #3 is closed and #76 covers legacy RAG operation, not the whole target-path correction. Before implementation, create/link an issue for the candidate-contract retirement and real plan/execute corpus wiring. Release must not describe the legacy candidate-prefilter path as AI-engine independent RAG.
- Documentation alignment: `docs/ai-rag/README.md` now identifies the 2026-11-17 report as the current role-boundary diagnosis; PRD remains product scope, while its 12-candidate `candidatePolicy` appendix is marked historical/non-normative. The 2026-10-21 HTML is labeled a generated target snapshot, not implementation evidence. Its builder still overwrites that dated file, so preserve it until output-path support exists. The query-processing contract clarifies that Spring may pass authority bounds and explicit user-pinned IDs, not a pre-ranked shortlist.
- Documentation organization: moved AI-RAG Markdown from the flat directory into `product/`, `architecture/`, `integration/`, `data/`, `quality/`, `operations/`, and `history/`; added `docs/ai-rag/DOCUMENTATION.md` and recategorized the main README. Rebased local Markdown links, repository path references, and the HTML briefing builder's source paths. Verified local Markdown links and all 21 builder inputs resolve; no application tests were run for this documentation-only change.
- Report presentation: added `docs/ai-rag/reports/2026-11-17-canary-role-boundary-review.html`, a self-contained Korean HTML rendering of the diagnosis with side-by-side legacy/target pipeline diagrams and links to the Markdown source and 2026-10-21 briefing. Added `reports/README.md` and linked the HTML from the AI-RAG index and documentation reading order. The historical briefing HTML remains untouched.

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
