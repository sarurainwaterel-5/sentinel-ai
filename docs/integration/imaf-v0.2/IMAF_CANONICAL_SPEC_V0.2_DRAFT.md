# IMAF canonical specification v0.2 — review draft

**DRAFT — NOT APPROVED FOR EXECUTION.**

> Current first-model consolidation: [IMAF canonical v0.3 audit](../imaf-v0.3/IMAF_CANONICAL_SPEC_V0.3_DRAFT.md)
> records Decisions17–36 and the four newly selected Chicago discovery windows.
> This v0.2 document describes its original scope; passing its tests does not establish
> v0.3 compliance. Executable versions, null definitions and historical results remain unchanged.


> Session-policy amendment: [SESSION_GOVERNANCE_V0.2.md](SESSION_GOVERNANCE_V0.2.md)
> records the later owner-selected CT cutoffs and model-specific discovery/expiry
> choices. Read [OWNER_DECISION_REGISTER_UPDATED.md](OWNER_DECISION_REGISTER_UPDATED.md)
> for D13–D16 and current remaining questions. Earlier NY-window/D12 questions below
> describe the pre-amendment review; they do not override the later selected policy.
> Null model/canonical predicates remain null and existing runtime behavior unchanged.


Version: 0.2.0-draft. Documentation owner: Sentinel integration review. Operational
definition lineage remains Trading AI's `IMAF-OPERATIONAL-PROPOSAL-001` v0.1; this
package proposes its next specification, not a parallel approved registry. It is not
loaded by either application. All proposed executable predicates are `null`.
Execution authorization: **DENIED**.

## Package and source authority

| Document | Purpose |
|---|---|
| [Canonical doctrine matrix](CANONICAL_DOCTRINE_MATRIX.md) | All twelve decisions compared across all five required sources |
| [Predicate definition register](PREDICATE_DEFINITION_REGISTER.md) | Versioned, incomplete rule records and causal evidence requirements |
| [Conflict report](DOCTRINE_CONFLICT_REPORT.md) | Eight conflict classes, alternatives and unresolved owner choices |
| [Owner decision register](OWNER_DECISION_REGISTER.md) | Selected concepts, exact remaining questions and minimal next decision |
| [Dependency review](DEPENDENCY_AND_CIRCULARITY_REVIEW.md) | Noncircular evidence design, time ordering and rejected inference routes |
| [Implementation readiness](IMPLEMENTATION_READINESS.md) | Completion evidence, limitations and change-control boundaries |

Source keys C/P/R/T/S/E/G follow [DOCTRINE_RECONCILIATION.md](DOCTRINE_RECONCILIATION.md)
and exact hashes in [SOURCE_MANIFEST.json](SOURCE_MANIFEST.json). M2 is the complete
replacement mission supplied in attachment `8517abb9-7902-408a-9c6f-febff29c189a`.
It completes the previously truncated M; no substantive owner decision differs.
The earlier partial review is retained as provenance, not the current completion
verdict. C is the owner manuscript v0.9, verified by its SHA-256; Current Canon
supersedes conflicting developmental wording. Owner concepts in M2 are authoritative
preferences; none is an approved executable predicate. Research numbers in P/S and
running code are not doctrinal evidence of approval.

## Governing sequence

1. Time.
2. Liquidity Objective.
3. Liquidity Acquisition.
4. Institutional Participation.
5. Liquidity Acceptance/Rejection.
6. Accepted Structural Transition.
7. Price Delivery.
8. Market Narrative.
9. Professional Execution.
10. Professional Risk.
11. Professional Review.

C CC2 (physical PDF page2) and CC9 (physical72) group checkpoints 2 and 3 as
Liquidity 2A/2B within ten numbered stages. Both are required and ordered. This
review preserves the eleven explicit checkpoints without renumbering existing
serialized ten-stage contracts or agent scopes. The original eight-stage handbook
is historical where it conflicts with Current Canon.

