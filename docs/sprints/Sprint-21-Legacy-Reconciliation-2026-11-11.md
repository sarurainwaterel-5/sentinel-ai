# Sprint 21 legacy reconciliation — 2026-11-11

The bounded read-only capture is **quarantined**. It does not establish migration
readiness, verified indexing, authenticated retrieval, or release permission.
Production answering remains disabled and Sprint 21 remains open.

## Actual observations

At 19:00:09 UTC, the running Sentinel application had 76 catalog records and
47,429 Qdrant points. Catalog metadata matched before and after capture; two
bounded Qdrant scrolls matched. These observations are not a distributed snapshot.

The upload directory contains 78 regular PDFs and no symlinks. Seven files exceed
the collector's 20 MiB bound and were skipped. Of the 71 captured file hashes,
69 catalog records have matching hashes. Seventy-five catalog document IDs have
indexed points. These counts alone do not verify chunk manifests or source truth.

Six source extractions completed within the bounded pass. Extraction remains
incomplete. One catalog record has an invalid chunk count under the reconciliation
contract. Strict validation therefore withheld all per-document classifications;
no document was established ready for migration review. The initial slower pass
was stopped without retaining its partial in-memory extraction results.

## Implementation and evidence

`evaluation.governed_answers.legacy_reconciliation.reconcile_inventory` is a pure,
bounded auditor. It checks exact schemas, capture completeness, unique document,
source and point identities, source hashes, scope and model metadata, contiguous
ordered chunks, and source extraction digests. Duplicate catalog file hashes also
quarantine affected records. Reports omit filenames, source text, credentials,
and raw document identities. All eligibility, index, epoch, authorization and
release flags remain false even when metadata agrees.

The private digest inventory and collector scripts remain outside Git under
`outputs/sprint21-reconciliation/private/`; the sanitized report is
`outputs/sprint21-reconciliation/report.json`. The extraction implementation hashes
match this checkout. Current extraction code does not prove historical policy.

Validation: 63 tests passed across reconciliation and disposable SQLite catalog
coverage. Independent review identified the duplicate catalog hash edge case; its
fix has a regression test. No source rows, PDFs, vectors, or application routes
were changed.

## Next work

Inspect the invalid chunk-count record and the seven oversized PDFs through a
bounded private diagnostic. Extend the capture with streaming hashes and a
resumable extraction worker, then rerun exact ordered digest reconciliation.
Preserve mismatches as quarantined evidence; do not repair, delete, or reindex
legacy data automatically. After reconciliation, implement the reviewed isolated
migration/index/retrieval integration. Human empirical acceptance and the remaining
provider, answer, presentation, and release gates still apply.
