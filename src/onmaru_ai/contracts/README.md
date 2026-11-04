# AI ↔ Spring private contracts (W0 / #4)

These frozen Pydantic v2 models and [JSON Schemas](schemas/) pin the private
plan/approval/artifact/progress boundary. They do not install endpoints, execute
retrieval, authorize publication, or implement Spring public SSE.

| Model | `schemaVersion` |
| --- | --- |
| SafeQueryRequest | `ai-safe-query.v1` |
| PlanProposal | `ai-plan-proposal.v1` |
| ApprovedQueryPlan | `ai-approved-plan.v1` |
| CandidateSet | `ai-candidate-set.v1` |
| EvidenceSet | `ai-evidence-set.v1` |
| ValidatedProposal | `ai-validated-proposal.v1` |
| ProgressEvent | `ai-progress.v1` |

Plan/approval also carry `planVersion: ai-query-plan.v1`. All wire keys are
camelCase. All declared fields are required, including nullable fields. All
objects reject additional fields, including nested objects. Raw member data,
raw questions/conversations, model tokens, prompts, source bodies, and reasoning
have no fields. `safeQuery` and `semanticQuery` are sanitized, transient inputs;
the DTOs do not perform Spring's redaction, or permit logging these values.
Evidence carries source revision and offsets, never source body. Claim text is a
proposal requiring later grounding and Spring final validation. The authoritative
[grounding contract](../../../docs/ai-rag/grounding-and-review.md) fixes `Claim.kind`
to `FACT`, `INTERPRETATION`, `PREFERENCE`, or `CONNECTOR`. Every reason/summary
claim references one to three unique evidence IDs; the whole `EvidenceSet`
retains its separate twelve-record cap.

`SQL_ONLY` uses mode `NONE`; the three retrieval-only routes use their matching
mode; `SQL_PLUS_RETRIEVAL` uses `LEXICAL_ONLY`, `DENSE_ONLY`, or `HYBRID`.
`CLARIFY_OR_SCOPE` uses mode `NONE` and a reason plus fixed `questionCode` for
Spring's renderer. It carries no semantic query or canonical field requests.
The callback ordinal starts at one; duplicate/order/terminal delivery semantics
belong to the future Spring receiver and progress adapter.

## Validation order and authority

1. Validate payload against the matching JSON Schema / Pydantic model.
2. For a proposed plan, call `validate_plan(request, proposal, current_versions=...)`.
3. For approval/execute, call `validate_approval(request, proposal, approved, current_versions=...)`.
4. For candidate/evidence/proposal output, call `validate_artifact` with the approved
   plan, current versions and current revoked `(sourceId, sourceRevision)` pairs.
   A validated proposal also requires its `EvidenceSet` registry. Progress checks
   only run/hash; it has no version fields and does not advance authority state.

Schema validation alone cannot compare documents or recompute cryptographic
hashes. The Python checks enforce run ID, corpus/config/dictionary/revocation
version equality, canonical-field authority, filters and hash binding. No stale
watermark is automatically accepted. A caller may perform a separate current
eligibility recheck in a later execution layer. The W0 validator fails closed.
Source revision checks use the supplied current revocation registry; they do not
fetch that registry or infer source eligibility from an arbitrary revision ID.

For inclusion filters (`placeIds`, `regionCodes`, `categoryCodes`), `null` means
unrestricted within public authority and `[]` means an empty permitted set.
Any empty inclusion filter forbids nonempty candidate/evidence/proposal output,
including when place IDs are otherwise unbounded. Empty result artifacts remain
valid. A proposal may narrow an inclusion set; it may not replace a bounded set with
`null`. All mandatory pins and exclusions in the authority must survive the
proposal. Pins must remain included and cannot be excluded. `publicOnly` is
always the actual JSON boolean `true`; numeric `1`/`1.0` and other coerced
values are rejected by Pydantic as well as JSON Schema. `filterHash` is Spring's
authority-bound hash and must echo it.
Canonical field IDs are `PUBLIC_ADDRESS`, `REGION_CODE`, `CATEGORY_CODE`, and
`PUBLIC_STATUS`; Spring additionally supplies the allowed subset per request.
The approved filters must equal the proposed filters exactly, including array
order and `filterHash`. Narrowing at approval requires a new proposal/hash.
All other execution-affecting approval echoes must also equal the proposal.

The limits are fixed at `bm25K=20`, `vectorK=20`, `rerankK=30`, `evidenceK=12`,
`maxPlaces=5`. Retrieval expressions allow four positive concepts, two negative
concepts, and two public entity IDs. Concept/ID arrays reject duplicates;
producers supply dictionary-order arrays. Semantic queries are at most 240
Unicode code points. An evidence set has at most twelve chunks and two per
place, with at most five allowed places. Candidate lists enforce twenty for
individual retrieval stages and thirty for fusion/reranking.

## Closed code vocabularies

[`vocabulary.py`](vocabulary.py) pins machine-readable enums; their literal values
are also exported in the generated schemas. The currently registered dictionary
`questions-1` contains the twenty searchable explanation-focus, topic, companion,
and atmosphere codes from the [initial design table](../../../docs/ai-rag/question-understanding.md).
Operation codes remain the separate `questionFrame.operation` enum; condition
operations use structured filters, and canonical fact fields have their own enum.