Each checkpoint retains the Four Pillars Observe/Reason/Execute/Improve (C physical20)
and all Observation Ladder rungs Observe/Describe/Differentiate/Interpret/Hypothesize/
Verify/Decide (C physical24–26). Record facts, inference, competing explanations,
unknowns and later verification separately. Risk gates apply before any action,
regardless of the pedagogical position of Professional Risk. Outcome review remains
pending until its evidence exists; profit does not prove prior reasoning.

## Conceptual invariants selected by owner

D1: qualifying sweep/return/displacement supports provisional rejection only.
D2: rejection confirmation may use structural evidence or persistence in an eligible
context, not a universal requirement for both and not an unconditional OR.
D3: qualifying reclaim plus opposite acceptance invalidates rejection; a crossing
alone does not. D4: infer participation from contextual independent evidence, never
attribute institutions from OHLCV. D5: accepted transition requires persistence AND
delivery confirmation; MSS is distinct. D6: classify retracement/acquisition/potential
reversal/confirmed transition/unresolved; countertrend is not automatically invalid.
D7: larger objective first, no timeframe vote. D8: arrays are contextual tools, never
standalone permission. D9: absent coherent actionable narrative means stand aside;
volatility/range/disagreement alone do not establish out of balance. D10: contextual
objective ranking, no automatic nearest/highest-timeframe rule. D11: versioned
exchange-aware day with independently binding account restrictions; CME exchange day
is a proposed default, not an implemented schedule. D12: in-window discovery,
possibly later confirmation, finite nonextending expiry.

These are logical constraints on a future operationalization, not complete sufficient
conditions for passing a predicate. The register supplies necessary/negative evidence
relations while keeping all unapproved executable predicates null.

## Time and evidence contract — proposed specification obligations

Preserve exact pairs 4H→15M, 1H→5M, 15M→1M, 5M→15S. No majority voting or favorable
lower-chart substitution. Use closed candles with instrument/contract, interval,
event time, close time, actual availability and revision identity. Eligible evidence
must be available by the historical cutoff. Later delivery may confirm a later
record; it cannot justify an earlier assessment. A late-received candle is not
backdated to its timestamp. Record source identity/hash and dependency lineage;
hashes prove consistency, not provider authenticity or institutional identity.

Owner NY windows: 08:30–08:35, 08:50–08:55, 09:10–09:15 and explicitly bounded
post-09:30 opportunities. These govern discovery. Confirmation may be later but
cannot survive missing context, an invalidated setup or its finite expiry. Endpoint
inclusion, discovery event, expiry construction and later opportunity bounds require
selection; no global cutoff/duration or exchange session schedule is invented here.
America/New_York is a presentation/session timezone, not a trading-day identifier.

Lifecycle: DISCOVERED → DEVELOPING → CONFIRMED / INVALIDATED / EXPIRED, as selected
by owner. Terminal ordering, same-instant conflicts and the effect of subsequent
liquidity events remain proposed alternatives, not adopted semantics. A fresh setup
cannot be declared merely by assigning a new ID. No lifecycle state grants authority.

## Result domains remain separate

Contract validity; observation state; interpretation sufficiency; risk/account
validation; lifecycle; and execution authorization must remain distinct. Research
STAND_ASIDE is an action/conclusion, not a seventh informational oversight status.
Keep OBSERVED, COMPLIANT, NON_COMPLIANT, INSUFFICIENT_EVIDENCE, REVIEW_REQUIRED, INVALID
as the existing assessment domain; this documentation changes none of their runtime
semantics. A future canonical mapping is not approved. A missing predicate cannot
PASS; missing/contradictory evidence must not create a coherent narrative or authority.
Execution stays DENIED even if a research observation is reproduced.

## Preservation and limits

Four `approvedDefinition:null` entries, historical Phase3 source/pins/results/replay,
Trading entry locks, risk limits and account controls remain unchanged. Existing
$50 planned-risk, $100 daily-loss, one-MNQ and one-entry-per-session research controls
are recorded as existing policy, not newly selected doctrine. The owner daily rule
and account session rules cannot cancel each other. Behavioral/cognitive/operational
readiness cannot be inferred from price arithmetic. No implementation, network,
calendar acquisition, broker connection or production action is part of this mission.
