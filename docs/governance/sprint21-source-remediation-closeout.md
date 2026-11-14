# Accepted source remediation and remaining limits

The accepted owner packet authorizes additive Smith identity correction, separate
Stearns/Cook intake, and label-only PNG intake. It accepts only the listed partial
OCR corrections; it does not approve a complete transcription or production use.
The historical acceptance file remains unchanged.

## Apply Smith identity without altering source locators

1. Freshly read the legacy row `f29a29c6-0abb-45a4-b1d3-ecce65fb95ba`.
   Verify its file hash and original bytes are
   `f2dbc04c342058d33b29948f31aea64f3752d974325e26610dff0f158e7140dc`
   (14,737,587 bytes). Retain the observed original filename exactly.
2. In the installed governed schema, explicitly call
   `SourceIdentityOverlay(catalog).install()` once. This adds an isolated receipt
   table and immutable audit triggers. It does not alter any existing catalog
   table, filename, source object, vector or migration plan.
3. Call `record_smith` with the tracked acceptance file, its pinned
   `OWNER_ACCEPTANCE_SHA256`, observed filename and verified source hash.
   Save the returned receipt digest in the rollout evidence. Repeated identical
   calls return the same digest; different locator/identity records conflict.
4. Execute `admit_smith_after_identity` with the existing configured migrator,
   fresh complete inventory, complete Smith extraction checkpoint, current source
   path, pinned checkpoint policy and the saved identity receipt digest. This
   separate admission permits only the known Smith source, exact 1,130 chunk
   hashes/order, original filename, and `default/law/law/general` scope. It uses
   normal issued authentication, verified source/chunk CAS and atomic outbox.
   Keep `MANDATORY_QUARANTINES` unchanged in the bulk migration module. Wait for
   the governed worker's complete index verification before reporting searchable.

The receipt identifies *A Manual of Equity Jurisprudence*, Josiah W. Smith,
Fifteenth edition by Sydney E. Williams, 1900. Database triggers reject changes,
row deletion and truncation; ordinary privileged schema administration can still
remove the table, so retain its digest outside the database as audit evidence.

## Separate Stearns/Cook source

The approved candidate is the private
`sprint21-source-remediation/private/suretyship-stearns-cook-1922-archive.pdf`,
32,840,724 bytes, SHA-256
`57e76c5de835a1deb0f6cf715f99adbd910133ea05ad61b4bd821c41537dacff`.
Its identity is *The Law of Suretyship*, Arthur Adelbert Stearns, Third edition
by Wells M. Cook, 1922.

`prepare_cook_source(path, extractor=installed_server_extractor)` checks the
exact original before extraction and checks file identity again afterwards.
It returns text plus its digest and bibliographic identity. It performs no
writes. Use normal issued Rain authentication and existing authorized
`default/law/law/general` scope for a new governed document and version, with the
verified operator extraction-policy digest. Save the resulting source/version/manifest
and identity receipt. Never use Smith's document ID, chunk hashes or vectors.
The installed strict extractor must reject warning-bearing/empty extraction;
this is a real remaining extraction review if encountered, not permission to
silently weaken the policy.

## PNG and partial OCR

The chart's PNG source is SHA-256
`43a28f3bd51c303dd69a2e1c9aa19c79638d0a0d18d102d6cc13c291467427c4`
(116,774 bytes). Preserve it as a PNG with source-byte provenance. The retained
isolated OCR output is label text only and has no numerical-series, geometry or
market-claim verification. Store that limitation beside any derivative. The
current governed runtime deliberately rejects image OCR as searchable text;
source storage does not require promoting the derivative. After copying the
original into verified source CAS, call `record_chart_held` with the exact original,
retained `chart-isolated.ocr.txt` and original filename. It binds the exact accepted
68-character derivative SHA-256 and immutable limitations without search promotion.

The image-only PDF SHA-256
`fc6e847c46494d2f75d934e878291d9706ef01c5d9c1d10d3686d421ce86604f`
remains quarantined. Complete page-by-page proofreading, resolution of remaining
uncertainties, explicit complete-derivative acceptance and a bound reindex are
still needed before searchable transcription. Neither the existing acceptance
nor synthetic tests supply those missing human judgments.

## November 14 closeout execution

The immutable Smith identity receipt and its separate 1,130-chunk admission were
applied. The original filename, bytes and legacy catalog remain unchanged.
The chart original and exact accepted label derivative were retained in CAS with
an immutable held receipt; neither was promoted into searchable OCR.

The generic PDF timeout could not extract the 760-page Stearns/Cook source.
`operator_pdf_extraction.py` supplies a separate bounded, resumable embedded-text
workflow with per-page checkpoints. Its complete extraction verifies the exact
original, parser and implementation policy, all 760 ordered page hashes, and
aggregate text. Normal authenticated ingestion committed a separate document with
2,869 chunks. Live verification after deployment confirmed all 76 retained document manifests,
71 active documents, five archived denials and 50,281 active index points.
All retained source/chunk CAS hashes and the original public tables were checked.

The private 18-page OCR review packet is assembled; complete transcription
acceptance remains pending. The actual-corpus model review is implemented and
locally tested; external dispatch requires explicit approval of its prepared
four excerpts and at most six model calls. No production authority follows from
these source changes or local tests.
