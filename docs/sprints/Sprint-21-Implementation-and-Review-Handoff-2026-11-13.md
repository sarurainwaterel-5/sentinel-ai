# Lifecycle, publication and owner-review handoff — 2026-11-13

The remaining three workstreams now have concrete code and review artifacts.
This is an implementation checkpoint, not a claim that the installed application
or complete legacy corpus has passed governed production acceptance. ADR-037 is
Proposed and the existing public answer contract remains disabled.

## Application lifecycle and outbox

The opt-in PostgreSQL v2 migration creates a separate catalog with immutable
source/chunk references, exact four-field scopes, versioned credentials/grants,
expected-epoch lifecycle transitions and a durable leased outbox. Application
credential sessions are issued by and bound to the exact catalog instance.
Authorized intake verifies original CAS bytes and every extracted chunk before
committing a pending version/outbox, then rechecks locked credentials/grants in
that transaction. Supported archive/restore/tombstone operations preserve original
versions and reject stale epochs; unsupported reindex/replacement/scope moves are
explicitly denied in the new HTTP workspace.

The opt-in HTTP router includes actual Basic verification before multipart parsing,
bounded declared/streamed request sizes and concurrency, private server filenames,
server-owned extraction/policy, thread-pool parsing and source retention on later
failure. It is not silently mounted in frozen main modules and provisions no default
administrator. The injected extractor must retain CPU/time/memory limits.

## Publication controls and actual composition

The governed index representation binds exact scope, current versions/epochs,
manifest, locators and embedding policy. Full SQL/index verification is paginated
up to the defined 100,000-locator/64MiB verified-text ceiling. Embedding batches are
32 and index pages 256. Explicit selected locators bound the model context; index
verification is never silently truncated to those selections. A separate explicit
Qdrant SDK adapter excludes legacy collection names and automatic collection
adoption. A strict offline embedding adapter validates model identity/dimension and
finite outputs under an explicitly configured artifact-policy digest.

Supported workers renew only a live current lease between bounded pages/batches
under an outer deadline. Expired/superseded claims cannot be revived or acknowledged;
expiry during activation rolls the entire SQL transition back. Complete index
readback precedes conditional acknowledgement. Synthetic vector tests prove control
flow, not real model weights, ranking quality or large-corpus throughput.

Inspection evaluation exposes only an opaque owned handle. Publication and checked
reading lock current SQL gate, credentials/grants, scope and document versions;
verify exact immutable context and extractive premises; and durably record the
inspection artifact and selected-locator proof. Gate rotations and revocations
serialize with the publication transaction. The linearization point is SQL commit,
not later network delivery. Already viewed text cannot be recalled. This is an
inspection publication barrier, not a production-release approval.

Actual disposable PostgreSQL16/Qdrant1.18 tests compose authentication, original and
chunk CAS, catalog/outbox, full index readback, real Responses SDK HTTP mocks,
conditional publication and checked reading. The 257-chunk case crosses the page
boundary and detects tampering in an unselected point. No new paid calls, installed
source/index mutation, live migration or production enablement occurred.

## Owner-review preparation

[The private packet](../../../outputs/sprint21-owner-review-20261113/owner-review.html)
contains exact model outputs, book title pages, all 18 scans, source dispositions
and a new partial OCR derivative. Originals and frozen labels remain unchanged.
Page 2's source spelling `PYSCHE` is preserved; the earlier agent claim that it
printed `PSYCHE` was corrected. OCR remains incompletely proofread, with unresolved
passages. No new candidate, source correction, benchmark or production acceptance
has been signed on the owner's behalf.

The [owner review description](Sprint-21-Owner-Review-Packet-2026-11-13.md) lists
six separate substantive decisions. The [rollout candidate](Sprint-21-Governed-v2-Rollout-Candidate.md)
identifies the installed destination, new schema/store/collection isolation,
credential provisioning, backup/cutover/recovery sequence and explicit mounting
requirements. The retained old audit is not a fresh migration snapshot.

## What is still pending

- The owner's actual model/source/independence judgments and bound acceptance
  records; no general instruction to complete work substitutes for those judgments.
- Review and execute the installation plan: fresh exact inventory and verified
  backups, model-artifact policy, operator/grant mapping, new schema/volume/collection,
  route/worker mounting, approved source intake/corrections and actual-target checks.
- Corpus-scale operational measurements and real embedding/retrieval quality, exact
  rendered runtime acceptance and explicitly bound production authorization.

Thus the code supports the reviewed opt-in path, but the installed legacy application
has not been silently converted and the sprint is not declared complete. See the
catalog, transactional publication and paginated-capacity documents for exact
protocol limits rather than extending synthetic evidence to production claims.

## Final validation and preservation

Final full backend regression with the explicit disposable PostgreSQL16 and
Qdrant1.18 environment: **2,350 passed, one optional skip, seven warnings** in
127.34 seconds. This run includes the real service integration checks, application
SDK adapter pagination, lease expiry/renewal, HTTP pre-parser limits, selected
context, publication concurrency and fabricated-premise rejection. The optional
skip is not counted as executed evidence. Frozen packet/review/presentation
integrity inspectors remain valid; readiness returns its expected blocked exit2,
and production/release flags remain false. Thirteen implementation hashes in
`docs/governance/governed-v2-rollout-candidate.proposed.json` were recomputed and
matched. Per-test owned schemas/collections and the shared disposable services
were removed after validation. No installed service, source, credential or index
was modified by those tests; no new provider calls occurred.
