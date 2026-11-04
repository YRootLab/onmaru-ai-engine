# Handoff

Current work:
- Summary: W0 fixes seven private AI↔Spring versioned DTOs, schemas, authority/hash checks, and portable accepted/rejected fixtures.
- Issue/PR: [W0 Issue #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4), under AI-RAG Root Issue #3. No W0 PR opened in this implementation task.
- Branch: `feature/ai-rag-w0`, isolated worktree `.worktrees/feature-ai-rag-w0`.

Touched files:
- `src/onmaru_ai/contracts/`: frozen closed models, JSON schemas, authority/hash validation, contract and fixture instructions.
- `tests/contracts/`: synthetic shared fixtures and schema/model/context validation tests, including both review rounds: authority/vocabulary, claim kind/evidence caps, strict publicOnly and clarification-pair cases.
- `docs/ai-rag/progress-event-contract.md`: implemented private payload references; Spring receiver/public SSE remains future work.

Verification:
- TDD RED: initial 15 focused tests failed because the package did not exist; Fix Round 1 added 28 expected failures reproducing empty-scope artifact acceptance, failure-stage vocabulary mismatch and open code vocabularies. Final review fix added 29 expected failures for claim kinds/counts, strict publicOnly and clarification pair mapping.
- GREEN: `uv run pytest tests/contracts -q` → 259 passed; `uv run pytest -q` → 564 passed, 1 skipped (opt-in live provider test); `uv run ruff check src tests scripts` → passed; `uv run mypy` → no issues in 69 source files.

Next step:
- Review W0 against Issue #4 and open its PR into `develop` after reconciling logs and verification.
- Share the pinned schema/fixture files with Spring CI. No cross-repository import has been performed or claimed.

Open risk or decision:
- Spring must adopt the documented canonical SHA-256 serialization, fixed reason/question IDs, `questions-1` dictionary and fixture validation stages.
- W0 has no HTTP endpoint, progress transport, public SSE serializer, retrieval executor, or publication authority.
- Inclusion filter `null` means unrestricted public scope; `[]` means deny all. Approval must exactly echo the proposed narrowed filters.

Ad hoc requests captured this session:
- Implement W0/#4 as the foundation for later AI-RAG issues, with focused TDD, full checks, and a reviewable commit.
