# Decision 53 independent verification

**DRAFT — NOT APPROVED FOR EXECUTION.**

Execution authorization: **DENIED**. This review concerns deterministic synthetic research; it does not establish institutional attribution, empirical accuracy, accepted structure, account authority or release readiness.

## Independence and inspected baseline

The verification role inspected the mission directly, Trading `docs/strategy/STRATEGY-001.md`, `packages/ict-model/index.js`, `packages/ict-model/context.js`, `services/market-data/timeframe-evidence.js`, `tests/unit/timeframe-evidence.test.js`, `research/governance/IMAF-OPERATIONAL-QUESTIONS.json`, both test entry points and Sentinel's prior v0.3 readiness report. It subsequently read the complete owner-supplied `/home/rain/Downloads/IMAF_Decision_Records_37-52.md`. That source explicitly labels every D37–D52 selection D, conceptual research governance only, and preserves unresolved predicates. No decision was reconstructed from an area summary.

Existing ICT strict research swings use `confirmedIndex`; that index alone cannot establish receipt-time availability or canonical structural significance. The new component therefore requires independent causal checks and must not promote old research MSS output into an accepted structural transition. All four existing canonical governance approval slots remain null.

The existing closed-timeframe helper is reused rather than duplicated. It requires closed complete windows, validates instrument/contract consistency, propagates delayed receipt and preserves source references. These references provide linkage, not source authentication.

## Verification design

`services/structure-research/adversarial.test.mjs` is owned by the independent verification role, separate from implementation tests. Expected recognition times are calculated from a hand-constructed five-bar fixture: the center opens 14:02 UTC, the first right bar closes 14:04, and the second closes 14:05. A late second right bar arriving 14:08 must delay five-bar recognition until 14:08. No implementation-provided expected timestamp is used.

The suite challenges unavailable future prices, overlapping three/five geometries, distinct technical observations sharing displacement ancestry, repeatability and input immutability, source-version identity, unresolved comparisons, equal-high ambiguity, gaps, ordering, duplicate bars, impossible availability, contradictory OHLC, missing extremum attribution, unknown profiles, structural-promotion injection and missing source versions. Independent checks also challenge the existing aggregation boundary for partial/mixed/gapped/unreceived data and directly verify its OHLCV arithmetic and late availability.

Evidence overlap bookkeeping is not a canonical independence predicate. Even disjoint source groups must retain `independent_confirmation_count: null`; no sufficient participation or confirmation predicate has been approved.

## Lifecycle and MSS boundary

A pure geometric detector cannot authorize or select an MSS reference. Every geometric observation must retain unresolved structural confirmation, significance and MSS-reference status. Retrospective reference selection, invalidated setup revival and expired setup revival require the replay/lifecycle seam and its separate tests; geometry alone cannot prove those lifecycle properties. The acceptance report must identify the actual replay tests rather than count geometry assertions as lifecycle coverage.

## Baseline execution reliability

Trading `tests/run.js` imports unit/adversarial tests directly into one Node process. `tests/integration/run.js` is a distinct entry point and is not included in that count. Run direct files under the deny-network preload. Do not use worker-level aggregate summaries as case counts. Relevant separate synthetic oversight, session and new research suites require their own explicit invocations.

## Executed results and findings

The independent suite was executed directly against the installed implementation under the existing deny-network preload:

```sh
node --import '/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs' services/structure-research/adversarial.test.mjs
```

Working directory: `/home/rain/Documents/ChatGPT/Sentinel Trading AI`.
Final result: **31 tests, 31 passed, 0 failed, 0 skipped, 0 cancelled**. Raw log: `/tmp/phase53-independent-final.tap` (retained copy linked in the aggregate acceptance report).

