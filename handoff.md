# Handoff

Current work:
- Summary: W9 grant-only Spring `PlaceQueryPort` REST adapter implemented on the reviewed W0/W8 contract foundation.
- Issue: [W9 #14](https://github.com/YRootLab/onmaru-ai-engine/issues/14), under AI-RAG Root Issue #3; dependencies [W0 #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4) and [W8 #8](https://github.com/YRootLab/onmaru-ai-engine/issues/8).
- Branch: `feature/ai-rag-w9`, isolated worktree `.worktrees/feature-ai-rag-w9`.

Touched files:
- `src/onmaru_ai/adapters/spring_place.py`: fixed HTTPS route, opaque-grant-only request, bounded single-attempt execution, closed projection/result models, exact plan/revocation binding, and typed fallback outcomes.
- `src/onmaru_ai/adapters/__init__.py`: public adapter types for W13 orchestration injection.
- `tests/adapters/spring_place/`: route eligibility, exact outbound payload, timeout/error/fallback, concurrency, projection allowlist, stale response, size and schema rejection tests.

Verification:
- TDD RED: focused suite initially failed during collection because `onmaru_ai.adapters` did not exist; the first implementation then exposed alias-construction and projection-test errors before correction.
- GREEN: 25 focused adapter tests; full `uv run pytest -q` → 642 passed, 1 skipped (opt-in live provider smoke test).
- `uv run ruff check src tests scripts`, strict `uv run mypy` (76 source files), and `git diff --check` passed.
- Pytest reports two upstream FastAPI/Starlette TestClient deprecation warnings; no application warning or failure.
- Self-review checked zero calls for retrieval-only routes, reservation before network await, no retry after timeout/error, exact grant-only JSON, no query/filter/member/SQL fields, response caps, approved projection subset, plan hash and revocation sequence binding, and sanitized errors.

Next step:
- Review W9 and integrate through its issue-linked PR into `develop` after W0/W8.
- W13 injects this adapter into `ApprovedPlanExecutor`; Spring adopts the fixed REST path and shared response fixture before production activation.

Open risk or decision:
- The fixed REST path `/internal/v1/ai/place-query/lookup` and `journey.lookup.result.v1` envelope require Spring implementation and cross-repository fixtures; no Spring endpoint exists yet.
- W0 currently approves four canonical fields, while the Spring design catalog lists additional mandatory display projections and names `PUBLICATION_STATUS` differently. W9 fails closed on any projection outside the W0 approved set. The shared contract must reconcile that drift before integration.
- Per-process attempt reservation prevents duplicate calls inside one adapter instance. Spring still owns durable grant consumption/idempotent receipts across workers and restarts.
- W13 must supply lifecycle management, production service credentials and parent deadline propagation; this adapter caps its own timeout at five seconds and performs no retry.

Ad hoc requests captured this session:
- Implement W9/#14 with strict TDD, grant-only fixed REST, bounded single-call semantics, typed fallback, full verification, and a reviewable commit.
