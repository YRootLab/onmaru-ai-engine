# Handoff

Local integration base for W4/W5/W6 only:
- Combines reviewed W2 normalization/chunking and W3 PostgreSQL corpus persistence.
- Parent PRs are #37 and #33; this branch must not be pushed or merged directly.
- Child work remains stacked until both dependency chains reach `develop`.

W5 / Issue #19 implementation:
- Added deterministic Korean query normalization, BM25 scoring, exact/prefix name ordering,
  active snapshot hard filters, and closed lexical `CandidateSet` output capped at 20.
- Added a PostgreSQL snapshot repository that fails closed when `pg_search` is unavailable.
- Focused lexical tests: 12 passed. Full suite: 624 passed, 32 skipped because optional
  PostgreSQL/live-provider environments were not configured.
- Operational `pg_search` image/version/license/index DDL and reviewed-alias persistence remain
  explicit BE/environment gates; see `docs/ai-rag/lexical-search-implementation.md`.
