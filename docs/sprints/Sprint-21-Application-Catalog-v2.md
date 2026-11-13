# Application catalog v2 and lifecycle writer — 2026-11-13

`app/services/governed_catalog.py` is an opt-in PostgreSQL application service.
Its separately packaged SQL migration creates a **new explicitly named schema**;
installation fails if that schema already exists. It neither runs through legacy
startup automatically nor alters legacy documents, uploads, Qdrant or release
flags. Install it only against a reviewed destination after backup and migration
planning. The service requires PostgreSQL transactions and owns/closes a fresh
connection from its injected factory for each operation.

Immutable SQL versions reference source CAS identities and exact ordered chunk
locators. Source bytes remain in CAS. The writer checks all chunk objects against
an independently pinned manifest digest before opening SQL locks; the ingestion
service separately validates original source bytes. SQL triggers reject updates
and deletes to versions, chunks and source references. The trusted SQL owner can
still change schema/triggers; these controls are not a defense against a database
administrator. No garbage collector or destructive source deletion is supplied.

Creating a document atomically inserts pending lifecycle state, immutable version,
all bounded chunk pages and one outbox operation, and increments the exact scope's
catalog epoch. Archive, restore and tombstone compare all three expected epochs,
lock scope then document, supersede outstanding work, advance lifecycle/index
epochs, and enqueue the next operation in the same transaction. Tombstoned
versions cannot restore. Content bytes and version identity remain preserved.
Publication stays denied in pending, archiving, restoring and tombstoned states.

Workers claim one operation with `FOR UPDATE SKIP LOCKED`, a random expiring
lease token, 1–120 second lease and at most ten claims. Acknowledgement locks scope,
document and operation, validates the exact live lease, immutable manifest, current
version/epochs and expected transition, then atomically changes state and marks
the operation acknowledged. Expired/replaced leases and superseded work cannot
activate a version. Empty manifests cannot become active. Exhausted operations
remain withheld for explicit operator recovery; they do not silently retry.

Acknowledgement is a trusted worker API: matching a supplied digest alone does
not prove that Qdrant contains the complete current index. The separate publication
and reconciliation service must perform the external index verification first,
and readers must recheck authoritative SQL rather than trusting vector payloads.
A SQL transaction cannot make an external network write atomic. PostgreSQL and
CAS durability, remote index reconciliation, output owner review and production
release authorization remain distinct requirements.

Principals are explicitly provisioned with salted password records; there is no
default admin, proxy-header fallback or reuse of legacy Caddy credentials. Grant
replacement and disabling compare/increment permission epochs transactionally;
credential rotation compares/increments its own epoch. Credential/grant reads use
one repeatable-read snapshot. Authentication handles can be checked again against
these epochs. `create_authorized_version` and `transition_authorized` lock the
current principal, compare credential and permission epochs and exact scope grant,
then acquire scope/document locks before committing. Both require the exact
authentication session bound to this catalog instance and its issued handle; a
constructed principal or handle issued by a different catalog is rejected. Thus revocation during CAS
I/O cannot turn a prior authentication check into a later unauthorized write.
The explicit privileged writer APIs are internal capabilities, never request
identity or public authorization substitutes.

The legacy intake path has not been silently migrated. Application routing,
source inventory migration, destination/backup review and production release
remain explicit integration decisions. No human acceptance is recorded here.

Validation: 41 focused ingestion/authentication/catalog tests passed with the
dedicated disposable PostgreSQL 16 database. Fifteen catalog integration cases
exercise actual SQL commits, constraints, rollback, concurrent lifecycle/authority
writers, issued authentication handles, and multi-chunk original-to-CAS-to-pending
SQL/outbox intake. Synthetic sources and credentials are isolated from live state.

## Opt-in HTTP workspace and deployment contract

`app/routes/governed_workspace_v2.py::create_governed_workspace_router` supplies
actual authenticated intake and archive/restore/tombstone HTTP handlers. A host
injects the exact catalog, separate private CAS stores, private accepted-source
root, server-owned extractor and policy digest. The current frozen main app does
not mount it; no migration or credential provisioning occurs on import. Requests
cannot supply source paths, extracted evidence or extraction-policy identities.
Other lifecycle operations are explicitly denied. Existing legacy writers remain
separate and cannot mutate this schema or its distinct governed index collection.
No legacy source becomes governed merely because an existing catalog row exists.

A route wrapper checks actual Basic credentials before FastAPI parses multipart
or creates parser temporary files. Duplicate authorization fields are rejected.
It bounds declared and streamed total request bytes (1GiB plus 2MiB envelope by
default), with a maximum of two requests in flight per process. Excess work is
rejected rather than queued without bound. Source names are private server UUIDs;
folder paths are never filesystem locations. Extraction and ingestion run in a
thread pool. The injected extractor must enforce its own CPU/time/memory budgets;
thread execution is not a parser sandbox or a hard CPU deadline. The existing
media worker bounds must be retained when configuring it. Accepted originals and
complete CAS objects remain after downstream SQL rejection for audited recovery;
no automatic garbage collection or destructive rollback is implied.

The HTTP factory tests use real scrypt verification, real private original/chunk
CAS and an injected recording catalog, while the separate PostgreSQL tests cover
actual transactions. Pre-parser tests assert unauthorized/declared-oversized
requests do not create parser files, and a no-content-length stream exceeding its
configured limit is rejected. Source-derived chunks retain the server extraction
policy; fidelity or completeness of OCR/video extraction still requires its
separate source review and per-source limitations at final deployment.

Before mounting: review the destination DB/schema and filesystem identities,
backup/rollback plan, source migration inventory, explicit operator/grant mapping,
separate governed collection/embedding policy and runtime gate bindings. Provision
no implicit principal from a filename, organization field, Caddy header or model
API key. Mount the intake/lifecycle routes as a reviewed opt-in application change;
keep the existing public answer contract disabled until its separate acceptance.

The worker may renew its current claim for 1–120 seconds between bounded batches.
Renewal preserves token and attempt count, locks scope/document/operation, and
requires matching current version/epochs/state and a still-live original lease.
Expired, replaced and superseded claims cannot be revived. Acknowledgement also
rechecks lease expiry in its final conditional update; expiration during SQL work
rolls back activation rather than acknowledging a stale worker.
