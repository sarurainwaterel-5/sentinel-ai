# Sprint 21 resumable legacy extraction — 2026-11-11

The reconciliation remains quarantined. These changes preserve completed audit
work and allow bounded extraction of large reference documents; they do not grant
migration eligibility or enable production answering.

## Implementation

`legacy_extraction_checkpoint` binds completed chunk digests to the exact source
SHA-256, source byte length, extraction implementation hashes, and parser version.
It accepts only strict, intact, complete records, with at most 100,000 chunk hashes
and a 1 GiB source. Failed, partial, stale, or changed records cannot be reused as
completed extractions. Integrity hashes detect changes; they do not authenticate
execution or authorize source access.

`LegacyChunkDigestStream` processes pages with the same nonempty-page newline,
1,000-character chunk size, and 800-character stride as the legacy pipeline. It
holds fewer than 1,000 pending characters between page feeds. Its progress snapshot
contains only digests and counters. Restoring requires source/policy binding by
the caller and the exact pending tail reconstructed from the PDF; no text tail is
persisted. Only finalization after all pages marks completion.

Independent review found an impossible restored page-boundary state; validation
now rejects positive totals below two characters and missing trailing newlines.
Regression tests cover this, exact legacy equivalence, Unicode, overlap, malformed
snapshots, failure states, source/policy changes, defensive copies, and bounds.
All 180 relevant tests passed across streaming, checkpoints, source capture,
reconciliation, and disposable SQLite catalog coverage.

## Actual diagnostics

The zero-chunk legacy record is *103 Amazing Facts About the Black Indian of the
Western Hemisphere*: 18 pages, zero pages with extractable text, zero extracted
characters using pypdf 6.13.3. Its legacy status is `indexed` despite zero chunks.
The source is retained for OCR review. The current upload implementation rejects
new zero-text uploads; that guard does not repair this historical row.

Two bounded file-level batches saved seven completed source checkpoints. A
streaming pass completed all 78 pages of *Institutional Market Dynamics*, producing
112 chunk hashes. All eight completed sources matched their exact ordered chunk
hashes and counts in the retained index snapshot. The first streaming implementation
used for that document is preserved privately with its own implementation digest;
it predates the subsequent strict restore fix, and did not restore a partial state.

*Law of Suretyship* completed all 760 pages, producing 1,962 chunk hashes that
exactly match the ordered retained index and catalog count. Bounded workers
actually stopped and resumed at pages 81, 144, 204, 272, 336, 404, 470, 528, 598,
680, and 735. Pending tails were reconstructed from source pages and digest-checked;
only the final worker declared completion. These terminations are expected bounded
progress stops, not successful completed extractions on their own.

The final aggregate contains **nine completed source extractions and nine exact
ordered snapshot matches**, with no completed-source digest mismatch observed.
This is partial corpus coverage. File-level timeout statuses are retained as
historical attempts even when a later streaming run completes the same source.
Partial progress never counts as a complete source verification.

Four earlier private worker starts failed before extraction because of a local
worker syntax error. They produced no progress or completed checkpoints. The
corrected worker passed a syntax preflight before the successful resumed run.

The 78 source files contain 77 distinct content hashes: one hash occurs twice,
and one distinct hash is absent from the catalog. These observations require
review; no duplicate or unreferenced PDF was removed.

## Evidence and remaining limits

Private inventories, checkpoint records, page-progress logs, pinned worker code,
and reproducibility scripts are under `outputs/sprint21-extraction/private/`.
The sanitized aggregate report is `outputs/sprint21-extraction/report.json`.
No document text, credentials, source filenames from the inventory, or private
runtime records are committed. The source PDFs, catalog rows, and Qdrant points
were not changed.

Digest comparisons refer to the retained read-only index snapshot. They are not
a distributed current snapshot, a source-truth assessment, authenticated retrieval,
or release approval. Full extraction across all sources, the zero-text/OCR case,
duplicate/unreferenced-source review, current revalidation, isolated migration and
retrieval integration, and human acceptance remain open. ADR-037 remains Proposed
and the Proposition → Inference boundary remains closed.
