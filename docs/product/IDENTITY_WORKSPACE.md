# Identity operator workspace

Identity observes Sentinel's Living Canon. It provides Overview and Principles tools with refresh, loading, retry, and empty states.

Overview displays the actual structural report: discovered document/layer counts, architecture decisions, sprint records, warnings, and empty documents. It omits the former hard-coded version and claims of self-understanding or universal consistency. Structure, confidence, constitutional semantic admissibility, and human execution authority remain distinct.

Principles provides search by title/path and knowledge-layer filtering. The reader shows original Markdown source as inert text with relative provenance. No source HTML executes. Documents are read-only; the interface neither edits nor activates principles. Operators can open the identity statement directly or navigate to Governance and Domains.

GET /canon/library lists observed Markdown documents beneath the Canon root with relative paths, titles, layer, and type. GET /canon/document?path=RELATIVE_PATH opens one registered source. The reader rejects absolute paths, parent traversal, non-Markdown files, external symlinks, missing files, and documents beyond its one-megabyte limit. Read failures return bounded errors without filesystem details.

The source documents and backend classifications remain authoritative. The workspace does not establish independent semantic acceptance, change ADR-037, or authorize autonomous action.
