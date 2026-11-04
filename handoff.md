# Handoff

Current work:
- Summary: W0 implementation and review are complete; prepare its `develop` PR and start dependency-safe Wave 1 branches from the reviewed W0 head.
- Issue/PR: [W0 Issue #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4), under AI-RAG Root Issue #3.
- Branch: `feature/ai-rag-w0`, isolated worktree `.worktrees/feature-ai-rag-w0`.

Touched files:
- `src/onmaru_ai/contracts/`: frozen closed models, JSON schemas, authority/hash validation, contract and fixture instructions.
- `tests/contracts/`: synthetic shared fixtures and schema/model/context validation tests, including both review rounds: authority/vocabulary, claim kind/evidence caps, strict publicOnly and clarification-pair cases.
- `docs/ai-rag/progress-event-contract.md`: implemented private payload references; Spring receiver/public SSE remains future work.

Verification:
- TDD RED: initial 15 focused tests failed because the package did not exist; Fix Round 1 added 28 expected failures reproducing empty-scope artifact acceptance, failure-stage vocabulary mismatch and open code vocabularies. Final review fix added 29 expected failures for claim kinds/counts, strict publicOnly and clarification pair mapping.
- GREEN: `uv run pytest tests/contracts -q` → 259 passed; `uv run pytest -q` → 564 passed, 1 skipped (opt-in live provider test); `uv run ruff check src tests scripts` → passed; `uv run mypy` → no issues in 69 source files.

Next step:
- Open the W0 PR into `develop`; then begin W1, W3, W7, W8, W12, W15, and W16 only from this reviewed contract head.
- Share the pinned schema/fixture files with Spring CI. No cross-repository import has been performed or claimed.

Open risk or decision:
- Spring must adopt the documented canonical SHA-256 serialization, fixed reason/question IDs, `questions-1` dictionary and fixture validation stages.
- W0 has no HTTP endpoint, progress transport, public SSE serializer, retrieval executor, or publication authority.
- Inclusion filter `null` means unrestricted public scope; `[]` means deny all. Approval must exactly echo the proposed narrowed filters.

Ad hoc requests captured this session:
- Implement W0/#4 as the foundation for later AI-RAG issues, with focused TDD, full checks, and a reviewable commit.
- Continue the GitHub AI-RAG issue graph and parallelize dependency-safe work.

## W7 implementation

- Request: implement deterministic normalization, interpretation, and route proposals for [Issue #7](https://github.com/YRootLab/onmaru-ai-engine/issues/7).
- Branch/worktree: `feature/ai-rag-w7`, `.worktrees/feature-ai-rag-w7`, based on reviewed W0 contracts.
- Scope: `src/onmaru_ai/query/`, route gold fixtures, provider call counters; no approved execution or Spring state.
- Verification: 85 focused tests and 649 full tests passed with 1 existing opt-in live-provider skip; Ruff, mypy, and diff check passed.
- Next: review and open a stacked PR on W0; after W0 merges, retarget to `develop`.
