# Sprint 21 integration checkpoint — 2026-11-12

Sprint 21 remains open. Media intake and local video speech transcription are
implemented and deployed. This checkpoint adds tested storage, index-composition,
provider-review and current release-inspection work; it does not approve migration,
semantic acceptance or governed production answering. ADR-037 remains Proposed.

## Completed engineering and observations

- The full backend regression run passed **2,125 tests**, with three optional
  tests skipped. The final storage/provider/readiness/media selection passed
  **99 tests**, with one optional host image-decoder skip. The separate actual
  PostgreSQL/Qdrant rehearsal passed eight tests without skipping its real service
  check. The media frontend's preceding complete run passed 92 tests.
- The new bounded PostgreSQL 16 → Qdrant 1.18 → authoritative SQL-byte inspection
  rehearsal passed 14 rollback/readback/tampering/revocation/stale-completion
  observations. It uses two synthetic chunks and fixed vectors, not production
  credentials, corpus migration, embeddings or semantic accuracy evidence.
- The proposed content-addressed source store streams up to 1 GiB, verifies exact
  bytes and source stability, publishes exclusively, and fsyncs both newly created
  and adopted objects. It is isolated from live uploads. The v2 storage contract
  proposes paginated manifests suitable for the 64 MiB PDF text ceiling; its SQL
  references, chunk store and application publication barrier are not implemented.
- The separate selected-provider review harness is implemented with frozen input
  pins, explicit role credentials, at most 44 calls, strict budgets, no retries,
  durable private checkpoints and escaped exact-context review rendering.
  Its 36 scripted tests passed. The subsequent actual 44-call run completed with
  zero operational failures, one control relevance disagreement and two withheld
  generated candidates; see [the preserved result](Sprint-21-Provider-Result-2026-11-12.md).
- The additive read-only `/governance/release-inspection` workspace route consumes
  the current denial diagnostic and recomputes the saved Astra report's evidence.
  It keeps every approval, production and inference-opening flag false. Frozen
  governed-answer routes, main-module bytes and historical packet bindings remain
  unchanged. Real network-disabled image checks passed speech, silence, local
  embeddings/isolated indexing and the current release diagnostic.
- A fresh sequential observation of all **76 catalog rows, 78 source files and
  47,429 point digests** matched the retained audit inventory on two reads. These
  observations ran at 2026-11-13 00:55–00:56 UTC (November 12 in Chicago). They are
  not a distributed snapshot, authority attestation or release authorization.

Private evidence remains outside Git under the workspace's `outputs/` directory.
The actual corpus checkpoint and source-remediation proposal record their own
counts and limitations. No original source, existing catalog row or live vector
was changed by these audits. The Smith/Cook source-identity issue remains
quarantined even though Smith's ordered bytes match the retained index.

## Remaining work and decisions

1. The dictionary extraction finished: 75 documents and all 47,429 retained
   indexed chunks match re-extraction, with zero completed mismatches. The remaining
   image-only PDF has no indexed chunks and needs separate OCR review. This compares
   a retained snapshot; it does not attest current distributed index authority.
2. Review the concrete source-remediation proposal: retain Smith, add the separately
   verified Stearns/Cook book, and review page-bound OCR/image candidates before
   explicit catalog repair or reindexing.
3. The owner approved using the application key for Sol and Terra while retaining
   the separate Astra judge key. Explicit process-local assignments were used for
   the preserved evaluation; production configuration was not changed.
4. Review the completed selected-role Responses report, exact candidate text, full
   context and retained disagreements. The earlier 108-call Astra benchmark measured
   a different Chat Completions path and still needs its final human review.
5. Implement and review the actual application storage/lifecycle/outbox/authority/
   retrieval/publication composition against the final migration target. The new
   isolated checks are evidence for their bounded contracts, not a substitute.
6. Obtain exact empirical, independence, rendered-runtime and production-release
   acceptance. Agents cannot supply these attestations for the owner.

The current checkpoint can be reviewed and preserved. It does not establish that
only an approval remains, and it does not declare the entire sprint complete.

## November 13 engineering follow-up

The isolated chunk-object store adds exact bounded UTF-8 publication and verified
reads. All 48 focused source/chunk tests pass. It is not registered with intake or
retrieval. Versioned SQL references, paginated manifests and application publication
controls remain outstanding. The completed corpus comparison is saved privately in
`outputs/sprint21-extraction/corpus-weighted-audit.json`; source-title quarantine
and OCR review remain separate from exact byte matching.
