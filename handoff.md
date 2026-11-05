# Handoff

## Current Status (2026-11-06)

All AI-RAG engine wave issues (W0 through W22) have been implemented, tested, PR-reviewed, and merged into `develop`.
Parent epic Issue #3 has been verified and closed.

### 1. Completed Waves & PRs
- **Wave 0 (PR #29, Issue #4)**: AI-RAG boundary contract pinning and schema compatibility.
- **Wave 1 (PR #32, Issue #5)**: Public projection manifest and integrity checks.
- **Wave 2 (PR #37, Issue #12)**: Public text normalization and chunking metadata.
- **Wave 3 (PR #33, Issue #6)**: PostgreSQL atomic corpus storage and active pointer swap.
- **Wave 4 (PR #41, Issue #18)**: 384-dimensional multilingual E5 embedding adapter & pgvector retrieval.
- **Wave 5 (PR #42, Issue #19)**: Korean BM25 lexical search adapter.
- **Wave 6 (PR #43, Issue #13)**: Revocation lifecycle, fail-closed sequence checks, and bounded 2-rollback GC.
- **Wave 7 (PR #31, Issue #7)**: Question normalization, QueryFrame, and deterministic router.
- **Wave 8 (PR #34, Issue #8)**: Private plan/execute API & grant approval boundary.
- **Wave 9 (PR #38, Issue #14)**: Spring PlaceQueryPort limited lookup adapter.
- **Wave 10 (PR #44, Issue #21)**: Hybrid lexical-dense RRF fusion and degradation.
- **Wave 11 (PR #47, Issue #24)**: Lightweight reranker with deterministic fallback and diversity EvidenceSet selector.
- **Wave 12 (PR #35, Issue #9)**: Evidence-limited generation and claim proposal validation.
- **Wave 13 (PR #50, Issue #25)**: Five route orchestration and in-run fallback.
- **Wave 14 (PR #39, Issue #15)**: Bounded progress sink callback adapter.
- **Wave 15 (PR #36, Issue #10)**: Online RAG OTel telemetry and low-cardinality metrics.
- **Wave 16 (PR #30, Issue #11)**: Reviewed RAG gold schema and leakage linting.
- **Wave 17 (PR #40, Issue #16)**: Deterministic offline replay evaluation gates.
- **Wave 18 (PR #45, Issue #20)**: Asynchronous FailureCase review queue and 90-day retention/GC.
- **Wave 19 (PR #48, Issue #22)**: Quality aggregation, weekly summary reports, and decoupled notification dispatch.
- **Wave 20 (PR #49, Issue #23)**: Operator-selected isolated experiments and promotion gating.
- **Wave 21 (PR #51, Issue #26)**: Staging mixed load simulation and release evidence packaging.
- **Wave 22 (PR #46, Issue #17)**: Gold dataset curation workflow and sealing validation.

### 2. Current State
- `develop`: Fast-forwarded and synced with `origin/develop`.
- Test suite: 1,012 tests collected (970 passed, 42 skipped for optional DB/live providers).
- Static analysis: Ruff clean, Mypy strict clean (149 source files).
- Git worktrees: All local wave worktrees removed.
- Branches: All merged short-lived feature branches deleted locally and remotely.

### 3. Next Steps (Git Flow / Release)
- Under the repository Git Flow policy:
  - Create release branch (e.g. `release/v0.1.0`) from `develop`.
  - Open PR from `release/v0.1.0` into `main`.
  - Upon merge to `main`, CI will build and publish the commit OCI image with its immutable digest.
  - Tag semantic version (e.g. `v0.1.0`) on `main`.
  - Coordinate with `OnMaru-backend` for 2GB Lightsail staging deployment and infrastructure verification.
