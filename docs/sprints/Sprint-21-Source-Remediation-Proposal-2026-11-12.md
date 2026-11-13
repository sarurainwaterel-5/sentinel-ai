# Sprint 21 source remediation proposal — 2026-11-12

This is a reviewable source proposal. No catalog row, original upload, index point,
mission, release flag, or human acceptance record was changed by this work.
Private original paths, OCR candidates, and image renders remain outside Git.

## Correct the source identity while preserving both books

The two existing upload copies share SHA-256
`f2dbc04c342058d33b29948f31aea64f3752d974325e26610dff0f158e7140dc`
and byte length **14,737,587**. The original review render, page 7, identifies
*A Manual of Equity Jurisprudence*, Josiah W. Smith, fifteenth edition by Sydney
E. Williams, London, Stevens and Sons, 1900. The existing suretyship title is
incorrect for those bytes. Preserve both original files and correct the catalog
identity only through a separately reviewed metadata operation.

The actual suretyship book was obtained separately from
[Internet Archive's Cornell scan](https://archive.org/details/cu31924018855001),
with its [primary metadata](https://archive.org/metadata/cu31924018855001) retained
privately. Downloaded PDF page 5 visually confirms *The Law of Suretyship*, Arthur
Adelbert Stearns, third edition by Wells M. Cook, Cincinnati, The W. H. Anderson
Company, **1922**. The PDF has **760 scanned pages**, including front matter.
The archive's bibliographic metadata and the scanned title page agree. This is a
historical source candidate awaiting source review.

The separately downloaded candidate is **32,840,724 bytes**, SHA-256
`57e76c5de835a1deb0f6cf715f99adbd910133ea05ad61b4bd821c41537dacff`.
Its original URL, retrieval time, raw archive metadata, title-page renders, and
hash evidence are retained in the private remediation output directory. It was
not imported or substituted for the Smith source.

## OCR candidates remain separate from indexed evidence

The existing eighteen-page image-only PDF has source SHA-256
`fc6e847c46494d2f75d934e878291d9706ef01c5d9c1d10d3686d421ce86604f`
and byte length **1,893,408**. All eighteen pages were rendered locally at a
maximum dimension of 1,600 pixels. The cover is visibly a noisy, low-contrast
scan. A separate network-free container completed English Tesseract OCR for all
eighteen page images after normalization to a maximum dimension of 1,000 pixels
with one OCR thread. Seventeen pages produced nonempty candidates, totaling
**43,281 characters**; the cover produced no text. All per-page text digest
bindings and ordered page numbers were independently checked. These are private
derivatives, not a reviewed transcription. Source/page bindings and per-derivative hashes must be
retained before any ingestion. A nonempty OCR result alone does not prove
accuracy or repair the existing indexed/zero-chunk catalog state.

The uncataloged source with SHA-256
`43a28f3bd51c303dd69a2e1c9aa19c79638d0a0d18d102d6cc13c291467427c4`
and byte length **116,774** is visibly a chart PNG despite its PDF extension.
A private copy with a PNG extension preserves the exact original bytes. An isolated local OCR check completed and produced **68 characters** of candidate
labels. OCR may
capture labels; it does not capture all chart geometry or establish trading
conclusions. Use explicit image intake, retaining original-byte provenance.

## Concrete operations awaiting review

1. Correct the Smith catalog title while retaining original source bytes and
   recording an auditable metadata change.
2. Add the separately verified Stearns/Cook source as its own document through
   normal intake; do not replace Smith or inherit its existing point identities.
3. Review page-bound OCR candidates for the image-only PDF before creating a
   linked derivative and performing an explicit reindex operation.
4. Admit the chart through explicit image intake if required, preserving the
   original hash and recording OCR limitations.

These source operations do not supply human gold labels, semantic acceptance,
authorization evidence, or permission to enable production. The existing
quarantine and release boundaries remain in force.
