# Sprint 21 atomic checkpoint persistence and corpus progress — 2026-11-12

This pass advanced completed source extraction from 36 to **62 PDFs**, each with
an exact ordered digest/count match against the retained 47,429-point index
snapshot. It does not enable migration, authenticated retrieval, or production
answering. ADR-037 remains Proposed and Sprint 21 remains open.

## Durable completed checkpoints

`legacy_checkpoint_store` persists completed records under keys derived from the
exact source hash, source size and extraction policy. Store directories must be
owned by the current user and mode 0700; records must be owned and mode 0600.
Reads are bounded to 8 MiB, refuse symlinks, duplicate JSON fields and invalid
bindings, and return no reusable checkpoint for truncated or unsafe evidence.

New records are written to exclusive random temporary files, flushed and synced,
then published with an exclusive hard link. A concurrent winner is revalidated;
identical evidence is idempotent and conflicting evidence is refused. Existing
invalid files are preserved for separate quarantine rather than overwritten.
Cleanup removes only the temporary file owned by the current save operation.

Saves sync the immediate parent directory, the complete file and the store
directory. Idempotent adoption and concurrent-winner adoption sync the same file
descriptor used for validation before directory sync. Loads remain read-only.
Independent review identified retry/adoption durability gaps; all have regression
coverage. Existing ancestor directories are assumed durable. If publication
succeeds but a later sync fails, the call raises and the complete file may remain;
retries repeat the required syncs. Integrity checks do not authenticate execution.

The 20 store tests cover interrupted writes, file/parent/directory sync failures,
retries, truncated/oversized records, symlinks, binding mismatches, conflicts and
concurrent publication. All **222 relevant tests passed**, including the existing
worker, streaming, checkpoint, source-capture, reconciliation and SQLite suites.

## Actual adoption and execution

The temporary launch scripts had been cleared. The audit resumed from preserved
private scripts and checkpoint evidence without losing completed extraction.
The report script now tolerates absent temporary copies. Historical artifacts
were retained.

The first continuation completed seven additional sources (43 total). Those 43
records were imported into the private atomic store and verified by loading and
idempotently saving each one. The collector then adopted the atomic store for new
completion publication and resumed two disjoint source partitions. Setup writes
are serialized; each source has one collector. Each worker has a 1.5 GiB address
space cap, a 60-second soft CPU limit, a 65-second hard CPU limit, and a 70-second
alarm. The machine reported four logical CPUs and approximately 4.7 GiB available
memory before selecting two workers. No model API calls were made in this pass.

After both collectors stopped, all **62 records** loaded successfully and passed
idempotent save checks. The store and all records retained the required private
permissions. All 62 completed extractions exactly matched the saved index.

Coverage by document count differs substantially from coverage by content:
**6,476 of 47,429 chunk digests** are covered by those completed matches. The
remaining large books contain most of the indexed content. Fourteen catalog
records lack completed extraction evidence: twelve remaining candidates and the
two source-review cases. The uncataloged PNG is outside the 76 catalog records.
This is corpus progress, not a percentage of sprint completion or source truth.

Private evidence remains under `outputs/sprint21-extraction/private/`, including
`atomic-checkpoints/`, adoption/round-trip reports and collector scripts. The
aggregate is `outputs/sprint21-extraction/report.json`, regenerated at
23:39:11 UTC on 2026-11-12 after workers stopped. No runtime records or source text
are committed. Source PDFs, catalog rows, vectors and application routes were not
changed.

## Remaining work

Continue the large books from the retained source/policy bindings, handle OCR and
image intake explicitly, and resolve the pending Smith/Cook/both source choice.
The known mislabeled record and zero-text record remain review cases. Source
corrections, fresh runtime index validation, isolated migration/retrieval
integration, empirical/presentation acceptance and production release remain open.
