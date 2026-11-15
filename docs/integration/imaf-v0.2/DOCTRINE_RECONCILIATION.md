# IMAF canonical specification v0.2 — doctrine reconciliation draft

Date: 2026-11-15. Status: PARTIAL_REVIEW_DRAFT_AWAITING_MISSION_REMAINDER.
Conceptual owner decisions are authoritative preferences, not approved executable
predicates. No strategy, schema, pin, registry, calendar or authority change.
This document reconciles supplied mission sections 1–4. The attachment ends at
`5. FORMAL PREDICATE DESIGN`; its requirements and later sections are unavailable.
Do not treat this document as completion of that missing scope.

## Ownership, provenance and precedence

The existing Trading proposal `research/governance/proposals/imaf-operational-v0.1.json`
remains the predecessor for operational research. Its DRAFT_FOR_OWNER_REVIEW status
and four null approvedDefinition registry entries remain intact. This is a review
companion, not a competing approved doctrine or a runtime replacement specification.
Future v0.2 operational definitions should evolve that lineage after reconciliation;
no executable predicate is approved by this review.

Source keys below are repository-relative, with exact SHA-256 in SOURCE_MANIFEST.json:

- **M**: owner's supplied canonical v0.2 mission, sections 2–4 and Decisions 1–12.
- **C**: IMD Living Manuscript, Sentinel Training Edition v0.9, SHA-256
  `e170611529c68f674b5f4187515a8e6fba7e15624c365f844b750b82ffa06ece`.
  Fresh extraction inspected physical pages 2, 20, 24–26, 59–62 and 66–73.
  Rendered physical pages 2 and 72 inspected visually. Printed Current Canon page
  labels differ from physical PDF positions: CC2=physical2; CC4–9=physical67–72.
- **P**: Trading `research/governance/proposals/imaf-operational-v0.1.json`;
  references use JSON pointers, definitions indices 0=response, 1=transition,
  2=narrative, 3=discovery/expiry.
- **R**: Trading `research/governance/IMAF-OPERATIONAL-QUESTIONS.json`;
  four question IDs remain unapproved. `boundaries` remain separate hard limits.
- **T**: Trading `services/governance/imaf.js`, `IMAF_CANON`, `ICT_TIMEFRAMES`,
  `evaluateImaf` records; `docs/architecture/ADR-005-imaf-governance.md`.
- **S**: Sentinel `backend/evaluation/synthetic_oversight/strategy/specification-v1.json`;
  `rules`, `mission_policy`, `hierarchy`, `unresolved`, `additional_unresolved`.
- **E**: adjacent `evaluator.mjs`, `evaluateStrategyReview`, observation rule IDs
  cited below. This describes current behavior by inspection, not a new test run.
- **G**: Sentinel `docs/integration/phase3/SPECIFICATION_COVERAGE.md`,
  `PROPOSED_DEFINITIONS.md`, `READINESS.md`.

Precedence: C's explicit later-approved-doctrine rule supersedes historical eight-stage
wording. M adds authoritative conceptual choices without approving operational
parameters. P and S remain research artifacts. Neither their code nor numerical
precision can promote them to manuscript doctrine. Differences remain explicit;
immutable historical specifications/results must retain their original meaning.

## Sequence and evidence dependencies

| Owner checkpoint | Name | Existing canon stage |
|---:|---|---|
| 1 | Time | 1 |
| 2 | Liquidity Objective | 2A (Liquidity) |
| 3 | Liquidity Acquisition | 2B (Liquidity) |
| 4 | Institutional Participation | 3 |
| 5 | Liquidity Acceptance/Rejection | 4 |
| 6 | Accepted Structural Transition | 5 |
| 7 | Price Delivery | 6 |
| 8 | Market Narrative | 7 |
| 9 | Professional Execution | 8 |
| 10 | Professional Risk | 9 |
| 11 | Professional Review | 10 |

Classification: CANONICALLY_SUPPORTED (C CC2 and CC9; M section2). Eleven
checkpoints preserve both required liquidity sub-stages in the ten-stage canon.
Do not renumber T's serialized ten-stage records or agent scopes in this mission.
A future contract migration would need explicit compatibility review.

The objective must precede acquisition reasoning; acquisition evidence precedes
participation/response conclusions; accepted structural transition depends on the
preceding auction evidence. Price-delivery confirmation for transition must be
recorded as time-stamped observations, not as a circular reference to an already
completed later-stage narrative. Full Price Delivery and Market Narrative then
synthesize the preceding chain. Later context may support a new assessment; it cannot
retroactively alter an earlier one. Professional Risk remains independently binding
before any action despite its position in the pedagogical sequence. Professional
Review cannot be completed before the relevant outcome exists.

