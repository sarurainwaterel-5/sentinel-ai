# Sprint 21 remaining owner review — 2026-11-13

Prepared by an analysis agent from the exact saved evidence. This packet records
unanswered decisions; it records **no human acceptance**, source mutation or
release authorization. ADR-037 remains Proposed and proposition-to-inference
remains closed. Application integration remains work even after these reviews.

## Evidence checked independently

The selected-provider JSON has SHA-256
`c51575a020cc9e6edbe5ebd80d3b93e04fcdebd5c382665b96999a801632a364`.
It contains 19 rows and 44 completed steps: six generation, 19 statement and 19
relevance. Each canonical request hash, exact response-text hash, parsed response
and relevance request-hash echo was independently recomputed and matched. There
are ten review previews and nine withheld rows, with no structural rejections or
operational failures. All acceptance and release flags remain false.

Exact private JSON and escaped HTML are outside Git at
`outputs/sprint21-provider-review/private/sol-astra-terra-20261112-run1.{json,html}`
under the workspace parent of this repository. Review the HTML alongside the JSON;
the HTML includes sources, premises, relationships and withheld candidates.
The report records local execution observations rather than independent provider
attestation. See [the run record](Sprint-21-Provider-Result-2026-11-12.md).

## Selected-provider decisions still unanswered

| Item | Preserved result | Decision needed from owner |
|---|---|---|
| All 13 fixed controls | Astra matches 13/13; Terra matches 12/13; combined six previews, seven withholds | Accept or reject this bounded run's observations and limitations as evaluation evidence. Do not relabel the controls in response to this run. |
| Control `certainty` | Expected statement=false, relevance=false; Astra=false, Terra=true; withheld | Record whether the Terra disagreement is an unacceptable relevance behavior under the existing policy and whether a separately versioned future policy/protocol is needed. Preserve this run and frozen labels. |
| Generated `faithful-paraphrase` | Astra=true, Terra=true; preview | Review statement and qualification, including the qualification that requirements do not grant execution authority. |
| Generated `multi-premise` | Astra=true, Terra=false; withheld | Decide whether withholding is appropriate when the question asks which records are required but sources establish only that records are retained. |
| Generated `qualification` | Astra=true, Terra=true; preview | Review both the possible-recovery condition and the distinction between no reported guarantee and proof that none exists. |
| Generated `conflict` | Astra=true, Terra=true; preview | Confirm the candidate preserves disagreement between reports without deciding the underlying approval rule. |
| Generated `uncertainty` | Astra=true, Terra=true; preview | Confirm the answer preserves an unestablished cause and treats credentials only as a possible explanation. |
| Generated `causality` | Astra=false (`unsupported_fact`), Terra=true; withheld | Review whether Astra rejected a faithful statement, or identify the exact unsupported portion. Do not manually override the saved withholding or certify unseen accuracy. |

For `certainty`, the source says recovery **may** occur with a valid backup and
the backup is not validated. The candidate asserts recovery is certain. Terra's
returned reason explicitly acknowledges unsupported certainty while calling the
candidate a direct answer. This suggests a distinction between topical/direct
response and an adequately supported answer. That is an analysis observation,
not permission to change the meaning of the frozen relevance label.

For generated `multi-premise`, Sol states that Cedar retains the source document
and approval record, and qualifies that the premises do not establish a retention
requirement. Terra withholds because the question asks what is required. The
qualification makes the limitation visible; it does not manufacture the missing
requirement. The owner must review the desired behavior for this precise case.

For generated `causality`, the sources explicitly report an injected wait caused
a delay and that the wait lasted two seconds. Sol attributes those claims to test
C1 and qualifies that the duration of the delay itself is not established. On its
face, the statement preserves both claims and distinguishes their durations.
Astra nevertheless returns `unsupported_fact` without locating a disputed span.
The report supplies no more specific explanation. This is a potential false
rejection requiring adjudication, not an established false rejection or proof
that the combined system is accurate. The row remains withheld.

These six generated candidates have no new human gold labels. Four previews are
reviewable candidates, not approved answers. Nineteen rows are not nineteen
independent production tasks and do not validate real retrieval, deployed
citations, chart interpretation or unseen documents.

## Separate Astra empirical acceptance

The earlier [108-assessment Astra benchmark](Sprint-21-Astra-Empirical-Result-2026-11-11.md)
uses report SHA-256
`922844683321ebf816cc56d40c701dd0f002e3b902a7aa25f5ed8446fc860d32`.
The 36 reviewed synthetic cases were repeated three times. Its measured
classification accuracy and decision stability are 100%, with no recorded errors.
Its Chat Completions transport differs from the later Responses composition.
Neither run extends the other's measured scope automatically.

