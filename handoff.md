# Handoff

Current work (v0.1.2 contract alignment):
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
- `docs/ai-rag/progress-event-contract.md`: W14 implementation boundary and W13 integration handoff.

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
