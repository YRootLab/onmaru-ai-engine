# Handoff

Current work:
- Summary: W2 public-body normalization and paragraph-first chunk enrichment implemented on the reviewed W0/W1 contract foundation; awaiting parent review and integration.
- Issue/PR: [W2 Issue #12](https://github.com/YRootLab/onmaru-ai-engine/issues/12), under AI-RAG Root Issue #3; dependency [W1 #5](https://github.com/YRootLab/onmaru-ai-engine/issues/5).
- Branch: `feature/ai-rag-w2`, isolated worktree `.worktrees/feature-ai-rag-w2`.

Touched files:
- `src/onmaru_ai/corpus/normalizer.py`: executable markup removal, NFC/space normalization, original-body offset map, and an explicit untrusted-source data envelope.
- `src/onmaru_ai/corpus/chunker.py`: W1 eligibility gate, document-boundary chunking, 400 target/600 maximum/60 overlap defaults, deterministic IDs/hashes, and corpus/source/place/revision metadata.
- `tests/corpus/chunking/`: Korean paragraphs, long boundaries, overlap, HTML and role-disguise injection, unclosed executable elements, Unicode offsets, traceability, and fail-closed fixtures.

Verification:
- TDD RED: focused collection failed because `onmaru_ai.corpus.chunker` did not exist.
- GREEN: `uv run pytest tests/corpus/chunking -q` → 14 passed; `uv run pytest -q` → 611 passed, 1 skipped (opt-in live provider test).
- `uv run ruff check src tests scripts` passed; `uv run mypy` → no issues in 75 source files; `git diff --check` passed.

Next step:
- Parent review W2 against Issue #12 acceptance criteria; open an Issue-linked PR after W1 dependency integration is available.
- W4/W5 can consume `SourceChunk`; persistence and embedding/index adapters remain separately owned.

Open risk or decision:
- The initial deterministic token-count profile is whitespace based and recorded in `chunkerVersion`; W4 must introduce a new version and reindex if the pinned embedding tokenizer becomes the shared chunk budget authority.
- HTML bodies are handled locally and never fetched by this module. Transport, download limits, document-hash verification, persistence, activation, and revocation runtime enforcement remain outside W2.
- Source offsets refer to the received body. Entity decoding and Unicode composition retain an enclosing source range, which can be wider than one normalized character.

Ad hoc requests captured this session:
- Implement W2/#12 in its isolated branch with strict TDD, focused/full checks, self-review and a reviewable commit; keep embedding and DB storage outside this change.
