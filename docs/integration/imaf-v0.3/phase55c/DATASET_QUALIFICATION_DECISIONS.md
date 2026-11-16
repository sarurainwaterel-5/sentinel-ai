# Dataset qualification decisions

Phase 55C, November 16, 2026. **Both datasets: INSUFFICIENT_EVIDENCE. EMPIRICAL_CALIBRATION = BLOCKED.**

| Dimension | Dataset A — HFD monthly file | Dataset B — MarketParquet sample |
|---|---|---|
| Provenance | UNRESOLVED: local bytes verified; catalog filename matches, authenticated exact-file binding absent | VERIFIED for current provider-artifact identity: official anonymous download is byte-identical; original receipt unknown |
| Licensing | UNRESOLVED: exact monthly-sample use grant not established | UNRESOLVED: anonymous sample vs account/payment license scope needs clarification |
| Instrument | UNRESOLVED: MNQ filename claim only | DOCUMENTED_BUT_NOT_INDEPENDENTLY_VERIFIED: official artifact identifies root MNQ, upstream exchange origin not independently authenticated |
| Contract | UNRESOLVED: provider additive-continuous construction not bound to file generation/dated components | UNRESOLVED: ratio-adjusted continuous; April components/roll ratios/basis history unavailable |
| Calendar | UNRESOLVED dataset binding: scheduled exchange hours/DST verified; file bar label and availability unbound | UNRESOLVED dataset binding: scheduled hours/DST verified; Eastern bar-open documented; receipt/completeness/window review remains |

Statuses apply to the specific raw hashes in [the manifest](DATASET_QUALIFICATION_MANIFEST.json). A verified subfact does not promote an entire dimension. Provenance verification for B establishes delivery of these bytes by the official endpoint, not independent certification of the underlying exchange trades. The record does not reject either dataset: missing evidence is not a documented prohibition or integrity failure.

Neither receives APPROVED_FOR_RESEARCH or a provider-licensed RESTRICTED_TO_ENGINEERING_TESTS grant. The owner authorized this local evidence inspection and deterministic engineering; external sample rights remain unresolved. No empirical scope is permitted by this qualification record. Source bytes and derivatives stay private and outside Git.

B may be the shorter path to a narrowly defined adjusted-pattern study because provider-artifact binding and timestamp documentation now exist. That would still need explicit sample permissions, April adjustment/roll/as-of evidence, appropriate causal/completeness assumptions, and a separately reviewed adjusted-price research method. The present integer-tick calibration adapter only supports unadjusted identified dated contracts. Qualifying an adjusted pattern scope cannot silently enable it.

For the existing adapter, obtain authorized unadjusted identified MNQ contract observations (or a provider-authenticated zero-adjustment segment with proven lineage), bind timestamp/session/availability interpretation, and supply a separately reviewed five-dimension, scope-specific attestation. A generic symbol or month must never fabricate a contract. Exact exchange schedules are now captured; do not request them as if no progress occurred.

Supporting evidence: [provenance](DATASET_PROVENANCE_EVIDENCE.md), [license matrix](RESEARCH_LICENSE_MATRIX.md), [CME contract/calendar report](MNQ_CONTRACT_AND_CALENDAR_VERIFICATION.md). No calibration, threshold adoption, trading, deployment, push or merge follows from these decisions.
