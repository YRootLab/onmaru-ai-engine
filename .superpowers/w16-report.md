# W16 / Issue #11 implementation report

Branch: `feature/ai-rag-w16`, based on reviewed W0 contracts.

Implemented:

- Portable closed JSON Schema 2020-12 dataset/case v1: source/corpus hashes, source
  revision and Unicode code point offsets, five W0 routes plus clarification,
  W0 QuestionFrame/ConfirmedContext, pinned questions-1, tags/split, graded
  places/evidence, minimum claims, expression preservation and semantic expectations.
- Executable `scripts/lint-rag-gold`: schema validation; canonical gold content
  hash; two distinct reviewer decisions; completed agreement/third-person
  adjudication; evidence/claim/span/allowlist checks; revision hash consistency;
  unique query IDs and dataset version; cross-file split leakage on same canonical
  place OR same source ID/revision. Diagnostics do not print question/source text.
- Three small synthetic valid/invalid fixtures; provenance/hash/version workflow,
  release manifest and sealed access rules. No production labeling, runner,
  collection, deployment or database changes.

TDD evidence:

- RED: `uv run pytest tests/evals/rag_gold -q` → 56 failed because schema and
  executable were absent (no collection/import errors).
- GREEN: initial implementation → 56 passed.
- Additional RED: route semantic-query presence boundary → 6 failed, 58 passed.
- Final focused GREEN: 64 passed.

Verification:

- `uv run pytest tests/evals/rag_gold -q` → 64 passed.
- `uv run pytest -q` → 628 passed, 1 skipped (existing opt-in live provider test).
- `uv run ruff check src tests scripts` → all checks passed.
- `uv run mypy src tests scripts/lint-rag-gold` → no issues, 71 source files.
- `git diff --check` → passed.
- Direct executable invocation and invocation from another working directory pass.

Self-review:

- Checked Issue acceptance criteria, portable W0 shape/route parity, executable
  mode, semantic hash/review binding, source offset boundaries and multi-file
  grouping. Source-free unanswerable cases and same-split variants are supported.
- Schema validation alone cannot express independent-review/offset/leakage
  relationships; docs require executable lint for release inputs.
- Source/corpus fixture hashes and reviewer identities are explicit synthetic
  placeholders. Linter checks format and internal consistency, not actual snapshot
  bytes, public rights, human independence or sealed ACLs. Those responsibilities
  are documented for the dataset owner; no claim of actual evaluation quality.
- Both split files must be supplied together in a restricted evaluation job. A
  single-split invocation cannot detect overlap with files not supplied.
- No outstanding implementation concern found in the scoped self-review.

Integration: parent reviews the commit and opens an Issue #11 PR into `develop`;
no push, PR, Issue closure or merge performed by this worker.