Four Pillars remain Observe, Reason, Execute, Improve (C physical20). Every checkpoint
retains Observe, Describe, Differentiate, Interpret, Hypothesize, Verify, Decide (C
physical24–26). Observations, inferences, hypotheses, alternatives and unknowns must
remain distinct. Evidence available after a cutoff belongs to later verification.

## Decision-by-decision reconciliation

Classification applies to a specific assertion relative to cited sources. A broad
concept can be supported while an exact formulation is a PROPOSED_EXTENSION and its
machine predicate remains UNRESOLVED. CONTRADICTORY below describes old research
semantics relative to M, not a rejection of the owner's conceptual choice.

### D1 — Initial liquidity rejection

**Classification:** SUPPORTED_BUT_UNDERSPECIFIED. C CC9 and physical25 distinguish
observed return through a boundary from inference; neither defines a quantitative
provisional-rejection test. M D1 selects sweep + qualifying return + displacement
as provisional only. Exact qualifying return/displacement are UNRESOLVED.

**P:** `/definitions/0/proposal/rejection` requires a pair of subsequent closes;
`decision` calls that provisional. It does not express M's initial route. The pair,
three-bar horizon and one-tick rule remain proposed parameters, not selected doctrine.
**S/E:** `rules`, STRICT_SWEEP and RESEARCH_DISPLACEMENT compute a research sweep
and displacement separately; no canonical provisional rejection is produced. A sweep
alone is not a reversal. **R:** LIQUIDITY_ACCEPTANCE_REJECTION_OPERATIONAL_DEFINITION
remains null. **v0.2 disposition:** preserve the initial/confirmed distinction; do
not relabel the existing sweep observation as canonical confirmation.

### D2 — Contextual rejection confirmation

**Classification:** SUPPORTED_BUT_UNDERSPECIFIED. C physical60–62 requires converging
independent evidence; CC4 gives preceding context weight. M D2 permits structural
confirmation OR persistence when contextual sufficiency is established. Route
eligibility and sufficiency are UNRESOLVED; no universal AND or unconditional OR.

**P:** `/definitions/0/proposal/rejection` supplies only a close-persistence pattern;
`/definitions/1/proposal` adds structural sequencing but no context-dependent route
selector. The draft is incomplete for M. **S/E:** canonical response/transition
observations are UNRESOLVED; RESEARCH_MSS_AFTER_SWEEP is not accepted transition.
**R:** response and transition questions remain null. **v0.2 disposition:** document
each route's prerequisites, contradictory evidence and availability separately once
specified; neither route may self-certify context with a caller boolean.

### D3 — Rejection invalidation

**Classification:** SUPPORTED_BUT_UNDERSPECIFIED; exact reclaim/acceptance predicates
UNRESOLVED. C physical24–26 requires falsifiable hypotheses and revised conclusions;
M D3 specifically requires a qualifying reclaim accompanied by opposite acceptance.

**P:** `/definitions/0/proposal/invalidation` invalidates on an opposite close alone.
That is CONTRADICTORY to M if promoted as canonical rejection invalidation; a
conservative research suspension is a different decision. A temporary crossing must
not be silently upgraded to acceptance. **S/E:** no canonical rejection lifecycle;
RESEARCH_MSS_AFTER_SWEEP/STRICT_SWEEP do not resolve this gap. **R:** response
question explicitly asks contradictory evidence/invalidation and remains null.
**v0.2 disposition:** retain the original provisional record; later qualifying
invalidation requires linked reclaim AND acceptance evidence. Missing acceptance
cannot manufacture invalidation or certify continuing coherence.

### D4 — Institutional participation

**Classification:** CANONICALLY_SUPPORTED for contextual convergence and limits on
attribution (C physical59–62); SUPPORTED_BUT_UNDERSPECIFIED for measurable sufficiency.
M D4 uses higher objectives, liquidity behavior, displacement and subsequent delivery.
Displacement alone does not prove control; OHLCV does not identify institutions.

**P:** `/definitions/2/proposal/requiredRelations/3` and `participationProposal`
require distinct bar sets for displacement and later structure. This is a
PROPOSED_EXTENSION for a particular independence implementation; disjoint bars alone
do not establish distinct information or contextual sufficiency. **S/E:**
RESEARCH_DISPLACEMENT and observation_ladder.Interpret avoid participant attribution;
INDEPENDENT_PARTICIPATION_CRITERIA remains unresolved. **R:** narrative question
includes contradictory participation but does not approve an independence test.
**v0.2 disposition:** preserve evidence lineage/dependence, alternatives and supporting
vs contradictory evidence; do not count renamed FVG/displacement labels twice.

### D5 — Accepted structural transition