Concepts are closed in JSON Schema and Pydantic. `validate_plan` additionally
looks up the specified dictionary version and checks every frame/positive/negative
concept against that version's registered set. Echoing an unregistered dictionary
version consistently still fails `VERSION_MISMATCH`. Adding concepts requires a
new registered dictionary version and matching closed schema/fixture updates;
provider strings cannot extend the dictionary.

The design describes route/clarification cases without assigning wire literals
for reason/question codes. W0 pins the following fixed IDs for those cases:

| Design case | `reasonCodes` ID | Clarification `questionCode` |
| --- | --- | --- |
| Registered canonical facts only | `CANONICAL_FACT_ONLY` | — |
| Exact public name/term | `EXACT_PUBLIC_TERM` | — |
| Single semantic topic | `SINGLE_SEMANTIC_TOPIC` | — |
| Composite retrieval query | `COMPOSITE_QUERY` | — |
| Canonical fact plus retrieval | `CANONICAL_FACT_WITH_RETRIEVAL` | — |
| Ambiguous target | `AMBIGUOUS_TARGET` | `CHOOSE_TARGET` |
| Conflicting conditions | `CONFLICTING_CONDITIONS` | `RESOLVE_CONDITIONS` |
| Unsupported scope | `UNSUPPORTED_SCOPE` | `SUPPORTED_TRAVEL_SCOPE` |
| Lost input meaning | `SEMANTIC_LOSS` | `PRESERVE_MEANING` |

Each clarification reason must use the corresponding question code in this
table; mismatched pairs are rejected by both JSON Schema and Pydantic.
Unknown uppercase strings are rejected. New fixed reason/question IDs require a
versioned plan-contract update rather than a regex-only extension.

`ValidatedProposal.failureStage` uses its own `FailureStage` enum from the
[request lifecycle failure table](../../../docs/ai-rag/request-lifecycle.md):
`REQUEST`, `INTERPRETATION`, `PLANNING`, `ROUTING`, `QUOTA`, `RETRIEVAL`,
`RETRIEVAL_EMPTY`, `GENERATION`, `VALIDATION`, `DELIVERY`, or null. Progress stage
values such as `RETRIEVING` and `GENERATING` are rejected in this field. Keeping
these vocabularies distinct does not authorize FastAPI to perform Spring-owned
request/quota/delivery actions.

## Canonical `planHash` algorithm

Spring and AI must implement these exact steps; accepted fixtures pin literal
expected hash values independently of the Python hash implementation.

1. Take the complete PlanProposal wire object with all required nullable fields.
2. Remove `planHash` and `semanticQuery`. Add `semanticQueryHash`, whose value is
   `null` for a null query, otherwise `sha256:` plus lowercase SHA-256 hexadecimal
   of the exact UTF-8 query bytes. Do not trim or normalize Unicode.
3. Serialize this object recursively with keys sorted lexicographically, no
   whitespace, commas/colons as separators, JSON null/true/false, and Unicode
   characters unescaped (normal JSON escaping for quotes, backslash and control
   characters). Preserve array order. This plan contains no floating point
   values; version sequences and limits serialize as decimal integers.
4. Hash those UTF-8 bytes with SHA-256 and prefix the lowercase hex with `sha256:`.

Equivalent Python serialization is `json.dumps(body, ensure_ascii=False,
sort_keys=True, separators=(",", ":"))`. The hash binds the schema/plan versions,
run, route/mode, reason/clarification codes, frame/expression, fields, filters,
limits, all version echoes and the semantic query digest. It is an integrity
binding, not a signature or bearer authority.

## Shared fixtures and schema regeneration

[Portable fixtures](../../../tests/contracts/fixtures/) are individual JSON
objects containing `name`, `model`, full `payload`, `schemaValid`, `expected`,
and, for contextual validation, a full `context`. `context` supplies `request`,
`proposal`, `approved`, `currentVersions`, `revokedSources`, and `evidence`.
These wrappers are test artifacts, not additional runtime DTOs.

The expected stages are:

- `schemaValid: false`: JSON Schema and Pydantic must reject the wire shape.
  `VERSION_MISMATCH` and `UNEXPECTED_FIELD` describe the reason at this layer.
- `schemaValid: true, expected: INVALID_PAYLOAD`: JSON Schema accepts the shape;
  Pydantic must reject a relational invariant such as overlapping concepts or
  more than two evidence chunks for a place.
- Other cases: parse the DTO, then run the appropriate contextual validator.
  It must accept `ACCEPT` or reject with the exact `ContractViolation.code`.

Copy schemas and fixtures unchanged to Spring CI; implement the same validation
stages there. This repository verifies them locally and does not claim that
Spring has imported or accepted them yet. Fixture data is synthetic.

Run `uv run pytest tests/contracts`. To regenerate schemas from model sources:

```sh
uv run python - <<'PY'
import json
from pathlib import Path
from onmaru_ai.contracts import CONTRACT_MODELS
root = Path('src/onmaru_ai/contracts/schemas')
for name, model in CONTRACT_MODELS.items():
    schema = model.model_json_schema(by_alias=True)
    (root / f'{name}.schema.json').write_text(json.dumps(schema, indent=2) + '\n')
PY
```
