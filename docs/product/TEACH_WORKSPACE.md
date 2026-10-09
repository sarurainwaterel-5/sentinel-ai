# Teach local release

Teach accepts one text-based PDF per mission, within the configured upload limit, into a registered specific domain. Topic and source context are preserved. The upload is validated before a queued mission is accepted; the operator then follows actual backend observations. Up to eight accepted missions may wait/run; indexing is serialized to bound CPU memory and duplicate races in the local single-process worker.

The timeline reports receive, fingerprint, extraction, chunking, embedding/vector storage, catalog persistence, and acquisition history recording. It does not simulate percentages, claim semantic understanding, or fabricate connection discovery. Exact duplicates short-circuit ingestion, with the existing document domain shown. Indexed documents with a failed Learning Event recording remain indexed and show an explicit warning.

Mission progress, results, failures, and timestamps are persisted in an additive PostgreSQL table. API reads are scoped by organization and optionally domain. Leaving Teach does not stop the worker. The UI polls while accepted missions remain active, reconnects after navigation/reload, and exposes recent missions and completed source provenance. Poll errors stop automatic refresh until operator retry.

On restart, queued/running missions become interrupted history. The operator checks the catalog and explicitly resubmits if needed; the service does not automatically repeat uncertain writes. Interrupted source files are retained. This local worker is single-process, not a distributed queue. The existing /upload contract remains available.

Memory acquisition is independent of cognitive confidence, constitutional acceptance, and execution authority. ADR-037 remains Proposed and the proposition-to-inference boundary stays closed.
