# Sprint 21 application writer inventory — 2026-11-13

Read-only source inspection of the active application and maintenance entry
points below. No live mutation or runtime routing was changed. These are legacy
writers; isolated Sprint 21 stores, SQL adapters and rehearsals are not composed
into these paths. Production governed answering remains disabled and ADR-037
remains Proposed. Human review alone cannot complete the missing integration.

Paths below are repository-relative. “Required” describes future governed
material handling, not behavior already implemented.

| Entry point and concrete implementation | Current mutations and ordering | Governing gap and required routing or deny |
|---|---|---|
| `POST /upload`, `backend/app/routes/upload.py` → `backend/app/services/upload_service.py::{process_source_upload,process_saved_pdf,_index_pdf}` | Writes a UUID-named original through `source_upload_io.save_source_upload`; fingerprints and extracts; calls Qdrant `store_chunks` before `DocumentRepository.create_document` commits SQL. No-text/unsupported media instead commit a `stored` zero-chunk row. Duplicate hash detection deletes the newly accepted duplicate file. | No immutable source/chunk/manifest reference transaction, lifecycle/content/index epochs, authenticated scope grant check or outbox. Global SQL hash lookup is not a scope grant. Governed intake must capture authenticated principal/exact scope, preserve verified bytes, atomically commit version/manifest/pending state plus index command, then reconcile and read back every expected point before making the version eligible. Until routed, deny legacy writes to governed identities/scopes rather than inheriting eligibility from `status=indexed`. |
| `POST /teach/missions`, `backend/app/routes/teaching.py` → `backend/app/services/workspaces/teaching.py::{run_mission,advance,recover_interrupted}` | Saves original, commits queued mission, schedules an in-process background task. Worker serializes locally and calls the same upload writer. Stage/status/event updates commit independently. Restart marks unfinished missions interrupted; it does not replay them as successful. | In-process lock/slots and durable progress are not a transactional index outbox or cross-process idempotency. Organization/domain form values do not authenticate the actor. Governed mission acceptance must bind identity/scope and a durable operation ID, route content writes through the same transactional writer, and acknowledge success only after reconciled content/index state. Mission telemetry must not commit an in-progress governed content transaction accidentally. |
| `PUT /knowledge/{document_id}/archive` and `/restore`, `backend/app/routes/lifecycle.py` → `backend/app/services/knowledge_management_service.py` | For indexed material, sets Qdrant payload status first with a document-ID filter, then commits SQL status. Zero-chunk/not-indexed material skips vector mutation; restore returns it to `stored`. | No authenticated scope lookup, expected-version condition, lifecycle increment, catalog revision increment or outbox. Split failure can leave SQL/vector status inconsistent. Governed archive/restore must atomically transition authoritative state/epochs and enqueue exact-version reconciliation. Retrieval denies from SQL immediately on archive regardless of stale vectors; restore remains ineligible until expected content/index verification passes. Deny these legacy endpoints for governed IDs until routed. |
| Direct repository helpers, `backend/app/repositories/document_repository.py::{create_document,archive_document,restore_document}` | Commit immediately; lifecycle helpers mutate only SQL status. Repository restore always sets `indexed`, unlike the zero-chunk-aware service path. | Alternate callers can bypass service ordering and zero-chunk handling. Governed writes need one transaction owner and shared transition rules; low-level helpers must not independently commit or promote governed records. Deny direct legacy helper use for governed material. |
| Metadata repair CLI `backend/scripts/migrations/migrate_vector_metadata.py --apply` → `backend/app/services/migrations/vector_metadata_migration.py::VectorMetadataMigration.run` | Reads SQL rows and matches Qdrant points by document ID, then file hash, then unique filename; patches payload metadata with `set_payload(wait=True)`. Defaults missing scope/status values to legacy defaults. Dry run is the default. | Hash/filename matching and payload patching cannot create governed identity, grants or provenance. Governed metadata changes require reviewed exact identity/version mappings, audited SQL mutation and revision changes plus a version-bound outbox patch. Deny fallback matching/default scope and direct payload patching for governed records. Smith title correction needs a separate reviewed catalog metadata operation; this CLI only copies existing SQL metadata into vectors. |
| Reconstruction CLI `backend/scripts/migrations/reconstruct_missing_vectors.py --apply` → `backend/app/services/migrations/vector_reconstruction.py::VectorReconstructionService` | If any point exists for a document ID, reports `already_present`. Otherwise resolves `upload_directory / document.filename`, re-extracts PDF text, chunks and calls `store_chunks` with the catalog hash/metadata. Does not create SQL document rows. | Nonzero count is not completeness; filename lookup is not verified source identity and the source bytes are not rehashed against the catalog hash in this path. It can recreate indexed-status payloads without a lifecycle check. Governed reconstruction must use verified immutable source references, a frozen extraction policy/manifest, authoritative current lifecycle and expected-version index command; read back the entire manifest, not just count. Deny direct reconstruction of governed material. |
| Legacy import `scripts/import_legacy_memory.py --apply` | Validates an exported SQL/vector inventory and collisions, upserts vectors for new document IDs, then adds and commits SQL rows. Preserves legacy identifiers/timestamps; default is dry run. | Validation of an export does not authenticate current grants or source truth. Vector-before-SQL import is not atomic across stores; imported payloads have no governed epochs/manifests. Governed migration needs the reviewed exact mapping and source verification, SQL pending versions plus durable outbox, bounded reconciliation and rollback/recovery evidence. Do not mark imported legacy rows governed merely because their IDs/counts match. |
| Core memory `POST /core-memory/initialize` and `/ingest`, `backend/app/routes/core_memory.py` → `backend/app/services/core_memory_service.py` | Creates `sentinel_core_memory`; reads Markdown under `docs/philosophy`, `docs/design`, `docs/architecture/decisions`; embeds chunks and upserts random-ID points with `priority=constitutional`. Repeated intake adds fresh IDs. | No governed SQL catalog/source identity, exact organization scope, immutable version, manifest or authorization record. A priority label is not constitutional or publication authority. Keep this collection explicitly excluded from governed evidence until a reviewed intake maps each source to authenticated scope and versioned storage/outbox; otherwise deny its use as governed evidence. |