**Classification:** CANONICALLY_SUPPORTED for contextual acceptance beyond a line
break (C CC4); PROPOSED_EXTENSION for M's explicit requirement that both structural
persistence AND price-delivery confirmation be present. Their exact predicates are
UNRESOLVED; the conjunction is an owner conceptual choice.

**P:** `/definitions/1/proposal/sequence` uses adjacent closes and a five-bar limit;
it does not independently define delivery confirmation. Those numbers cannot become
canon. **S/E:** STRUCTURAL_CLOSE_BREAK and RESEARCH_MSS_AFTER_SWEEP are research
observations only; accepted transition is always unresolved. **R:**
ACCEPTED_STRUCTURAL_TRANSITION_OPERATIONAL_DEFINITION remains null. **v0.2 disposition:**
retain separate persistence and delivery evidence and their causal timing; MSS must
not be renamed an accepted transition. Avoid circular proof using the later completed
Price Delivery checkpoint.

### D6 — Market narrative coherence

**Classification:** CANONICALLY_SUPPORTED for coherent evidence and STAND_ASIDE when
absent (C CC5–6, CC9); PROPOSED_EXTENSION for M's explicit five-category taxonomy:
Retracement, Liquidity acquisition, Potential reversal, Confirmed directional
transition, Unresolved conditions. Category predicates remain UNRESOLVED.

**P:** `/definitions/2/proposal/requiredRelations/5` conservatively returns WAIT on
conflicting interpretations; the decision has only coherent/incoherent/unknown.
Automatically rejecting all countertrend movement would be CONTRADICTORY to M D6;
the draft lacks retracement/acquisition distinctions. **S/E:** midpoint location is
not narrative; NARRATIVE_COHERENCE_OPERATIONAL_DEFINITION remains unresolved and
research PASS returns REVIEW_REQUIRED. **R:** that question remains null.
**v0.2 disposition:** require a falsifiable relation to the larger objective, retain
alternatives, and keep potential reversal distinct from confirmed transition.
STAND_ASIDE is a research action, not a seventh oversight assessment status.

### D7 — Higher-timeframe directional bias

**Classification:** SUPPORTED_BUT_UNDERSPECIFIED for hierarchical interpretation
(C CC5, physical61); M D7 specifies larger liquidity objective first and no majority
vote. Four exact mappings are owner-selected research scope, not a universal
manuscript-derived timing law.

**P:** `/definitions/2/proposal/requiredRelations/5` already rejects majority voting
but checks registered contexts; `/definitions/3/proposal/hierarchy` matches M.
**S:** `hierarchy` matches 4H→15M, 1H→5M, 15M→1M, 5M→15S. **E:** rejects unsupported
pairs; EXPLICIT_RANGE_DISCOUNT_PREMIUM computes location only, not directional bias.
HTF_DIRECTIONAL_BIAS_AND_CONFLICT_RESOLUTION remains unresolved. **R:** narrative
question covers conflict handling. **v0.2 disposition:** identify the larger objective
and context interpretation before classifying lower-timeframe behavior; no vote,
nearest-level fallback, or midpoint substitution resolves bias.

### D8 — Contextual PD arrays

**Classification:** CANONICALLY_SUPPORTED (C CC5–6); numerical geometry and contextual
eligibility remain SUPPORTED_BUT_UNDERSPECIFIED. M includes FVG, IFVG, order blocks,
breakers and OTE, with no standalone entry authority.

**P:** `/definitions/2/proposal/requiredRelations/4` requires contextual consistency
and independent risk. **S/E:** THREE_CLOSED_BAR_FVG, LATER_FVG_OTE_ENTRY and midpoint
location verify the pinned ICT research subset; IFVG/OB/breaker detection is not
implemented by this evaluator. PD_ARRAY_SELECTION_AND_NARRATIVE_ALIGNMENT remains
unresolved. **R:** narrative question, null. **v0.2 disposition:** retain array source,
liquidity-event relationship, participation/transition/narrative context, validity and
contradictions. Do not force every IMAF methodology through the research FVG/OTE entry.

### D9 — Market out of balance

**Classification:** PROPOSED_EXTENSION for M's explicit definition in terms of absent
coherent actionable narrative; the STAND_ASIDE consequence is CANONICALLY_SUPPORTED
(C CC9). Specific coherence sufficiency/recovery rules remain UNRESOLVED.

**P:** shared missingDataRule and narrative decision block incomplete/incoherent input;
no distinct approved balance predicate. **S/E:** STAND_ASIDE_OUT_OF_BALANCE checks a
supplied synthetic boolean; OUT_OF_BALANCE_OPERATIONAL_DEFINITION stays unresolved.
A supplied false is not independent proof of balance. **R:** narrative question
is open; no separately approved balance definition. **v0.2 disposition:** ordinary
volatility, range or timeframe disagreement alone cannot classify out of balance.
Distinguish evidence of incoherence from unavailable evidence; both stand aside
without asserting the same factual market condition.

