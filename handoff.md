# Handoff

Local integration base for W4/W5/W6 only:
- Combines reviewed W2 normalization/chunking and W3 PostgreSQL corpus persistence.
- Parent PRs are #37 and #33; this branch must not be pushed or merged directly.
- Child work remains stacked until both dependency chains reach `develop`.

W4 / Issue #18 implementation:
- Added the commit-pinned 384-dimensional multilingual E5 adapter with distinct passage/query
  prefixes, strict profile/dimension/finiteness/norm checks, bounded batches, timeout handling,
  process-local online/batch admission, and cold/warm latency plus RSS samples.
- Added exact cosine pgvector search through the W3 repeatable-read `CorpusSnapshot`, with active
  revision/profile/public/revocation/hard filters, deterministic chunk tie-breaking, top-20 cap,
  and fail-closed result validation.
- The actual model runtime remains an injected backend. Deployment must package the pinned artifact
  and use shared admission if it runs multiple AI worker processes.
- Verification: 18 focused tests; full suite, Ruff, strict mypy, and diff check recorded at commit.
