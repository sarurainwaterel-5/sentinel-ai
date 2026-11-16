# IMAF canonical specification v0.3 — consolidated audit

**DRAFT — NOT APPROVED FOR EXECUTION.**

Version:0.3.0-draft. Baselines: Sentinel52d881d; Tradinga726709, with unrelated Trading
user edits preserved. Scope: documentation, contradiction/readiness audit and existing
offline validation. No executable policy version, predicate, runtime contract, risk
limit or routing authority changes. **Execution authorization: DENIED.**

## Review package

| File | Purpose |
|---|---|
| [Owner decisions17–36](OWNER_DECISIONS_17_36.md) | Twenty individual records with selected concept, source, dependencies, inputs and gaps |
| [Canonical doctrine matrix](CANONICAL_DOCTRINE_MATRIX_V0.3.md) | Source-supported principles vs owner extensions and incompatible promotions |
| [Predicate readiness register](PREDICATE_READINESS_REGISTER_V0.3.md) | Actual inventory,24 scoped records,18 required fields each, all null |
| [Evidence dependency graph](EVIDENCE_DEPENDENCY_GRAPH_V0.3.md) | Explicit first-model graph, eight circularity risks and independence requirements |
| [Temporal integrity audit](TEMPORAL_INTEGRITY_AUDIT_V0.3.md) | Knowledge/cutoff/ordering and actual session-window discrepancies |
| [First-model readiness](FIRST_MODEL_READINESS_V0.3.md) | What exists/is tested vs missing canonical qualification/authority |
| [Conflict report](DOCTRINE_CONFLICT_REPORT_V0.3.md) | Ten conflicts, implementation gaps and version-scope findings |
| [Implementation readiness](IMPLEMENTATION_READINESS_V0.3.md) | Actual tests, five blocker groups and short dependency-ordered owner queue |

Exact source hashes and paths: SOURCE_MANIFEST_V0.3.json. Sources are local inspected
files; no web doctrine substitutes for the manuscript. The full v0.9 PDF is accessible
and reverified by SHA-256 e170611529c68f674b5f4187515a8e6fba7e15624c365f844b750b82ffa06ece.
Fresh text extraction inspected relevant substantive sections; physical55 rendered
and visually inspected for Common Sources/External/Internal meanings. Prior reviewed
canon pages remain unchanged. No manuscript PDF is copied into Git.

## Exact manuscript source catalog

Physical pages are one-based PDF positions; printed handbook and Current Canon
labels are distinct. Citing a qualitative section never supplies a missing numeric
threshold, model geometry or implied institutional attribution.

| Key | Exact section / printed label | Physical PDF pages |
|---|---|---|
| C-PRE | Revision Note, Current Operational Sequence and later-doctrine rule, Current Canon2 |2|
| C-LADDER | Field Lesson3, Core Lesson IMD-FRM-002, Observation Ladder and reflection |24–26 (printed12–14)|
| C-TIME | Field Lesson6, Mission Brief/Core Lesson informational phases/Professional Principle |49–52 (printed37–40)|
| C-LIQ | Field Lesson7, Core Lesson, Common Sources, Liquidity Is a Destination, The Response Matters, External/Internal Liquidity; Evidence Box and review |55–57 (printed43–45); Mission Brief54 (printed42)|
| C-PART | Field Lesson8, Mission Brief; Core Lesson, Observation Versus Inference, Evidence Hierarchy, Participation Threshold, Commitment Versus Activity |59–62 (printed47–50)|
| C-AST | Field Lesson Accepted Structural Transition, Mission Brief/Core Doctrine/Professional Principle, Current Canon4 |67|
| C-PD | Field Lesson Price Delivery, Five Questions of the Institutional Auction and delivery tools, Current Canon5 |68|
| C-EX | Field Lesson Professional Execution, mechanisms/rules and No validated narrative principle, Current Canon6 |69|
| C-RISK | Field Lesson Professional Risk, risk domains, Current Canon7 |70|
| C-REV | Field Lesson Professional Review and404 Review, Current Canon8 |71|
| C-WORK | IMD Operational Worksheet, Current Canon9 |72|

Repository source keys:

- M4: current v0.3 mission attachment (exact path/hash in manifest), decisions17–36.
- P: Trading research/governance/proposals/imaf-operational-v0.1.json; response0,
  transition1, narrative2, discovery/expiry3 JSON array indices, all DRAFT.
- R: Trading research/governance/IMAF-OPERATIONAL-QUESTIONS.json, questions and boundaries.
- S/E: Sentinel backend/evaluation/synthetic_oversight/strategy/specification-v1.json
  and evaluator.mjs (evaluateStrategyReview); implemented research profile, not canon.
- Session: Sentinel backend/evaluation/session_governance_v02/specification.json,
  evaluator.mjs (evaluateSession), archive.mjs. Isolated synthetic outer guards.
- Trading geometry: packages/ict-model/index.js and context.js,
  packages/config/ict-research.js, services/signal-engine/ict-proposal.js.
- Trading governance: services/governance/imaf.js (buildImafDecision/validateImafEntry),
  research-operational.js/research-expiry.js; ADR-005 and IMAF-GAP-001 for source history.
