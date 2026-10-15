# Sprint 21-J — Catalog schema and migration-gate draft

Reconstructed 2026-10-15 from repository contracts at `ff415b94232337782b018bcabffd39c9fc1b29ee`. The named earlier uncommitted draft was absent from the clean checkout; its absence was reported before reconstruction. This is a reviewed proposal, not a recovered original, executable migration, ORM registration, migration authorization or production acceptance record.

## Contract review and narrow resolutions

The 21-G/H/I models require exact organization/collection/module/topic scope tuples, immutable request bindings, explicit epochs, and offline authority flags that remain false. Existing `Document` has globally unique file hash, legacy status/count and no durable lifecycle or chunk manifest. Existing startup automatically runs Alembic head; current source head is `032_teaching_missions` after `031_document_catalog`. Inspecting these facts does not establish the installed database's revision. This draft stays under docs, outside `backend/alembic/versions`, and introduces no SQLAlchemy metadata or startup changes.

| Design defect to avoid | Reviewed resolution |
|---|---|
| Treating module/topic grants as independent lists | Complete exact scope tuples only; no cross-products, wildcard, whitespace normalization or scope inference. A supplied scope mapping is data, not a grant. |
| Deduplicating identity by file hash | Stable document ID is distinct from content hash. Different IDs may share bytes in the same or different scopes. A repeated ID or incompatible scope mapping is quarantined, not silently merged. Preserve legacy global hash uniqueness until a separate scoped-dedup migration is reviewed. |
| Erasing identity on delete or allowing archive/restore ABA | Durable identity/tombstone ledger survives deletion; identity IDs are not reused. Scope moves are explicit transitions invalidating both scopes, never ordinary backfill remapping. |
| Guessing epochs or promoting legacy indexed rows | Unknown epochs and unverifiable legacy metadata stay quarantined/pending. Provided current epochs/revision must not regress their supplied prior floor; a prior tombstone cannot be resurrected. New tombstones advance both lifecycle and scope revision. Known content changes require a content/lifecycle advance and any epoch change advances scope revision. History not supplied cannot be certified as monotonic. |
| Confusing index generation and document lifecycle | Content/index epochs are nonnegative; index cannot be ahead of content. Eligible runtime evidence requires a verified index for the current content and lifecycle plus a matching manifest. Archive/restore advances lifecycle even when content bytes do not change. The current contracts compare index/content epochs; future adapters must retain the separate lifecycle binding. |
| Partial or reordered chunk manifests | Immutable ordered chunk indexes 0..N-1, exact count/hash/byte length and extraction policy; duplicate/gapped/out-of-range locators deny. Chunks are supplied bytes, not re-extracted or embedded by the dry-run planner. Identical chunk bytes at different valid locators are permitted. |
| Trusting vector acknowledgement/legacy indexed flag | Index completion must bind identity, scope, content/lifecycle generations and complete manifest. A synthetic completion is only a fixture input and never real index evidence. All proposed rows remain ineligible. |
| Late outbox work certifying a newer version | Catalog transition and outbox event commit together, stable operation identity, expected-generation compare-and-set for acceptance. Stale completions deny. Catalog/hash/version validation remains necessary even if a stale vector worker writes late; leases alone do not guarantee fencing. |

## Proposed additive schema (not registered)

- Principal/grant records: stable principal and credential-policy versions, permission epoch, exact unique scope grants. No grants are created by backfill.
- Scope revision ledger: one durable revision for each exact scope, advanced atomically for all eligibility changes. Moves advance both source/destination revisions.
- Document identity ledger: stable global ID, current lifecycle epoch and retained tombstone independent of the legacy row. Deletion cannot remove the tombstone or reset epochs.
- Immutable document/content versions: exact scope, lifecycle/content/index generations, source digest, pending/quarantined/indexed lifecycle state and verified-manifest binding. Unverified legacy rows initially stay governed-ineligible regardless of legacy status.
- Ordered chunk manifest: document/content generation/index primary key, UTF-8 content bytes policy or exact supplied bytes policy, byte count/hash, source digest, manifest digest and policy provenance. No silent overwrite of accepted manifests.
- Source mappings: verified file reference/digest. Original display filename is not a stored path. No file scan or path reconstruction in a synthetic planner.
- Lifecycle outbox/audit: operation ID, target generations and scope, payload/artifact digest, reconciliation status and bounded failure. Any unsupported legacy writer invalidates governed eligibility in the same relational transaction through a separately reviewed writer boundary or trigger policy.

Schema-only deployment must preserve existing rows and deduplication behavior; it does not activate readers or mark old documents verified. Epoch baselines are future generations, not invented historical evidence. The planner may preserve explicitly supplied tombstones without file bytes, but must not convert malformed, duplicate or resurrected identities into accepted tombstones.

## Mandatory future migration gate bindings

An eventual executor must require a versioned, explicit review record binding all of:

1. Target environment/database identity, observed source revision, intended destination revision and exact migration artifact SHA-256. Do not accept `head` or an inferred current installation as the target.
2. Canonical exact-scope inventory digest and source/catalog revision/epoch snapshot; dry-run planner input, policy and plan digests; mapping/manifest reconciliation digest. Changes invalidate approval.
3. Backup artifact digest, included stores/files, capture revision and demonstrated recoverability; restore/rehearsal report digest on the exact artifact/schema transition and database dialect/version. A backup filename or unchecked boolean is insufficient.
4. Explicit human migration authorization for those exact bindings, bounded validity and scope, maintenance/lock plan and operator identity. Authorization to run a migration is separate from source-truth, empirical, answer-release or deployment approval.
5. Pre-apply recheck of target/revisions/inventory/bytes, compatibility and row-preservation conditions; post-apply reconciliation and counts tied to the same operation. Partial/stale work stays ineligible; a new inventory requires a new reviewed plan.

None of these approvals, backups, inventory observations or rehearsals is fabricated by the planner. No executor is added. Before a deployable revision is ever registered, separately review an explicit migration-application gate because the existing Docker startup applies Alembic head automatically. Reversal should keep new ledger inactive and retain populated epochs/tombstones; destructive downgrade needs separate recovery review.

## Synthetic planner contract

Inputs are explicit synthetic record dictionaries, one exact scope/file-fixture mapping per identity, and in-memory file/chunk bytes. Top-level record/mapping/chunk collection order is irrelevant: the canonical binding sorts these collections; chunk locator and the declared ordered hash list retain semantic order. Duplicate identities/mappings are never deduplicated for acceptance. Reports carry safe IDs, scope/version/hash/size fields, bounded dispositions/reasons/counts and input/policy/plan digests, never raw document bytes, arbitrary metadata or credentials.

Valid supplied fixtures produce `pending_verification` rows with a synthetic manifest only. Missing/stale/unverified index evidence, missing/mismatched bytes, invalid scopes/epochs, incomplete manifests and conflicts produce quarantined rows. Valid prior tombstones are retained without requiring file/chunk material. Global malformed/oversized envelopes block the entire plan with bounded reason codes. This policy never emits an indexed/eligible row, real index verification, migration permission or grant.

Input/policy digests detect changes only when compared to trusted expected bindings; they are not signatures. Plan verification recomputes from supplied inputs and the fixed current policy. It remains inspectable dry-run evidence with all authority flags false and proposition-to-inference closed. No schema registration, database read/write, filesystem discovery, actual backfill, lifecycle worker, hash verifier, real storage adapter, live provider, benchmark, production route, ADR-037 change or PR #1 merge is authorized by this draft.