The owner still needs to review execution provenance, deployment independence,
the unchanged preregistered thresholds and the limited scope before completing
`backend/evaluation/semantic_judge/results/astra-20261111-run1.review.pending.json`.
Reviewer identity, timestamp and acceptance choices must come from an actual
review. A dedicated credential alone does not establish model independence.
The pending record is not a production release approval. Existing approved frozen
answer/presentation fixture records also do not accept these new live outputs.

## Source identity and intake decisions

Independent visual inspection confirmed the saved Smith title-page render
`outputs/sprint21-extraction/private/title-007.png`: *A Manual of Equity
Jurisprudence*, Josiah W. Smith, fifteenth edition by Sydney E. Williams,
Stevens and Sons, London, 1900. The saved two-copy hash evidence identifies
14,737,587-byte source SHA-256
`f2dbc04c342058d33b29948f31aea64f3752d974325e26610dff0f158e7140dc`.
A catalog label describing this as the Cook suretyship book is wrong even when
its extracted bytes match existing indexed chunks.

Independent visual inspection of remediation `cook-title-05.png` confirmed the
separate *The Law of Suretyship*, Arthur Adelbert Stearns, third edition by Wells
M. Cook, The W. H. Anderson Company, Cincinnati, 1922. Its local PDF size and
SHA-256 were independently recomputed: 32,840,724 bytes,
`57e76c5de835a1deb0f6cf715f99adbd910133ea05ad61b4bd821c41537dacff`.
The retained archive-integrity record reports matching length, MD5 and SHA-1.
This review made no new external requests and relies on the retained acquisition
evidence described in [the remediation proposal](Sprint-21-Source-Remediation-Proposal-2026-11-12.md).

Unanswered source dispositions:

1. Accept the Smith identity correction and specify the affected catalog entries
   in an auditable metadata operation, preserving both original files and source
   hashes. Decide how existing displayed citations and title-dependent metadata
   will be refreshed without pretending the source bytes changed.
2. Accept the separate Stearns/Cook candidate for normal intake as a new document.
   It must receive its own identity, provenance and index lifecycle; it must not
   replace Smith or inherit Smith's point identities.
3. Review and correct the image-only PDF's page-bound OCR before accepting a
   linked derivative and an explicit reindex operation.
4. Decide whether the chart should be admitted through image intake, preserving
   its original PNG bytes and describing the limited OCR output as labels rather
   than a structured representation of chart geometry.

## OCR evidence and concrete review defect

The eighteen-page image-only source is 1,893,408 bytes, source SHA-256
`fc6e847c46494d2f75d934e878291d9706ef01c5d9c1d10d3686d421ce86604f`.
Independent checking of all 18 saved page rows confirmed ordered page numbers,
render-file hashes, text-file hashes and character counts: 17 nonempty pages and
43,281 characters. Combined candidate text is 44,839 UTF-8 bytes, SHA-256
`debf1b9daa440542567af16b65661cae83326edee8ff80ebb6e530eaebf964fb`.
These checks prove consistency of saved artifacts, not transcription accuracy.
The normalized-image digests were not independently recomputed because those
normalized images are not separately retained beside the manifest.

A visual spot check of page 2 against `ocr-bounded/zero-text-page-02.txt` found
concrete OCR errors: the scan prints **PSYCHE**, but the candidate says
**PYSCHE**; the final **RECALL.** is rendered as **RECALL,**. Thus the current
candidate cannot be accepted wholesale on the basis of hash verification or
nonempty text. All pages still require transcription review. Preserve the
original candidate, record corrections as a new derivative with new hashes,
retain page/source bindings, and record illegible or uncertain passages rather
than silently guessing. The cover has no candidate text and still needs a
visible empty/unreadable disposition. No derivative is currently accepted or
indexed by this packet.

The mislabeled chart file is visibly a PNG. Its recomputed size and SHA-256 are
116,774 bytes and
`43a28f3bd51c303dd69a2e1c9aa19c79638d0a0d18d102d6cc13c291467427c4`.
The isolated OCR record reports 68 characters. The image visibly contains
candlesticks, axes and indicator values that this label text does not fully
represent. Intake must not imply numerical series extraction or verified market
claims. Renaming a private copy to PNG preserves its bytes but does not repair
catalog state or establish image-reading completeness.

## Recording the owner's review

For each decision, retain the exact artifact hash, reviewer identity, review
time, accepted/rejected/deferred disposition, rationale and approved next action.
Keep semantic-output acceptance, source intake/derivative acceptance and final
release authorization distinct. An instruction to put agents on remaining work
does not itself supply the missing substantive review judgments. Agent findings
may prepare the records; they cannot attest that a human inspected the artifacts.
No production flag should change as a consequence of this document.
