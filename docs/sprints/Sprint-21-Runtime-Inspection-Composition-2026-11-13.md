# Sprint 21 isolated SDK inspection composition

The additive `runtime_inspection_rehearsal.py` composes retrieval, generation,
statement validation and relevance through the existing real OpenAI Responses
SDK transport. It is unregistered and does not modify the frozen offline
coordinators or public response contract. ADR-037 remains Proposed.

The coordinator snapshots an explicit trusted adapter binding: question, full
context digest, exact four-field scope, principal ID, permission epoch, catalog
epoch and gate-evidence digest. It checks this binding before and after retrieval
and each provider await, then immediately before serializing the immutable
inspection result. A single outer deadline covers retrieval and all three roles;
there are no retries, repair attempts or fallback models. Parent cancellation
propagates to a pending SDK request. A rejected or invalid candidate discards all
partial candidate, context and source output. Complete structural premise and
relationship coverage precedes judgment, and judgment rejection stops relevance.

Validation used actual `AsyncOpenAI.responses.parse` and `httpx.MockTransport`
HTTP responses with synthetic keys and the frozen reviewed synthetic case packet.
No network connection, paid model call, application data or database mutation was
used. The new 46 tests plus 29 existing transport tests passed (75 total). They
check Responses request schema/store/truncation serialization, principal/catalog/
scope/question/context/gate changes at every await, invalid initial bindings,
HTTP and malformed-output failures without retry, generation structure rejection,
statement/relevance rejection, request-digest mismatch, outer deadline and parent
cancellation. Mock labels establish control-flow behavior, not semantic accuracy.

This milestone does not wire PostgreSQL/Qdrant retrieval into this coordinator.
Its supplied retrieval adapter and binding reader remain trusted capabilities;
`eligible=true` is a rehearsal input, not an authorization decision. The source
context remains review evidence, not an independently verified source-truth claim.
The additive PostgreSQL authority reader and versioned source work must be composed
through separately reviewed adapters. Application authentication, lifecycle writers,
outbox reconciliation, full immutable-source verification, exact rendered-output
acceptance and an atomic publication barrier remain outstanding. Serial checks
cannot prevent a revocation immediately after the last check. Consequently every
result explicitly reports `publication_barrier_implemented=false`,
`production_enabled=false`, `release_authorized=false`,
`empirical_acceptance=false` and proposition-to-inference closed. Inspection output
cannot be used as a production answer or acceptance record.

Successful immutable reports retain the exact nonsecret per-role model and
reasoning configuration, zero-retry settings and transport budgets, the complete
structured statement and relevance verdicts, and SHA-256 digests for all three
requests. Configuration changes during any await withhold output. No private
reasoning or credentials are recorded. Empty source sets and premises without
explicit evidence references deny before generation. The synchronous binding
callback must be bounded and nonblocking; an asyncio deadline cannot preempt
a callback that blocks the event loop. The adapter remains responsible for
authoritative source/scope validation.
