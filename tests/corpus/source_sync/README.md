# W1 public projection intake

`SourceManifestReceiver.receive(payload)` accepts the synthetic private JSON shape in
`fixtures/public-manifest.json`. Spring projection generation and HTTP wiring are
separate work; the existing baseline REST/sync endpoints keep their existing contract.
The receiver emits `prepared_documents`, not an active corpus revision.

The envelope carries `contractVersion=1.0`, immutable `revisionId`, the Spring export's
`sourceRevision`, timezone-aware `publishedAt`, exact `documentCount`, and
`revocationSequence`. Each document names one place and one source revision, its
content hash/reference, license verification and current public eligibility. Allowed
source types are `TOUR_API` (snapshot `OK`), `PLACE_CANONICAL`, and `K_CONTENTS`
(review `VERIFIED`). Unknown types and unverified rights are excluded. The asserted
license code alone never grants eligibility. `contentUrl` is passed through for W2;
W1 does not fetch or validate document bodies.

`manifestHash` is `sha256:` plus lowercase SHA-256 of the received JSON object with
only `manifestHash` removed: recursively sorted object keys, UTF-8, literal Unicode,
compact separators, no NaN. Array order and supplied timestamp spelling are significant.
The fixture hash is fixed independently of the Python receiver. A changed manifest
cannot reuse a revision ID; an unchanged source revision/place cannot change its
content hash. Manifest publication times strictly increase; opaque source revision
IDs are compared for equality, never lexically sorted.

Tombstones carry an ordered positive sequence, scope `SOURCE_REVISION` or `PLACE`,
its exact target, timezone-aware `revokedAt`, and `reasonCode`. Unused target fields
are explicit nulls. Events already received can be replayed unchanged. New sequences
must form the complete contiguous range through the envelope's `revocationSequence`.
A gap, reversal, conflicting sequence, duplicate document/source, malformed payload,
or bad hash rejects the entire intake without changing revision, exclusions or
watermark. A repaired delivery can reuse the rejected revision ID.

One receiver instance keeps serial, process-local intake history and exclusions.
Accepted manifest replays emit no preparation inputs and cannot reset the latest
revision. A fresh instance starts with watermark zero and requires contiguous event
history; there is no trusted resume/checkpoint override. Persistent state, active or
rollback revision blocking, heartbeat freshness, restore/GC, source reapproval beyond
a new source revision, and runtime current-eligibility checks belong to later work.