- Existing reusable temporal controls: packages/market-calendar/src/index.js,
  services/market-data/calendar-manifest.js and session-timeframe-evidence.js;
  services/risk-gateway/index.js for independent session/account/risk constraints.
- Baseline reviews: docs/integration/imaf-v0.2/ all requested source documents;
  phase2/READINESS.md and phase3/READINESS.md for persistence and canonical blockers.

The source manifest identifies baseline blobs for predecessor documents later updated
only with current-review navigation. It does not pretend those historical bodies
have become executable v0.3 policy. Every existing executable source remains unchanged.

## Consolidated authority and conceptual sequence

Current Canon's later-approved terminology supersedes conflicting earlier eight-stage
wording. Preserve Time → Liquidity Objective → Liquidity Acquisition → Institutional
Participation → Liquidity Acceptance/Rejection → Accepted Structural Transition →
Price Delivery → Market Narrative → Professional Execution → Professional Risk →
Professional Review. Objective/acquisition are required2A/2B sub-stages of Liquidity
within the existing ten-stage serialization; no contract renumbering.

D1–D16 remain historical conceptual/session selections where not refined by D17–D36.
M4 supplies the named first model, exact morning windows and contextual distinctions;
these are now the current model scope. No need to ask which first model/windows
again. Four Pillars and Observation Ladder remain distinct evidence responsibilities.
Neither a LLM majority nor two calls into a shared evaluator establish independence.

## Initial model and session specification

Initial research model: **Liquidity Sweep → MSS → Displacement → FVG Retest**. These
are model components, not a universally rigid chronological sequence. Observable
acquisition is separate from significant liquidity, provisional rejection, confirmed
response, structural acceptance, participation and later delivery. MSS/displacement
may share observations but do not thereby become independent confirmations. Intrabar
ordering stays unknown when only unordered OHLC extrema support it.

All model policy times use **America/Chicago**:

| Discovery interval | Boundary meaning |
|---|---|
|07:30–07:35|Start inclusive, end exclusive|
|07:50–07:55|Start inclusive, end exclusive|
|08:10–08:15|Start inclusive, end exclusive|
|08:30–10:00|Start inclusive, end exclusive|

Morning discovery stops exactly10:00; no morning entry at/after10:15. Earlier
qualifying setups may continue developing within original finite expiry, including
outside a discovery window; a discovery window is not automatically an entry window.
Previously entered positions retain target/stop management after10:15; do not flatten
solely then. Afternoon discovery may start inclusively12:00 with genuinely new event,
identity, discovery, finite bound and independent IMAF review. No morning carryover
or noon daily-count reset. At15:00 remaining positions subject to mandatory flatten;
no new entry at/after15:00, and an unfilled target/stop cannot postpone the deadline.
Existing independent risk/calendar/account limits continue to bind.

A valid session does not establish a valid setup or account allowance. One trade per
approved exchange trading day, never presumed from a local date, supplied zero or a
new setup ID. Authentic calendar/count unavailable means stand aside for eligibility.
Timezone conversion uses IANA zones and UTC instants, not permanent hardcoded NY/CT
offset arithmetic. No real calendar coverage is verified in this audit.

## Lifecycle, recovery and evidence states

Model discovery type is qualifying liquidity interaction/sweep. Model expiry must be
finite, evidence-based, nonextending; exact deadline source/maximum lifetime remains
UNRESOLVED. DISCOVERED → DEVELOPING → CONFIRMED / INVALIDATED / EXPIRED remains the
conceptual lifecycle; no null qualifying/confirmation/invalidation predicate is filled.
Invalidated/expired setups cannot revive. Narrative recovery requires standaside,
preserved contradiction, fresh independently evaluated evidence/new discovery and all
session/calendar/risk/authority checks. It does not imply automatic reversal.

Separate candidate/confirmed/significant swing; raw wick breach/close beyond/
displacement-supported break; geometric/relevant/setup-qualified FVG; provisional/
confirmed rejection; acceptance; structural persistence; independent later delivery;
accepted transition and full narrative.78.6% is an owner-preferred contextual precision
level within an eligible range, not a stand-alone entry rule or a forced grid price.
No numeric candle counts, tolerances, volatility thresholds or expiry durations invented.

## Coverage and readiness

Primary conceptual classifications for D17–D36: 4
CANONICALLY_SUPPORTED, 11 SUPPORTED_BUT_UNDERSPECIFIED,
5 OWNER_SELECTED_EXTENSION. No direct manuscript
contradiction identified under the reviewed scope. All sufficient executable predicates
remain unresolved/unapproved:24 scoped definitions null, plus4 separate null governance
approval slots. Compound records still contain unsplit leaf obligations; count is not
proof of atomic coverage or readiness.

Existing suites:220 executed case assertions passed,0 failed/skipped. Separate13
read-only window comparisons found5 v0.3 mismatches. Passing old suites therefore
cannot certify v0.3. No new executable code, contract, source data or policy changed.
Full model validation/operational readiness remains NOT READY; the audit itself is
complete. First next owner decision is a measurable causal boundary/range/swing
reference contract; expiry source/rule follows for model lifecycle qualification.
See readiness report for exact dependencies, source gaps and remaining decisions.
