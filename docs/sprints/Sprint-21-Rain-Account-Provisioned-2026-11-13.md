# Rain account provisioned — 2026-11-13

The installed `sentinel_ai` database now contains the additive
`sentinel_governed_v2` schema and explicitly authorized operator **Rain**. Principal
and username are both capitalized `Rain`. All nine exact authorized scope grants
are installed, covering the 76 existing catalog documents. Credential epoch is **1**;
permission epoch is **2**. New governed source/document/outbox tables remain empty.

Before the transaction, a private PostgreSQL custom-format backup was restored
into a fresh network-isolated PostgreSQL16 container. All four original public
tables matched the live inventory by exact ordered row digest and count. The
restored test container was removed. Backup SHA-256:
`884248c7045fcf5556a05005870ad8980b079814ba50e547321b5937189cd3bc`.
This is the database backup for additive account setup, not a complete upload/
Qdrant volume backup or a current corpus-migration attestation.

Installation executed the exact pinned SQL in a single transaction, refusing an
existing schema, checking the current scope inventory and inactive teaching jobs,
and retaining original tables. The exact pinned application authentication code
verified the generated credential against each installed grant before commit and
rejected a deliberately incorrect password. Independent post-commit readback
confirmed the enabled Rain record, all nine grants and the original 76 documents.
Every original public-table digest/count remained unchanged. Installed API readiness
returned **200**. No API restart, source/index change or production activation occurred.

New credentials are generated locally and stored only in mode **0600** at workspace:
`outputs/sprint21-rain-provisioning/private/Rain-login.txt`.
The restore-verified backup, operational source and detailed evidence remain in
that private directory, outside Git. Neither password nor salted credential bytes
are included in the tracked receipt or chat.

The current UI still uses its existing Caddy login. The new governed HTTP routes
are not activated yet, and no legacy documents have been migrated into the new
catalog. Account/grant setup is complete; the remaining rollout binds actual model
artifacts, complete corpus/backup identities, new CAS storage and a separate index,
then mounts the reviewed routes/worker and verifies actual-target inspection.
Production answering remains disabled and ADR-037 remains Proposed.

Tracked receipt: `docs/governance/rain-operator.provisioned-20261113.json`.
The original authorization/mapping receipt remains an unchanged historical record.