### D10 — Liquidity significance and target ranking

**Classification:** SUPPORTED_BUT_UNDERSPECIFIED (C CC5's origin, interaction, control,
acceptance and next-objective questions; physical61's context); M supplies contextual
ranking factors, not numeric weights or a total ordering.

**P:** `/definitions/2/proposal/requiredRelations/0` pins an explicit objective and
expiry but gives no ranking algorithm. **S/E:** SESSION_LIQUIDITY_DERIVED and
KNOWN_OPPOSING_SESSION_TARGET select extrema only inside a supplied research pool;
LIQUIDITY_SIGNIFICANCE_AND_TARGET_RANKING remains unresolved. They cannot prove that
the chosen pool is contextually highest priority. **R:** narrative question remains
null; no approved target-ranking definition. **v0.2 disposition:** record considered
objectives, acquired status, larger narrative, structure, session, delivery path,
proximity/timeframe significance and reasons for exclusion. No automatic nearest
or highest-timeframe winner; unresolved ranking remains unresolved.

### D11 — Trading day and calendar

**Classification:** PROPOSED_EXTENSION for M's exchange-aware versioned calendar and
proposed CME exchange-day default; C CC7 supports independent capital/operational
controls but supplies no executable exchange calendar. Calendar and accounting
predicates remain UNRESOLVED, including what event consumes the daily allowance.

**P:** `/definitions/3/proposal/calendarRule` already requires explicit exchange,
holiday, rollover and DST coverage. Its session entry limit does not define exchange
day identity. **S/E:** mission_policy.max_trades_per_ny_day and ONE_TRADE_PER_NY_DAY
use a NY date, explicitly synthetic; this is INCOMPATIBLE with M as a future canonical
exchange-day implementation, not a historical error to rewrite. **R:**
`boundaries.maxEntriesPerSession=1` remains independently binding. **v0.2 disposition:**
require calendar ID/version, product scope, effective interval, session/trading-day
identity, holiday/exception coverage, source and availability. No exchange hours,
holiday rules or rollover times are invented or externally verified in this mission.
Account-specific and exchange-day restrictions must both hold; no reset at arbitrary
midnight or relabeling of a trading day to create another allowance.

### D12 — Discovery and finite nonextending expiry

**Classification:** CANONICALLY_SUPPORTED for time conditioning opportunity and a
coherent process (C CC9); PROPOSED_EXTENSION for M's explicit lifecycle, owner windows
and finite nonextending expiry. Exact discovery trigger, later bounds and expiry
predicate remain UNRESOLVED.

**P:** `/definitions/3/proposal/discoveryWindow` only 09:30–11:00 and `/expiry` six
intervals/30 minutes/11:00 are CONTRADICTORY if imposed as selected v0.2 doctrine:
M explicitly allows early windows and supplies no universal later cutoff/duration.
Keep them labeled historical research choices. Nonextension and explicit calendar
requirements are compatible. **S/E:** EXPLICIT_NY_TRADING_WINDOW checks decision-time
membership; that cannot implement M's discovery-window/possible-later-confirmation
semantics. No setup expiry lifecycle is implemented here. **R:**
DISCOVERY_WINDOW_AND_SETUP_EXPIRY_POLICY remains null. **v0.2 disposition:** preserve
DISCOVERED→DEVELOPING→CONFIRMED/INVALIDATED/EXPIRED. Define event eligibility,
transition timing and terminal-state handling during formal predicate review.
Discovery must occur within an approved NY window; later confirmation requires valid
context and the original finite bound. No nested setup, reconnect, reinterpretation
or late receipt may silently extend expiry. Calendar unknown means stand aside.

## Remaining specification work

The twelve decisions settle conceptual direction; they do not settle return/reclaim
qualification, displacement, route-specific sufficiency, participation independence,
persistence, delivery confirmation, category classification, contextual ranking,
calendar accounting or setup expiry. No numerical defaults are introduced here.

The missing mission remainder must be obtained before declaring formal predicate
design, approval workflow or deliverables complete. Proposed future formal records
will need causal source references and explicit unknown/contradiction/invalidation
handling, but this review does not assume that the absent section prescribes a
particular schema. Existing six informational outcomes, registry lock, risk controls,
DENIED execution and immutable historical results remain unchanged.

## Validation and limits

This mission inspected doctrine and existing behavior; it did not modify or rerun
strategy logic. Prior Phase 3 test results are historical evidence, not validation
of new v0.2 predicates. Document/source-hash integrity checks are recorded separately
in REVIEW_STATUS.md. Source PDF was accessible; missing evidence is the mission text
from section 5 onward. No broker, market-data or production access occurred.
