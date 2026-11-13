# Governed v2 rollout candidate — review required

This is the concrete additive installation target, not an executed migration or
release approval. Keep ADR-037 Proposed, the existing public answer route disabled
and proposition-to-inference closed. The original application remains usable.

## Destination and isolation

The current local compose target is service `sentinel-local-postgres-1`, database
`sentinel_ai`. Install only the new `sentinel_governed_v2` schema through explicit
`CatalogWriter.install()` after verifying the backup and that the schema does not
already exist. Never apply the disposable test database allowlists or synthetic
credentials to this destination. The catalog migration is packaged at
`backend/app/services/governance_sql/001_catalog_v2.sql`; initialization of the
inspection gate/publication tables remains explicit, with an empty gate denying.
No legacy `documents` row is relabeled as governed or edited by this installation.

Provision a new named volume `sentinel-local_governed_v2_data`, mounted at
`/app/governed-v2`. Create private owned `accepted`, `originals` and `chunks`
directories there. Preserve existing uploads, cognitive data, PostgreSQL and
Qdrant volumes. CAS objects use content hashes, not original names/folders.
Use a separate collection under `governed_v2_`, with exact reviewed model
artifact policy and dimension. The application SDK adapter refuses legacy names
and automatic adoption of an existing collection. Test-only collection/URL
allowlists remain test-only; use the explicit application SDK adapter for the
reviewed installed Qdrant endpoint.

The server injects the installed offline `EmbeddingService` through
`GovernedEmbeddingAdapter`, explicitly pinning dimension and a reviewed artifact
policy digest. Hash/verify the actual cached model files when preparing the release;
a model alias and supplied policy hash alone do not attest those bytes or ranking
quality. No network model fallback or key reuse is implied. Reconciler payloads
bind the policy identity; changed configuration denies rather than mixing indexes.

## Authentication and route mounting

Provision the reviewed operator identity and exact four-field scope grants with
new explicit credentials using the salted-record API. No default administrator,
forwarded username, model API key or legacy catalog metadata may create a grant.
Existing local Caddy authentication remains the outer installation boundary;
application credentials are verified against the new catalog independently.

Mount `create_governed_workspace_router(...)` with the exact catalog, private
stores and bounded server-owned extractor/policy. It serves intake and supported
archive/restore/tombstone operations; unsupported replacement/reindex/repair/scope
moves remain explicitly denied. This is an additive workspace registration through
a reviewed host integration, not a change to frozen packet modules. A service worker
uses the new catalog outbox and distinct governed index. Every current writer is
either routed through this v2 service or stays in its separate legacy domain; no
legacy maintenance/import path may target the new schema/collection.

Keep inspection services separate from the public answer/frontend contract. SQL
inspection publication verifies current credentials, grants, gate identity,
versions and source/chunk bindings before a durable receipt; checked reads may
expose only that inspection artifact. Gate rotation records evidence identity,
not human acceptance. Initial empty gate must deny. Request context is immutable
and model budgets stay bounded with no repair/fallback or SDK retries.

## Backup, migration and rollback sequence

1. Stop new ingestion for the cutover window; confirm no running teaching jobs.
   Reobserve the exact catalog/source/index inventory and compare to the reviewed
   manifest. The retained 75-document/47,429-chunk result is not a live snapshot.
2. Preserve a verified PostgreSQL logical backup and restore-test it against a new
   disposable database. Preserve uploads/cognitive volumes and a complete Qdrant
   backup, recording hashes, volume/image IDs and timestamps outside Git. Abort on
   missing originals, source identity mismatch or unreviewed inventory drift.
3. Install the new schema and private volume only. Record actual schema/store/
   collection identities and the exact release code/policy hashes. Provision only
   reviewed operator/grants. Do not populate a production-acceptance gate.
4. Copy reviewed sources to CAS and verify every original hash/length. Ingest
   immutable versions with exact extraction policy/limitations; SQL remains pending
   until complete paginated index readback acknowledges the current operation.
   Preserve the Smith quarantine, unreviewed OCR and separately acquired Cook book
   dispositions until their exact owner choices authorize the specified actions.
5. Exercise mounted HTTP auth/size limits, expected-epoch lifecycle transitions,
   stale completion/revocation/gate races and exact checked inspection output on
   the actual target. Review rendered candidate/context/citations and operation
   budgets. Do not use synthetic vector tests as embedding/retrieval-quality proof.
6. If verification fails, stop the new worker/router and keep the new schema/store
   isolated for reconciliation; leave originals and legacy services intact. Do not
   delete CAS objects or restore a live database destructively as an automatic
   rollback. Reenable legacy intake only after catalog consistency is confirmed.
7. Production answering requires the separate empirical/independence/source/
   rendered-output acceptance and explicitly bound release authorization. None
   is supplied by this proposed rollout or by a successful installation.

Owner judgments are enumerated in
[the review packet](Sprint-21-Owner-Review-Packet-2026-11-13.md). No credentials,
private originals, database exports or acceptance signatures belong in Git.

The machine-readable candidate at
`docs/governance/governed-v2-rollout-candidate.proposed.json` pins 13 exact
implementation files and leaves operator/model/inventory/backup fields unset.
Every installation, migration and acceptance flag is false. Review and fill
those exact target bindings rather than interpreting the template as readiness.
