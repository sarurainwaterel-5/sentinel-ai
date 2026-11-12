# Sprint 21 PDF worker and source triage — 2026-11-12

The corpus reconciliation remains quarantined. The reusable worker is read-only
and unregistered in the application. Production answering remains disabled;
ADR-037 remains Proposed and Sprint 21 remains open.

## Reusable extraction worker

`legacy_pdf_extraction_worker.run_worker` accepts explicit source and upload-root
paths, exact source SHA-256 and byte length, the extraction-code/parser policy
digest, and optional digest-only progress. It validates the source and policy
before parsing, refuses non-PDF signatures, reconstructs and verifies the pending
text tail for page resume, and streams the legacy-equivalent chunk digests.

It holds a non-symlink file descriptor and checks device, inode, size, modification
and change times plus a final full source hash. Even a same-content path
replacement is rejected. Progress and completion contain no document text, source
paths, filenames, or raw parser exceptions. A zero-text PDF emits `no_text`, not a
completed extraction. Collectors bind progress to the exact worker implementation,
source and policy and enforce process CPU, memory, wall-clock and output limits.

Independent review found a callback propagation mismatch. The worker now raises
the original collector exception immediately, without a retry or misleading
extraction event. Six regression cases cover callbacks failing at source,
progress, complete, no-text, failure and resume emission. The 22 focused worker
tests and related streaming/checkpoint/source/catalog coverage pass: **202 tests**.

## Actual source triage

A fresh upload manifest contains 78 regular files: 77 have PDF signatures and one
has a PNG signature. There are 77 unique content hashes. The source identities and
catalog metadata match the preceding read-only capture. This is not a distributed
snapshot or authenticated index/retrieval attestation.

The duplicate pair is a substantive title problem. The file stored under the Cook
suretyship filename and the file stored under the Smith equity-jurisprudence
filename have identical bytes. Visual inspection of pages 1, 2 and 7 shows
*A Manual of Equity Jurisprudence* by Josiah William Smith. The catalog calls
this content the Cook book. The checked installed-checkout copy has the same
incorrectly named content. No correct Cook source was located in these copies.
The title-review PDF, rendered pages and a proposed correction record remain
private. Neither original file nor the catalog record was renamed or rewritten.
If the Cook book is required, its correct source must be supplied or separately
obtained and reviewed. A user clarification about keeping Smith, Cook, or both is
pending; no migration-plan choice is inferred from silence.

The uncataloged chart file has a `.pdf` extension but a PNG signature. The actual
worker emitted `failed: invalid_pdf_header` and no completion. The original image
is retained; it requires an explicit image/OCR intake decision rather than being
silently treated as an indexed PDF.

The existing 18-page zero-text PDF emitted `source`, `progress`, and `no_text`, with
no completion. Its original is retained for OCR review. This historical record
still says `indexed` with zero chunks; the read-only audit did not repair it.

## Bounded execution evidence

The initial 20-second CPU budget stopped three small Qdrant documentation PDFs
before progress. A separately bounded diagnostic on Storage — Qdrant completed
four pages and two chunks in about 24.22 seconds of CPU time. Both ordered chunk
hashes match the retained index. That observed stop was a resource-budget limit,
not evidence of invalid PDF content. Subsequent batches use a 60-second soft CPU
limit, 65-second hard limit, 70-second alarm, 2 GiB address-space limit and per-page
progress. This changes the audit execution budget, not the extraction algorithm,
source text, catalog metadata, or empirical acceptance thresholds.

Private source manifests, pinned worker modules, implementation bindings,
checkpoints, execution logs, format-case evidence and the source-remediation
proposal are under `outputs/sprint21-extraction/private/`. Runtime data and source
text are excluded from Git. Exact ordered digest comparisons use the retained
47,429-point snapshot, not a newly authenticated production index. The aggregate
report remains `outputs/sprint21-extraction/report.json`.

Final counts from this bounded pass are recorded below. Completed extraction does
not imply correct titles, source truth, authorization, migration readiness or
production release. The remaining corpus, source-title correction, original Cook
source, OCR/image handling and fresh runtime integration/revalidation remain open.

## Final bounded-pass result

At 14:03:33 UTC on 2026-11-12, the retained aggregate contained **36 completed
unique source extractions and 36 exact ordered index-snapshot matches**. No
completed-source digest/count mismatch was observed. Forty catalog records do not
yet have completed extraction evidence in this pass, including the source-review
cases. The uncataloged PNG is outside those 76 catalog records. All 202 relevant
tests pass.

Independent review verified checkpoint integrity, source hash/length bindings,
ordered digest comparisons, and the historical/current worker component hash
definitions. Component integrity is not execution authentication. Earlier report
counts were intermediate observations while workers continued; the final aggregate
was regenerated after the workers stopped.

The private source-remediation record is a proposal only. The Cook-versus-Smith
book preference remains pending; no database correction or source replacement
was authorized by that proposal or performed by this pass.