The initial 25-case run passed 24 and failed one assertion because the independent test expected the preliminary field name `structural_significance`; the implementation uses `significance`. Inspection confirmed that field remains `UNRESOLVED`. The test was corrected to the actual field without changing implementation behavior. Four additional independent tests then verified transitive ancestry overlap, disjoint bookkeeping never becoming confirmation, unavailable future ancestry isolation and cross-timeframe shared-extremum identity. That 29-case run passed before the subsequent semantic review below.

Subsequent root architectural review found an immutable-identity defect not detected by the initial 29 tests: the same raw extremum across one-minute and five-minute views retained one event ID but populated its event timestamp and availability from different parent bars. The independent suite had checked equal IDs but had not yet compared full immutable payloads. The implementation was corrected to retain `event_timestamp: null`, `available_at: null` and `raw_event_time: UNRESOLVED` for declared raw events whose tick time is unknown. Parent candle timestamps and actual receipt remain on the observation. A new independent full-payload equality regression directly compares both timeframe views and asserts the absence of invented tick times. Another test rejects an unqualified bare symbol to prevent silent delivery-month identity collapse. The final 31-case run passes against the corrected implementation.

No unresolved causal-integrity or authority defect was reproduced by the final suite. Geometry classification, source lineage and deterministic clocks are verified only for bounded synthetic fixtures. Declared raw event IDs are supplied research inputs, not authenticated independent exchange events. Receipt ordering gaps reject the snapshot; they are not interpolated. The suite does not establish real source correctness, source revision authority, canonical independence sufficiency, intrabar chronology, live session enforcement or full IMD/IMAF validation.

The comparison profile `STRICT_RESEARCH_V1` remains explicit research configuration. Omitting or inventing a profile is rejected, and `UNRESOLVED` never produces a geometrically completed conclusion. Equal extrema remain unresolved rather than resolved by an invented tie rule. All structural promotion assertions and the attempted injected MSS-reference flag fail closed.

The bounded pure evaluator has no selected-reference input or output authorizing a reference. Its unresolved `mss_reference` boundary is verified here; the dedicated causal replay tests provide actual historical selection rejection and lifecycle coverage. An absence of executable selection must not be presented as a complete structural-reference algorithm.

## Independent replay review and rerun

The independent reviewer read `services/structure-research/replay.mjs`, `replay.test.mjs` and `replay-worker.mjs` after installation and separately reran:

```sh
node --import '/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs' services/structure-research/replay.test.mjs
```

Result: **18 tests, 18 passed, 0 failed, 0 skipped, 0 cancelled**, raw log `/tmp/phase53-independent-replay.tap`. This rerun repeats the current 18 replay cases; it is not 18 additional unique test definitions. An earlier independent rerun passed the preceding 17-case suite. Root subsequently identified malformed boundary inputs whose parameter destructuring happened before the catch block. Destructuring now occurs inside guarded code, and the eighteenth regression verifies null, undefined, scalar, array and throwing-getter inputs remain denied without throwing. The independent reviewer inspected that correction and reran all 18 tests successfully.

Review confirmed that each cutoff recomputes only then-visible evidence; transitions retain candidate/observation identity, classification time, recognition time and dependencies. The restart test launches two actual child Node processes using file IPC, archives the original request, changes an unrelated current input file, and replays the archived request rather than the changed file. Dependency hashes include the evidence, geometry and replay modules plus Node/ICU/tz versions. Archive-integrity failure, changed dependencies and assessment mismatch remain explicit outcomes without a fallback to current input or an executable result.

The lifecycle seam accepts supplied synthetic original/proposed setup histories. Exact expiry rejects revival; changing discovery or expiry under the same setup identity is withheld; terminal identities cannot revive, and a new identity does not prove fresh discovery. This establishes fail-closed history reuse, not a market-derived invalidation detector or approved finite-expiry construction. The MSS seam always withholds structural selection; timely geometry cannot fill null confirmation/significance predicates. No additional actionable defect was found during this review. Missing source authenticity, model predicates, lifecycle-event authority and operational durability remain explicit limitations.
