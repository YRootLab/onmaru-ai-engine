# Handoff

Current work:
- Summary: W1 public projection manifest intake and source eligibility validation implemented from the reviewed W0 head; awaiting parent review and integration.
- Issue/PR: [W1 Issue #5](https://github.com/YRootLab/onmaru-ai-engine/issues/5), under AI-RAG Root Issue #3; dependency [W0 #4](https://github.com/YRootLab/onmaru-ai-engine/issues/4).
- Branch: `feature/ai-rag-w1`, isolated worktree `.worktrees/feature-ai-rag-w1`.

Touched files:
- `src/onmaru_ai/corpus/source_sync.py`: closed immutable manifest/tombstone models, idempotent preparation-only intake, hash/revision/count/duplicate/order checks, contiguous tombstone watermark handling.
- `src/onmaru_ai/corpus/source_policy.py`: public/license/eligibility/revocation and source-specific preparation gates.
- `tests/corpus/source_sync/`: fixed signed public fixture, 33 focused cases, interface and canonicalization notes.

Verification:
- TDD RED: 33 focused failures because `source_sync` was absent; corrected a local fixture setup command before recording the final RED run.
- GREEN: `uv run pytest tests/corpus/source_sync -q` → 33 passed; `uv run pytest -q` → 597 passed, 1 skipped (opt-in live provider test).
- `uv run ruff check src tests scripts` passed; `uv run mypy` → no issues in 72 source files; `git diff --check` passed.

Next step:
- Parent review W1 against Issue #5 acceptance criteria; open an Issue-linked PR into `develop` following the W0 dependency integration strategy.
- W2 can consume `prepared_documents`; W6 must implement durable revocation state, runtime blocking/freshness, rollback and restore behavior.

Open risk or decision:
- Intake is serial and process-local; a new receiver requires history from sequence 1. Durable watermark/checkpoint state is not claimed.
- The synthetic private manifest shape is documented with its fixture; Spring generation and cross-repository contract adoption remain separate.
- Existing REST/sync activation is not wired to this preparation boundary and is unchanged. There is no DB access, content fetch, normalization, chunking or activation here.

Ad hoc requests captured this session:
- Implement W1/#5 in its isolated branch with strict TDD, focused/full checks, self-review and a reviewable commit; keep later W2/W6 features outside this change.
