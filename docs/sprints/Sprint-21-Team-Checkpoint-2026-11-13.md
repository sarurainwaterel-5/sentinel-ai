# Sprint 21 team checkpoint — 2026-11-13

Subsequent implementation and current remaining decisions are recorded in
[the lifecycle/publication/review handoff](Sprint-21-Implementation-and-Review-Handoff-2026-11-13.md).
The engineering gap list below describes this earlier checkpoint.

Three implementation/review agents and root completed the following additive
work. Sprint 21 remains open; production answering is disabled, ADR-037 is
Proposed and proposition-to-inference remains closed.

## Implemented and reviewed

- Versioned source/chunk SQL references and complete paginated manifest checks
  in an isolated SQLite repository. Exact four-field scope, extraction policy,
  version/epoch bindings and a caller-supplied expected manifest digest are
  mandatory. Pages are bounded to 256 locators, up to 100,000 chunks. Every chunk
  resolves to verified CAS bytes. SQL snapshot consistency, valid-object
  substitution, coherent SQL digest tampering and interruption are tested.
  This is not the application PostgreSQL migration or a source-truth attestation.
- A separate bounded inspection coordinator composes retrieval and the three
  roles through the real Responses SDK. HTTP mocks exercise the wire protocol;
  no additional paid calls occurred. Binding/configuration changes around every
  await, malformed results, rejection, deadline and cancellation discard partial
  candidates. Success records exact context, nonsecret model configuration,
  structured assessments and request digests. Its retrieval and binding callbacks
  remain trusted synthetic adapters, not installed PostgreSQL/Qdrant readers.
- Read-only PostgreSQL authority observations enforce exact four-field grants,
  issued-handle rechecks and terminal denial after failure. Actual disposable
  PostgreSQL 16 tests exercise revocation and revisions. Principal authentication
  and the mandatory writer epoch protocol are explicitly external. An ABA grant
  change without an epoch bump is tested as invisible, not claimed prevented.
- Independent saved-evidence review recomputed all 44 provider-step hashes and
  OCR artifact hashes. It identified concrete OCR errors and prepared exact
  unresolved model/source decisions without supplying human acceptance.
- The application writer inventory maps uploads, teaching, archive/restore,
  maintenance/import/repair, repository bypasses, core memory and Learning Events.
  It records required outbox routing or explicit governed-material denial. Those
  application changes are not silently claimed implemented by this inventory.

Independent review found and corrected a missing external manifest pin, a
nonterminal repeated authority capture, absent inspection configuration/verdict
records and empty source support. Frozen packet/coordinator/main/route contracts,
application credentials, installed data and release flags were not changed.

## Validation

The full backend regression passed **2,222 tests**, four optional checks skipped,
seven warnings. Final tests after the review fixes passed **81 tests**, one optional
PostgreSQL test skipped without its service environment. A separate actual fresh
PostgreSQL16 run passed **five tests**, including that service check; its owned
container/schema were removed. The combined source/chunk/manifest selection passed
79 tests. Frozen packet, review and presentation integrity inspectors remain valid;
readiness remains blocked as required. No frontend changes or deployment occurred.

## Exact remaining work

1. Review [the owner packet](Sprint-21-Remaining-Owner-Review-2026-11-13.md): both
   measured model runs, exact generated candidates/disagreements, Smith/Cook
   identity/intake, OCR corrections and chart limitations. Human attestations
   must come from actual review, not from delegation or code execution.
2. Complete the application principal handoff and transactional permission writer
   protocol, then compose the PostgreSQL authority reader with actual retrieval.
3. Implement the reviewed PostgreSQL v2 application schema/references, lifecycle
   writers and durable outbox routing for every inventoried mutation. Preserve
   immutable versions/tombstones and deny unsupported governed writers.
4. Compose current-version Qdrant reconciliation, complete readback, immutable
   source-byte resolution and the publication barrier with the inspection
   coordinator. Current isolated results cannot substitute for that composition.
5. Prepare/review the exact migration target and backup, perform authorized source
   corrections/intake, inspect actual rendered runtime outputs and obtain bound
   production authorization only after the implementation and acceptance pass.

See [storage contract](Sprint-21-Source-Storage-Contract-v2-Proposed.md),
[inspection composition](Sprint-21-Runtime-Inspection-Composition-2026-11-13.md),
[authority observations](Sprint-21-Postgres-Authority-Observation-2026-11-13.md),
and [writer inventory](Sprint-21-Application-Writer-Inventory-2026-11-13.md).
This checkpoint does not establish that only approvals remain or declare the
sprint complete.
