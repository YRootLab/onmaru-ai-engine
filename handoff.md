# Handoff

Current work:
- Summary: W8 private plan/execute boundary implemented from the reviewed W0 head.
- Issue: [W8 #8](https://github.com/YRootLab/onmaru-ai-engine/issues/8), under AI-RAG Root Issue #3; dependency [W0 #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4).
- Branch: `feature/ai-rag-w8`, isolated worktree `.worktrees/feature-ai-rag-w8`.

Touched files:
- `src/onmaru_ai/api/`: private versioned plan/execute endpoints, injected service and closed response/error envelopes; transport and integration documentation.
- `src/onmaru_ai/security/plan_validator.py`: metadata-only plan binding, exact approval and trusted 30-second grant checks.
- `src/onmaru_ai/main.py`: optional service injection and endpoint registration alongside existing APIs.
- `tests/api/plan_execute/`: W0 fixture round trips, authentication, correlation, version/filter/semantic/grant rejections, no-dispatch assertions, timeout and concurrency checks.

Verification:
- TDD RED: initial 32 tests failed before implementation (missing endpoint/module); a later revocation-change-during-grant-resolution regression failed with an unwanted executor dispatch before the fix.
- GREEN: 53 W8 boundary tests; full `uv run pytest -q` → 617 passed, 1 skipped (opt-in live provider smoke test).
- `uv run ruff check src tests scripts`, `uv run mypy` (73 source files), and `git diff --check` passed.
- Pytest reports two upstream FastAPI/Starlette TestClient deprecation warnings; no application warning or test failure.
- Self-review checked auth-before-body parsing, exact W0 binding, current-version recheck immediately before dispatch, no query-text storage/logging, consumed-run behavior on failure/timeout, and preservation of existing endpoints.

Next step:
- Review W8 and integrate through its issue-linked PR into `develop` after W0.
- W9/W13 can inject the real planner, current-authority snapshots, grant resolver and executor via `PlanExecuteService`; no production implementations are fabricated by this boundary.

Open risk or decision:
- Default app returns typed 503 for these endpoints until dependencies are explicitly injected.
- In-memory reservations are bounded and never evicted to permit replay. Capacity exhaustion fails closed. Multi-worker/restart coordination and durable deduplication need W13 integration before production activation.
- W0 DTOs and shared fixtures are unchanged. Spring's linked design was read, but new path/scope/deadline/response-wrapper choices still require Spring adoption; cross-repository conformance has not been claimed.
- Trusted grant resolver must fail for revoked/unknown references; Spring retains grant issuance, lookup receipts, authority gate, and final publication. Async dependencies must honor deadline cancellation.

Ad hoc requests captured this session:
- Implement W8/#8 with strict TDD, side-effect-free rejection, focused/full checks, self-review, and a reviewable commit.
