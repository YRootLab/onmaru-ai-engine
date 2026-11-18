# Plan/Execute corpus and reviewed-fact preparation

## Goal

Make staging corpus preparation and reviewed-fact loading reproducible without allowing accidental hash embeddings, implicit activation, or unreviewed facts to become production evidence.

## Approved design

The corpus ingestion CLI must require a real Gemini API key unless the operator explicitly selects local hash-only mode. Hash-only output must carry a distinct non-semantic profile and must not be staged. The CLI stages a new revision only; a separate activator defaults to read-only validation and requires both `--apply` and exact revision confirmation after profile, count, and revocation checks.

A separate reviewed-fact loader consumes UTF-8 JSONL rows that already contain editorial approval metadata. It defaults to read-only validation. Only an explicit `--apply` may insert rows in one database transaction, after validating active revision, source public place ID, chunk ownership/bounds, exact source text offsets, unique fact IDs, safe atomic text, revocation state, and approval metadata. The loader records supplied review metadata and never creates, edits, or approves facts. Runtime remains read-only.

The work does not connect to staging/production, apply migrations, generate facts, decide whether a fact is true, or change feature flags. Those actions require the repository owner’s separately operated staging workflow and content review.

## Components and verification

- Harden both corpus ingestion CLIs and tests to fail closed when Gemini credentials are missing, while preserving explicit local hash-only dry-run behavior under a distinct profile; remove activation from ingestion.
- Add `scripts/activate_corpus_revision.py` for separate read-only candidate checks and explicit confirmed activation.
- Add a reviewed-fact JSONL model/validator and `scripts/load_reviewed_facts.py` with dry-run default and transactional `--apply`.
- Add unit tests for malformed/unapproved facts, stale revisions, incorrect spans, duplicates, no-write dry-run, and transaction rollback; run focused and full repository checks.
- Document command inputs, required role grants, and staging-only operation in the Plan/Execute runbook.
