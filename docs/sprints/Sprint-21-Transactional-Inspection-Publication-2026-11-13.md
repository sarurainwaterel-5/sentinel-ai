# Conditional inspection publication and governed index composition

The new `transactional_inspection_publication.py` composes the additive v2 catalog,
application credential verification, immutable chunk storage and the SDK inspection
coordinator. `catalog_index_reconciler.py` supplies a distinct governed Qdrant
representation. Neither module is registered as a public answer endpoint and ADR-037
remains Proposed. Every artifact retains production/release/empirical acceptance false.

## Durable publication boundary

A barrier accepts an exact `GovernedAuthenticationSession` bound to the same writer
and its own issued principal handle. It checks current credentials, permission epoch,
exact scope/grant, scope catalog epoch, active document/version/epochs, manifest digest
and acknowledged current outbox identity. Transactions lock the SQL gate row, principal, then scope,
then document, matching the supported catalog writers. The SQL gate table starts empty: missing evidence identity denies. Explicit
`set_gate(expected_epoch=..., sha256=...)` rotates evidence identity without
asserting acceptance. Proofs bind both its epoch and digest, including a rotation
that retains the same digest; gate writers serialize on the same row. Request
context is immutable per evaluation. Digest callbacks are additional observations,
not an atomic authority for mutable external memory. Capture and evaluation do not
produce release authority. Evaluation is reserved before its first await and remains
one-shot after cancellation/failure, preventing concurrent duplicate provider budgets.

Evaluation returns an opaque owned handle rather than candidate text. Publication
rechecks the authenticated binding and current request/gate digests under SQL locks,
verifies the complete paged immutable manifest and exact selected CAS chunk bytes
against every context source, then durably inserts the immutable inspection snapshot and digests in
one SQL transaction. Premises must be one-to-one exact extractive selected-source text with
complete evidence IDs; this bounded protocol does not accept paraphrased premises.
Forged result objects or copied handles cannot publish. The result is a receipt only.
A subsequent read repeats current authority/version, content and artifact-integrity
checks before returning the inspection snapshot. Revocation, credential rotation,
archive, gate/request changes and CAS corruption withhold it.

The linearization point is the committed SQL insert or read. Supported authority
writers serialize against those locks. This does not make later network delivery
atomic with permission changes, erase already viewed text, or stop privileged SQL
writers that bypass the protocol. Synchronous callbacks and filesystem reads must
remain bounded/nonblocking; asyncio cancellation cannot preempt blocking Python.
The durable barrier is an inspection artifact boundary, not production authorization.

## Governed index

Each point binds document/version, exact scope, content/lifecycle/index epochs,
manifest digest, ordered locator, byte length, chunk digest and text. The worker claims
one bounded outbox lease, verifies SQL manifest plus CAS bytes, replaces that document's
points in a uniquely named disposable collection, and compares its complete readback
before acknowledging the exact still-current operation. Archive/tombstone require an
empty readback. A late operation cannot acknowledge a superseded version. Verified
retrieval requires active acknowledged SQL state, exact scope and complete index
payload equality, then rechecks SQL/CAS identity. Malformed, omitted, duplicated,
extra, stale or altered payloads deny; vector payloads never establish grants.

The initial 128-chunk document limit is superseded by the
[paged capacity checkpoint](Sprint-21-Paginated-Index-Capacity-2026-11-13.md): complete
100,000-locator metadata bounds and 64 MiB verified text budget, with explicit selected
contexts capped at 128 locators and the provider byte limit. Vector adapters now bind
model/policy/dimension; the default remains a synthetic fixture. These tests do not
demonstrate real embedding or ranking quality.
The source-original CAS remains independently required migration evidence; exact chunk
verification does not prove extraction faithfulness to a PDF/video original.

## Executed evidence

Tests run against disposable PostgreSQL 16 and Qdrant 1.18, dedicated unique schemas
and collections, synthetic CAS chunks, real application credential verification and
actual `AsyncOpenAI.responses.parse` serialization through HTTP mocks. The combined **95 tests passed**: 20 actual service integration cases, 46 runtime
composition cases and 29 transport cases. An additional selected actual-PostgreSQL
regression passed: a fabricated premise was withheld from durable publication even
though all three SDK-mock roles accepted the candidate. No paid calls,
legacy data mutation or installed database migration occurred. Actual integration
observations include rollback after publication insert failure; revoked/rotated/archived
or corrupt-source denial; forged and cross-catalog handle denial; missing/rotated SQL gate denial;
SQL gate-update serialization and privileged SQL version/source-association tampering; SQL lock serialization
against concurrent grant revocation; one-shot evaluation cancellation; exact Qdrant
archive/restore readback; stale acknowledgement after tombstone; payload tampering; and
the complete verified-index → SDK mocks → durable publication → checked-read flow.

Human semantic acceptance, extraction/source corrections, corpus migration and scope
mapping, replacement/reindex lifecycle support, production route/frontend wiring and
explicit release authorization remain separate work. This is not sprint completion.
