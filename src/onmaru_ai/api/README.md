# Private plan/execute boundary (W8 / #8)

`create_app(plan_execute_service=...)` installs these endpoints alongside the
existing proposal and corpus APIs. Without an explicitly injected service they
fail closed with 503 after authentication and contract validation.

| Endpoint | Required Spring token scope | Request | Response |
| --- | --- | --- | --- |
| `POST /internal/v1/journey/plan` | `journey.plan:write` | W0 `SafeQueryRequest` | W0 `PlanProposal` |
| `POST /internal/v1/journey/execute` | `journey.execute:write` | W0 `ApprovedQueryPlan` | `ExecutionResult` |

The existing HS256 verifier requires issuer `onmaru-spring`, subject `spring-api`,
audience `onmaru-ai`, valid expiry/signature, and exactly the operation scope.
Legacy `journey.proposal:write` does not authorize these new operations. Deployment
must keep the endpoints on the private network/TLS boundary described in the
repository design; this module does not configure ingress.

Both requests require `X-Run-Id` equal to the body UUID, a bounded
`X-Request-Id`, a valid version-00 W3C `traceparent`, and timezone-aware ISO-8601
`X-Deadline-At`. Trace IDs must remain equal across the two calls; span IDs and
request IDs may differ. Each operation is limited by the deadline and a local
30-second ceiling. Execute cannot extend the original planning deadline.
Responses, including errors, set `Cache-Control: no-store`.

The W0 payloads and fixture files are consumed without conversion. The response
wrapper `ai-execute-result.v1` has required `runId`, `planHash`, `versions`,
`proposal: ValidatedProposal | null`, and `evidence: EvidenceSet | null`. Returning
artifacts does not publish them; Spring retains final validation and persistence.
Artifact run/hash/version/filter/evidence bindings are validated before response.
The injected current-version provider must supply an authoritative, fresh corpus,
config, dictionary, and revocation watermark. It must fail when freshness cannot
be established. A changed watermark rejects execution and stale results.

All errors have closed shape `{schemaVersion: "ai-boundary-error.v1", code}`;
no request text or dependency exception detail is included. Authentication uses
the existing `INTERNAL_AUTH_*` codes and 401/403. Malformed contracts/correlation
use 422, missing/mismatched/consumed plans use 409, rejected grants use 403,
deadlines use 504, and unavailable dependencies or capacity use 503. W0
`ContractViolation` codes are preserved.

`PlanExecuteService` accepts an asynchronous local planner and executor, a
synchronous current-version snapshot callback, and a trusted synchronous grant
resolver. These callbacks must not block the event loop; async executor/provider
implementations must honor cancellation. The resolver accepts only the opaque
reference and returns `QueryGrant` metadata or `None`; it must return `None` for
unknown, revoked, expired, or unauthorized references. Request JSON cannot supply
this metadata. The boundary additionally checks grant identity, run, exact plan
and filter hashes, versions, issue/expiry instants, and maximum 30-second lifetime.
The plan hash includes canonical fields, route/mode, filters, and limits. Spring
still owns grant issuance, fixed lookup operation authorization, consumption,
receipts, and idempotency; W9 implements the lookup transport.

A plan is validated before its metadata is retained. Only the semantic query
SHA-256 digest is stored; safeQuery and semanticQuery text are never cached or
logged by this layer. A run is reserved before planning and consumed before
executor dispatch with no intervening await. Duplicate/concurrent execute,
failure, timeout, and duplicate plan never produce a second dispatch. HTTP
retransmissions receive a typed conflict; this layer performs no automatic retry.

The store is intentionally process-local and bounded to 10,000 run reservations
by default. Reservations are not evicted to make room for replay; capacity fails
closed and requires lifecycle management before production activation. Restart
or routing execute to another worker loses its plan and returns `PLAN_NOT_FOUND`.
W13 must supply durable run deduplication and deployment coordination before
multi-worker production activation. This implementation does not claim durable
exactly-once execution or cancel an already-completed external side effect.

The Spring design remains a proposal in
[`journey-query-mcp.md`](https://github.com/YRootLab/OnMaru-backend/blob/develop/docs/ai-rag-spring/journey-query-mcp.md).
W8 pins the concrete path/scope/header/wrapper choices here. W0 shared fixtures
remain unchanged; no cross-repository fixture import or Spring CI conformance is
claimed. Spring must adopt these transport choices along with the W0 schemas.
