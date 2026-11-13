# Sprint 21 corpus extraction checkpoint — 2026-11-12

The read-only corpus audit has completed **74 of the 76** retained catalog
sources. Every completed source matches the retained index snapshot's complete
ordered chunk digests and catalog chunk count. There are zero completed-source
mismatches. These sources account for **38,326 of 47,429 indexed chunks
(80.8071%)**. The two incomplete source records are listed below.

Black's Law Dictionary is the one remaining text-bearing book, with 9,103 indexed
chunks. Its bounded extraction continues from a durable digest-only page
checkpoint; partial prefixes are excluded from the completed coverage above.
CCNA, Gibson's Chancery, Bouvier and PostgreSQL have now completed their exact
ordered comparisons. Two workers used at most 180 seconds CPU, 210 seconds wall
and two GiB address space each; later remaining-book partitions use stable
catalog ordering. The source/parser/chunking policy and originals are unchanged.

The second unresolved source is the previously observed 18-page PDF with no
extractable text and zero catalog chunks. It requires a separately reviewed OCR
path; this audit does not manufacture text or mark it complete.

A separate diagnostic extracted the Smith source retained under the Cook title.
Its 1,130 ordered chunks exactly match the retained index snapshot. That byte
consistency does **not** resolve the title/source mismatch: the source remains
quarantined. Both original copies remain intact. A separately acquired Cook/
Stearns candidate has not been substituted by this extraction audit.

The comparison binds the retained private inventory SHA-256
`e76257a105c56763e12f3a80c7166831a9baf2497fd5fbdd8ab5ca81e7ffbcb6`.
Private execution logs, source identities, code/parser policy bindings, durable
complete checkpoints, and partial snapshots remain outside Git under
`outputs/sprint21-extraction/private/`. The reproducible private
`corpus_weighted_audit.py` writes the sanitized
`outputs/sprint21-extraction/corpus-weighted-audit.json` summary.

No source files, catalog records, vectors, production routes, or release gates
were changed by this audit. The comparison uses a retained index snapshot, not
a current distributed snapshot. Checkpoint integrity does not authenticate the
extractor, establish authority or semantic accuracy, or authorize migration or
production answering. Sprint acceptance remains open.
