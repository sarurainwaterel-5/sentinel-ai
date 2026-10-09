# Preserve taught knowledge when moving to the local release

The packaged local release has its own PostgreSQL, Qdrant, and uploads volumes. Starting it does not automatically import the older development installation's teaching records. A PDF remaining in backend/uploads does not establish that its catalog and vectors exist in the running release.

The October 2026 recovery copied 69 existing document records and 47,386 unique indexed chunks into the packaged release. This includes four trading PDFs with 119 chunks. Original document IDs, hashes, upload timestamps, domains, organizations, and status were preserved. The legacy stores were retained. All source PDFs were copied into the persistent upload volume.

A private export and target database backup are retained under `.local/backups/legacy-import/`. The raw vector export preserves 299 identical duplicate chunk entries and the original catalog export. Four uncatalogued vector points remain in the legacy store. Identical duplicates were compared by full payload and embedding before deduplication; no conflicting chunks were silently discarded.

`scripts/import_legacy_memory.py EXPORT_DIRECTORY` validates a JSONL catalog (`documents.jsonl`) and vector export (`points.jsonl`) against the configured database and Qdrant collection. Default behavior is read-only validation. `--apply` imports new catalog records and their vectors. Run inside the API container with `PYTHONPATH=/app/backend`; use its existing storage environment. Source ingestion must be stopped while exporting. Exported chunk counts must match the catalog and embedding model/dimensions must match the target.

The importer rejects conflicting identities, hashes, scopes, or dimensions. Existing records are preserved, and repeating a completed import adds no documents or vectors. Original upload files must be copied separately after checking for filename collisions. No new Learning Events are invented for historical ingestion.

Evidence in Recall remains bounded by its selected domain, organization, archived status, and similarity threshold. Importing documents restores availability; it does not establish constitutional acceptance or make unrelated questions answerable.

Example invocation after preparing and checking the private export:

```sh
docker cp scripts/import_legacy_memory.py sentinel-local-api-1:/tmp/import_legacy_memory.py
docker cp .local/backups/legacy-import sentinel-local-api-1:/tmp/legacy-import
docker exec -e PYTHONPATH=/app/backend sentinel-local-api-1 python /tmp/import_legacy_memory.py /tmp/legacy-import
# Add --apply only after validation succeeds.
```

Import writes use a longer bulk-operation timeout. Interrupted writes may be retried with the same vector IDs. Existing vector content collisions are compared against the saved payload and embedding and rejected if different.
