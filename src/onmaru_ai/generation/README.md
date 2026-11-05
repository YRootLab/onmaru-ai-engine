# Evidence-limited generation (W12)

`EvidenceGenerator.generate(GenerationInput, timeout_seconds=...)` returns a
`GenerationResult` with a W0 `ValidatedProposal` and an optional typed fallback.
It calls the existing Gemini adapter's unary API exactly once after input checks,
with search grounding disabled. No retry, stream, progress payload, retrieval,
HTTP endpoint, publication or citation renderer is installed here.

## Trusted inputs and conservative support

W0 `EvidenceSet` contains IDs and offsets, not source text or semantic support.
The caller must supply the approved plan, current authority versions/revocations,
canonical source documents and **server-reviewed atomic facts** from its trusted
registry. These are local inputs, not additional fields on W0 wire contracts.
An LLM must never create or certify `verifiedFacts`; arbitrary chunk text cannot
be promoted into a reviewed fact. W13 must resolve these inputs and retain their
review provenance. Until a reviewed fact is available, `NO_SUPPORTED_FACTS`
skips the provider.

The validator checks run/plan/current versions, revocations, permitted places,
source identity/revision/corpus, source offsets, unique IDs and every cited span.
Offsets are Python Unicode code-point offsets with an exclusive end; registry
producers must convert byte/UTF-16 offsets before construction. A reviewed fact's
text must exactly equal **every** cited source span. `timeScope` is either the
literal qualifier included in that text or `TIMELESS`; historical facts should
use their explicit historical qualifier. Verified relations include an immutable
relation ID, subject, predicate, object and polarity, and must involve the claim's
place. `PREFERENCE` and `INTERPRETATION` have distinct reviewed support types.

This is deliberately narrow: model paraphrases, assembled multi-span claims,
comparisons, time shifts, negation changes and stronger relation claims are held.
The model selects approved facts and copies their text/kind/evidence IDs exactly.
It cannot establish semantic truth. Even an exact quotation can be wrong in its
source; human review and canonical registry provenance remain required. Numeric,
name, negation, relation and time changes fail exact matching rather than passing
on keyword overlap. Conditional tone and atomicity are review responsibilities;
code additionally rejects multiple punctuated sentences and unsafe formatting.

Only structured operation/approved filters, evidence metadata and reviewed facts
reach the provider. Query text and full documents stay local. The fixed policy
treats evidence as untrusted data and forbids added facts or instructions. The
closed provider schema has only `places` and `summaryClaims`; claim-local
`factId` binds to the registry and is stripped from the W0 proposal. Output is
bounded to five places, 24 claims, 1000 characters per claim and 6000 total claim
characters. HTML, encoded markup, Markdown, URLs and control characters fail
closed. Missing/unsupported claims are held; empty cards and summaries for
removed places are dropped. Structural corruption rejects the whole output.

## Fallback and integration

- `NO_EVIDENCE`, `NO_SUPPORTED_FACTS`, `INVALID_EVIDENCE`: zero provider calls.
- `PROVIDER_TIMEOUT`, `PROVIDER_RATE_LIMITED`, `PROVIDER_UNAVAILABLE`: one call,
  empty proposal, no provider body/error text and no retry.
- `INVALID_OUTPUT`: one call, no valid claims or a malformed/unsafe response.
- `CANCELLED`: adapter cancellation failure; task cancellation propagates normally.

All fallback proposals are empty. W13 must branch on `fallback`, especially for
stale authority: the internal failure envelope may carry the current watermark
that differs from the approved run, and is not a publishable success artifact.
Spring must recheck current eligibility/revocations immediately before publication.
Small supported results remain small; this module never fills missing cards.

`tests/generation/fixtures/` provides synthetic acceptance/rejection samples for
human review. The valid sample says only that the house was built in 1920; samples
that negate this, substitute 1930, or invent a filming relation must be rejected.
These fixtures and automated checks do not substitute for the sealed two-person
semantic-support evaluation required by the design documents.
