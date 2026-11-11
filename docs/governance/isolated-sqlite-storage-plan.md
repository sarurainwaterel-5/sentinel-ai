# Sprint 21 isolated SQLite storage integration

Implemented 2026-11-10. This harness uses actual SQLite file transactions and
supplied source/chunk bytes. It is outside application ORM metadata, Alembic,
startup and deployed routes. The `IsolatedCatalog` API only creates an absent
explicit file; opening requires its `isolated-test-only` metadata and fixed schema
version/digest, the actual SQLite schema inventory, foreign-key consistency and
SQLite integrity check. It cannot automatically discover or open application storage.
Callers must choose a disposable directory and preserve existing local data.

## Schema and operation bindings

`sqlite_catalog.py:SCHEMA` is the exact executable schema artifact. Its UTF-8
SHA-256 is stored with schema version `sentinel-isolated-catalog-v1`, a generated
database UUID, and isolation purpose. The schema includes exact-scope revisions,
a durable identity/tombstone ledger, immutable content versions and ordered chunk
bytes/manifests, and a relational outbox. Foreign keys are enabled on each handle;
write transactions use `BEGIN IMMEDIATE` and `synchronous=FULL`.

Every read/write transaction checks row and byte budgets: 1,000 identities and
scopes, 10,000 versions/outbox operations, 320,000 chunk rows and 256 MiB of
stored source/chunk bytes. Each source is bounded to 1 MiB; each manifest has
1–32 UTF-8 chunks, each at most 64 KiB and at most 1 MiB combined. Persisted
identity epochs, byte types, lengths, digests, scope and locator order are checked
before issuing source inspection. These bounds do not certify production load.

`put` requires explicit document identity, exact `EvidenceScope`, source bytes,
ordered UTF-8 chunk bytes, operation identity and expected lifecycle for an
existing identity. Every replacement advances lifecycle, content and scope
revision; archive/restore/delete advances lifecycle and scope revision. Source
and ordered manifest hashes bind outbox events. Catalog, bytes, revision and
outbox commit together; a failure rolls back every component. Equal bytes do not
merge identities. Cross-scope moves and replacement of archived content are denied; archived
content requires the explicit restoring transition first. Tombstones retain identity and
cannot be restored or replaced. Archived restore returns to pending verification.

Identical operation retries return their original lifecycle without another
write; reuse with a different payload fails. Every new transition serializes its
read/check/write under the SQLite writer lock. Independent connections with the
same expected generation cannot both succeed. Reconciliation compares document,
scope, lifecycle, content, state and manifest and verifies stored source/chunk
bytes. A late event becomes stale. A successful relational reconciliation never
sets an indexed state or proves a vector operation happened.

Snapshots and evidence reads use individual SQL read transactions. Evidence is
explicitly **source inspection**, issued only for pending documents. It carries
`index_verified=false`, `release_authorized=false`, and
`production_enabled=false`; it is not an `EvidenceChunk` accepted by governed
answer eligibility. The snapshot retains archived and tombstoned identities.
SQL reads do not establish atomic consistency with a separate authentication
store or a distributed publish barrier. Consumers must recheck their captured
permission/catalog bindings; final release remains independently gated.

## Backup and restore rehearsal

`backup(destination)` refuses an existing destination, uses SQLite's online
backup API, reopens the resulting artifact with schema/integrity checks, and
returns the exact artifact SHA-256, database UUID, schema version/digest and SQLite
runtime version. It does not approve application migration. Tests reopen that
artifact, compare a complete catalog snapshot, reconcile retained/stale events,
and perform a restore lifecycle transition on the clone while verifying the
source database remains unchanged. This rehearses this exact disposable schema,
not a live application migration or recovery of vector/file/auth stores.

Before any application migration, an independently reviewed record must bind:

1. Exact target database identity and observed source/destination revisions.
2. Migration source artifact digest and exact dialect/runtime version.
3. Exact inventory, scope mapping, source-byte and ordered manifest digests.
4. Backup artifact digest and included database/files/vector/auth stores, capture
   revision, and a successful restore report on those exact artifacts.
5. Explicit bounded human migration authorization, maintenance lock/writer
   coverage, compatibility checks, rollback plan and operator identity.
6. Rechecked pre-apply bindings and post-apply identity/count/epoch reconciliation.

No such application binding or authorization is fabricated here. The proposed
21-J schema is not registered in Alembic; existing startup's automatic head
migration behavior remains unchanged. Production promotion needs real verified
index/provider integration, independent semantic evaluation, final acceptance
and explicit release authorization. ADR-037 remains Proposed and inference closed.

## Validation

`backend/tests/test_sqlite_catalog.py` runs against pytest temporary SQLite files.
It covers persistence/reopen, exact scopes, duplicate bytes/distinct identities,
operation idempotence, stale completions, concurrent expected-generation writers,
archive/restore/tombstone ABA, ordered manifests, invalid-byte/budget rejection,
stored-byte corruption, deliberate last-write transaction failure on both create
and replace, and artifact-bound backup/reopen/restore. It opens no application DB
and contacts no vector service/provider. Temporary files are not committed.

## PostgreSQL 16 dialect rehearsal

The separate `postgres_rehearsal.py` runner executes
`isolated-postgres-catalog.sql` against an explicitly supplied PostgreSQL 16 DSN.
It requires `current_database() = sentinel_sprint21_rehearsal`, creates unique
rehearsal and restoration schemas, and does not use application configuration,
metadata or Alembic. The database must be a disposable container database.
`SENTINEL_ISOLATED_POSTGRES_DSN` is used only for explicit invocation; it is never
printed in reports. The DDL artifact is versioned and hashed. Tests with no DSN
explicitly skip the real integration check rather than asserting it passed.

The dialect rehearsal creates real principal/grant, exact-scope, identity,
version, ordered-chunk and outbox rows. It deliberately fails the final outbox
write to demonstrate rollback of an earlier catalog/revision transition,
uses a second independent connection for expected-generation conflict checks,
retains tombstones, denies stale completion and verifies source/chunk/manifest
bytes. Principal permission epoch and exact grants are transactionally revoked.
A canonical logical backup artifact includes this harness's synthetic row bytes,
schema digest and exact PostgreSQL database/version bindings. The runner rereads
that artifact and restores rows into a new schema using the identical DDL, then
compares complete canonical inventories, row counts and bytes and rechecks event
states. This artifact is a logical backup of the small rehearsal schema; it is
not `pg_dump`, physical recovery, a database cluster backup, or live user-data
recovery. The uniquely created schemas remain for inspection until the disposable
container is removed.

This establishes real PostgreSQL dialect and transactional evidence for the
isolated schema. It does not migrate the application, establish operational
writer coverage or prove a real vector index. Actual application migration,
source inventory/backup, authenticated runtime integration, independent semantic
evaluation and final release acceptance remain separate requirements.
