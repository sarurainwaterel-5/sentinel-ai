# Sprint 21-B — Contracts and provenance

Implemented on `codex/sprint-21-b-contracts`, based on the reviewed local release
`462f32718d170b349f2acc0d4ef005718b867ece`. The supplied Sprint 20.3 checkpoint
`213fb04125b189adc2fc770f157e4e454b559644` and its branch remain untouched.

This milestone adds contracts and a pure offline registry only. No routes,
providers, frontend behavior, inference, ADR-037, benchmark artifacts or deployment
configuration changed. There is no production enable flag: release status is a
literal `disabled`, answer text must be null, and envelopes reject published claims.
Positive statement validation requires explicit gates and text/input hash bindings;
it does not override the release restriction or false grounding marker.

The request reuses ReasoningRequest normalization/bounds with strict parsing and
unknown fields forbidden. Caller-supplied organization remains filtering, not
authorization; future orchestration must resolve authenticated scope server-side.
The registry consumes a caller-supplied trusted catalog snapshot, not model output.
It checks organization, collection, document identity, status, hash, module/topic,
chunk locator and nonempty text, then issues deterministic IDs independent of
similarity and arbitrary source metadata. Excerpts use exact validated bounds.
Duplicate identities deduplicate; conflicting records with the same identity
invalidate the entire registry. Rejected entries retain bounded reasons.

EvidenceReference uses an explicit frozen projection of existing EvidenceSource
fields instead of embedding the mutable source model/metadata dictionary. No
model-generated metadata enters certification. Missing file hashes remain explicit;
existing hashes must match the catalog. The registry checks snapshot consistency,
not file authenticity or source truth. Catalog collection identity must be supplied
by the future storage adapter; no collection is invented for legacy sources.

Claim contracts reuse existing relationship references and statement decisions.
Single-premise free-form synthesis remains disallowed. Exact source reports are
representable but cannot be published by this disabled milestone. Conflicts,
unresolved relationships and uncertainty have separate fields. Constitutional
status is fixed to not_evaluated; no synthetic constitutional score is invented.

Next: 21-C may implement the offline injected coordinator and complete-context
coverage gate after approval. It must never treat partial registry output as full
coverage when rejection reasons exist. It must bind verdicts to exact candidate and
input hashes, reconstruct citations, forbid compatibility/fallback paths, and keep
Proposition → Inference closed. No existing judge thresholds may change. Empirical
20.3-G acceptance and explicit answer-presentation acceptance remain release gates.

Tests exercise enforcement with synthetic inputs only. They do not measure actual
semantic judge accuracy. No live benchmark or provider calls are part of 21-B.

## Validation

- Final new contract/provenance tests: 26 passed.
- Final targeted contract plus existing candidate, structural-grounding and
  independent statement-gate tests: 112 passed.
- Broad backend regression was interrupted after stalling without a reported
  failure; it is not recorded as a passing full suite.
- Protected benchmark, ADR-037 and inference paths remain unchanged from the
  supplied checkpoint. Existing tracked files were not edited by this milestone.
- No live provider or benchmark execution, frontend changes or deployment.
