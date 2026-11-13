# Sprint 21 owner review packet — 2026-11-13

A private, self-contained HTML packet is prepared at workspace
`outputs/sprint21-owner-review-20261113/owner-review.html`. It embeds the 18
unmodified scan renders, both book title pages and all 19 exact saved
selected-provider rows. It offers separate decisions; it cannot save or submit
approval. No live catalog, original source, frozen label or acceptance record
was changed.

Agent visual inspection covered all 18 renders. A **new unreviewed partial OCR
derivative** corrects selected clear omissions/characters on ten pages while
preserving every original candidate. The derivative manifest binds every page's
source/render/original/candidate hashes and exact correction log. It is not a
complete verified transcription. Extensive numbering/layout problems and word
errors remain, especially in the dense two-column pages. The dark cover and dark
final right-hand page are unresolved, not certified blank. No facts, photograph
identities, historical claims or bibliography were verified by transcription.

Correction to the initial agent spot-check: page 2 itself prints `PYSCHE`; that
source spelling is retained. The earlier claim that it printed `PSYCHE` was
incorrect. Only the clearly discrepant final `RECALL,` punctuation was corrected
on that page. Source spellings are not silently normalized.

Private artifacts in the packet directory:

- `owner-review.html`, SHA-256
  `5d764d4d2f2e95a0994a1c467909f3c6256df184ddbc0edaced57bd8b35c931f`.
- `ocr-derivative.unreviewed.json`, SHA-256
  `f5ab4abfc75794da222b3ca7c8eedf9909915f81ba9a2a34b39f43c99797d044`.
- `page-01.candidate.txt` through `page-18.candidate.txt`, plus
  `all-pages.candidate.txt`; original OCR remains in its previous directory.
- `source-correction-plan.proposed.json`, bound to the saved catalog observation
  and exact source hashes; current live state must be revalidated before applying.
- `packet-bindings.json` and the preparation script `build_packet.py`.

The Smith correction plan preserves original bytes and the existing filename
locator. The current `Document` model has no distinct canonical title field;
an audited additive identity metadata change must be designed before applying a
bibliographic correction. The separate Stearns/Cook book receives a new identity
through verified intake; it cannot replace Smith or reuse its vectors.

The concrete owner choices are:

1. Accept, correct or defer Smith's displayed bibliographic identity.
2. Approve separate Stearns/Cook intake, request more provenance or defer.
3. Accept specified OCR corrections only, request further proofreading
   (recommended while the listed errors remain), or retain stored-only.
4. Admit the chart through PNG intake with label-only OCR limitations, retain
   stored-only or defer.
5. Accept/reject/defer each of the six generated outputs and adjudicate the Terra
   certainty/Astra causality observations under the frozen evaluation protocol.
6. Accept/reject/defer the earlier exact Astra benchmark's limited empirical
   result and independently assess provenance/deployment independence.

Owner identity, time and substantive dispositions remain unset. None of these
choices alone authorizes production. The subsequent application lifecycle/outbox and inspection publication components
are implemented and tested on disposable services; reviewed installation, real-corpus
operational checks and bound release authorization remain pending. See
[the current handoff](Sprint-21-Implementation-and-Review-Handoff-2026-11-13.md). See the
[writer inventory](Sprint-21-Application-Writer-Inventory-2026-11-13.md) and
[detailed unanswered decisions](Sprint-21-Remaining-Owner-Review-2026-11-13.md).

Validation parsed the HTML: 20 embedded original PNGs, all 18 page anchors and no
scripts. Every new candidate hash and false owner/completeness flags were checked.
This structural check does not assert that a browser render or human review occurred.
