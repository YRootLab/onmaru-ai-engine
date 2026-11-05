# Handoff

Current work:
- Implement W3 AI-owned PostgreSQL corpus storage and atomic revision activation.
- Issue: https://github.com/YRootLab/onmaru-ai-engine/issues/6 (depends on reviewed W0/#4).
- Branch: `feature/ai-rag-w3`; isolated worktree `.worktrees/feature-ai-rag-w3`.

Ad hoc request:
- Use strict TDD, local PostgreSQL integration where available, full pytest/Ruff/mypy and self-review; commit with #6.

Scope:
- AI schema migrations, immutable revision/document/chunk/vector metadata, CAS activation, two rollback candidates, consistent corpus/config/revocation read snapshot.
- Spring schema and production DB image are outside this change. Existing memory baseline remains separate.

Verification:
- TDD RED reproduced 16 storage, activation, rollback, constraint, and snapshot failures before implementation.
- Disposable PostgreSQL 17 + pgvector integration: 32 passed.
- Full suite with the integration database: 596 passed, 1 skipped.
- Ruff, strict mypy, and `git diff --check` pass.

Next step:
- Parent reviews the W3 commit and prepares its stacked PR after W0 integration.
- Production must provision separate migration, sync, and runtime roles before wiring this store.
