# Phase 2 schema and migration

Canonical SQL: `backend/evaluation/synthetic_oversight/migrations/001-durable.sql`.
Storage schema version 1 is separate from the unchanged proposal contract v1.

| Table | Purpose / constraints |
|---|---|
| schema_migrations | Exactly version 1, migration SHA-256, immutable UPDATE/DELETE triggers. |
| audit_records | Ordered sequence primary key, unique record ID/hash, kind DECISION/INVALID/CONFLICT/REPLAY, valid JSON, previous hash; SQL requires exact advisory true and execution/live false in outer payload. UPDATE/DELETE prohibited. |
| proposal_claims | Proposal ID primary key; event ID, assessment ID and record sequence unique; foreign key to original audit record; correlation/input-hash bindings; UPDATE/DELETE prohibited. |

Original assessments, evidence, evaluation context and errors live together in the
canonical record payload, rather than duplicating a second mutable projection.
The application verifies nested assessments, reference integrity and claim bindings
on every operation. An append does not update a head row: sequence and prior head
are calculated inside the serialized transaction and committed with its claim.

`initializeStore({path})` exclusively creates a new file mode 0600 under an existing
private directory (0700); no default/app database is selected. It applies 001 and
migration identity atomically. A failed owned initialization is cleaned up when its
schema is unusable; an existing file is never overwritten or adopted. Ordinary
open never auto-migrates or creates an absent database. Repeated initialization
fails without changing the existing history.

Opening requires matching user_version, exact SQLite table/trigger inventory,
migration hash and quick_check. Unknown versions, changed/missing triggers and
incompatible databases fail closed; no repair, drop, auto-upgrade or reset occurs.
A future migration requires a new explicit reviewed version and migration tests.
Do not edit 001 in place after using it for retained history.

The in-memory SQLite database in schemaShape() is only an expected-schema inventory
comparison. No proposal, assessment, claim or fallback authority is stored there.

Verified with real SQLite: fresh migration/refused overwrite, unknown version,
SQL immutability/uniqueness/false-authority checks, full transaction rollback,
concurrent writers and crash recovery. Test databases are disposable and separate
from both application's databases. No production schema was migrated.
