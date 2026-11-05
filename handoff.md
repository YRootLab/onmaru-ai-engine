# Handoff

Current work:
- Summary: W17 deterministic offline RAG replay and release gates are implemented on W16.
- Issue: [W17 #16](https://github.com/YRootLab/onmaru-ai-engine/issues/16), under AI-RAG Root #3.
- Branch: `feature/ai-rag-w17`, based on reviewed `feature/ai-rag-w16`.

Touched files:
- `src/onmaru_ai/evals/rag.py`: closed replay/report models, stage and place metrics, route/claim/safety gates, canonical report hash.
- `tests/evals/rag/`: deterministic replay, first-loss, hard violation, claim, and run completeness tests.
- `scripts/run-rag-evals`: report writer with nonzero exit for failed gates.

Verification:
- TDD RED: focused collection failed because the W17 replay module did not exist.
- Focused pytest: 5 passed. Full pytest: 633 passed, 1 skipped.
- Ruff, strict mypy, and `git diff --check` pass.

Integration limits:
- Development data can produce metrics but never `promotionEligible=true`; all cases must be sealed and every gate must pass.
- W22 supplies the reviewed 200/100 dataset. W21 connects real engine artifacts and sealed release evidence.
- Hard filter, rights, revocation, source-scope, and unsupported-claim violations block the safety gate on the first occurrence.

Next step:
- Parent reviews and opens the W17 stacked PR after W16 integration.
