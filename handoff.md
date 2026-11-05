# Handoff

Local integration base for W4/W5/W6 only:
- Combines reviewed W2 normalization/chunking and W3 PostgreSQL corpus persistence.
- Parent PRs are #37 and #33; this branch must not be pushed or merged directly.
- Child work remains stacked until both dependency chains reach `develop`.

W6 implementation for Issue #13:
- Added ordered revocation ingestion with duplicate conflict detection, 60-second heartbeat
  freshness, atomic active watermark advancement, and fail-closed restore reapplication.
- Added revocation-first candidate blocking followed by bounded physical removal from every
  active, rollback, and staging revision.
- Added bounded corpus GC with active/two-rollback/hold/sync/read-lease protection, durable
  stage checkpoints, row/byte audit evidence, and protection rechecks before every batch.
- Verified 42 PostgreSQL 17 + pgvector storage/lifecycle tests, 612 repository tests
  (42 skipped without the explicit disposable DSN), Ruff, strict mypy, and diff checks.
- Work remains local on `feature/ai-rag-w6`; it depends on W2/W3 integration and is not a
  standalone merge target until parent dependency PRs land.