Shared vector mutation primitive:
`backend/app/services/qdrant_service.py::{create_collection_if_not_exists,store_chunks}`
creates `incident_knowledge` and writes random-ID points in batches of 128,
embedding each chunk and attaching source text, scope labels and `status=indexed`.
A later-batch or SQL failure can leave partial points. Governed callers must use
an expected-version command and deterministic point identities, verify all exact
manifest rows and embedding configuration, and acknowledge only a complete
matching version. Vectors and their labels remain retrieval hints, never grant
or byte authority. Collection creation itself must use explicit target
configuration rather than infer that existing contents are governed.

An additional independent write follows successful ingestion:
`backend/app/services/workspaces/learning_history.py::IngestionHistoryRecorder`
saves an ingestion Learning Event to a separate SQLite store. Failure yields a
warning after indexing. This observation is not a content-commit receipt or proof
of understanding; future governed event emission needs an idempotent post-commit
outbox/receipt policy without turning optional history failure into false index
success or undoing committed originals.

## Next actual composition work

1. Choose and review the production target schema/migration and explicit legacy
   mappings. The current document model is not the isolated versioned catalog.
   Bind the authenticated local administrator to exact SQL grants; do not trust
   caller-supplied organization fields or vector payloads as identity.
2. Implement one application transaction owner for verified source/chunk references,
   immutable versions and paginated manifests, lifecycle/catalog/permission
   epochs, and durable index commands. Route **every** writer above through it or
   implement an explicit governed-material deny at its entry point. Read-only
   inventory and proposals have not installed those denies.
3. Compose durable worker reconciliation, retries/idempotency and exact readback
   with authoritative scoped retrieval. Prove batch failure, crash-before/after
   SQL commit, duplicate submission, archive/revoke during work, restore and
   stale-ack behavior against the actual application stores.
4. Bind selected-provider requests and returned citations to those verified
   retrieved versions and recheck authority/lifecycle at the publication barrier.
   Finish output/source review and bound release authorization separately.
   Passing isolated adapter tests cannot substitute for these application flows.

No delete/reindex/metadata-correction HTTP writer was found in the inspected
route set; the maintenance apply paths above and direct SQL operations still need
the same controlled boundary. Any new writer must enter this inventory before
it can mutate governed material. This statement is an inventory result, not a
claim that arbitrary administrative database access is technically blocked.
