# Phase 2 persistence architecture

Status: implemented local synthetic oversight persistence; execution remains DENIED.
Baseline reviewed: Phase 1 Sentinel `5a11571`, Trading `8ed8bf8`, including the Phase 1
readiness/runbook and existing canonical protocol. Both were local at task start;
no push, merge or deployment is part of this work.

## Infrastructure decision

Sentinel already uses SQLite for immutable learning history
(`backend/app/repositories/learning_event_repository.py`) and isolated evaluation
catalogs (`backend/evaluation/governed_answers/sqlite_catalog.py`): exclusive creation,
explicit schema identity, immediate transactions and full synchronous writes.
Trading's `packages/ledger/index.js` uses PostgreSQL as the sole authority for its
financial ledger. Reusing that financial database would unnecessarily widen this
synthetic observer's capabilities.

The new `backend/evaluation/synthetic_oversight/durable.mjs` adopts the established
local SQLite approach in Node's built-in SQLite binding, retaining the exact Phase 1
JavaScript evaluator and wire schema. No Python reimplementation, external service,
new package, Trading database credential or deployment infrastructure is needed.
The Node binding is experimental on the tested Node 22.22.1 / SQLite 3.46.1 runtime;
this is a local verified harness, not production runtime qualification.

## Ownership and flow

Sentinel AI owns persistence and replay. Trading's additive
`loadDurableConsumer`, `initializeDurableSupervisor`, `openDurableSupervisor` in
`services/synthetic-oversight/adapter.mjs` reuse the hash-pinned module and migration.
No second store implementation or schema is copied into Trading AI. The old Phase 1
API remains explicit and unchanged; the durable API never calls it as a fallback.

1. Explicitly initialize a new private disk database using migration 001.
2. For submit, acquire SQLite BEGIN IMMEDIATE; validate schema, triggers, journal and
   claim bindings before using any historical data.
3. Return an identical committed proposal's original assessment regardless of a
   later supplied evaluation clock. A different wire for an existing proposal ID,
   even malformed content retaining that ID, creates a separate conflict record.
   Event IDs are also unique. No conflicting original decision is inserted.
4. A new schema-valid proposal is evaluated by an isolated Phase 1 harness under
   its supplied historical clock. Insert the original record and unique claim in
   the same transaction. Only successful COMMIT permits a stored-assessment return.
5. Invalid/unidentifiable input gets an INVALID audit attempt without a proposal
   claim. Storage failure returns no assessment and never creates memory authority.

“Authoritative” means the original historical synthetic decision for that immutable
proposal identity. It never means authorization to trade.

## Contract preservation and corrections

`sentinel.synthetic.proposal.v1` and its canonicalizer are unchanged. The new durable
API adds an immutable proposal-identity policy, not a mutation to Phase 1's event
schema/API. Reusing an existing ID for a revision is explicitly CONFLICT in this
API. A correction must have a new proposal/event ID and `supersedes` metadata naming
an existing assessment. Use a new SUBMITTED revision-1 proposal; Phase 1's existing
in-memory lifecycle API is not silently converted into a durable event stream.
Superseding records link originals; originals and original duplicate responses
are never overwritten. Missing supersession targets are rejected.

## Stored information

`audit_records.payload` retains exact canonical wire, input hash, proposal/event/
correlation IDs, version, complete embedded synthetic evidence, risk/strategy
metadata, assessment, governance checks, validation errors and explicit supersession.
Historical context stores the original UTC evaluation clock, service-availability
simulation, isolated-initial-proposal semantics, evidence inventory hash, evaluator/
schema/wrapper hashes and Node version. Outer sequence/previous hash/record hash
bind the immutable global audit. `proposal_claims` binds identity to its original
assessment and audit row; database uniqueness/foreign keys supplement serialization.

Replay records have their own row/ID and original decision references. A replay is
not a new authoritative assessment or proposal claim. Reproduced results appear only
as `reproduced_assessment`; the top-level `assessment` is null.

## Durability and failure envelope

SQLite rollback journal DELETE mode, synchronous FULL, foreign keys and 5-second
busy timeout; BEGIN IMMEDIATE serializes independent local writers. No in-memory
assessment cache survives or substitutes for a failed database. A temporary lock,
closed handle, corrupt row or unavailable database fails closed. Retrying after an
uncertain commit returns the original if it committed, or creates the sole original
if it did not. SIGKILL before/after commit is tested with real independent processes.

Every transaction verifies schema identity, append-only triggers, contiguous audit
hashes, nested assessment authority and claim/history consistency. Records are
bounded to 4096; payloads to 131072 characters on read, proposal wire to 32768 bytes.
Verification scans history, so this is intentionally a small local store, not a
high-throughput or distributed service. Storage envelope serialization allows the
larger wire/history strings without changing Phase 1's canonical wire limits.

A private local filesystem is trusted. SQL immutability and hashes detect normal API
mutation/corruption; they do not defeat an administrator who rewrites the database,
triggers, hashes and external copies. No signed trusted head or physical power-loss
lab verification is claimed. SQLite/fsync and storage hardware remain dependencies.
