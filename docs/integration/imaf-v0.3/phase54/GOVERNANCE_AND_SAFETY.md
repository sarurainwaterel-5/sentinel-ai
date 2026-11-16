# Phase 54 — Governance and safety

RESEARCH ONLY — NOT APPROVED FOR EXECUTION. **Execution authorization: DENIED.**

## Scope and authority

The supplied Phase 54 directive authorizes offline research, deterministic tests and review artifacts. Its Section 13 ends after “Add deterministic tests”; omitted text supplies no inferred permission. No broker connection, order placement, live market feed, production configuration, risk-limit modification, secret collection, push, merge or deployment is authorized by this work. Candidate limits are experimental and never auto-approved. Synthetic output cannot establish empirical calibration, institutional intent, profitability or complete IMAF setup qualification.

## Existing architecture reused and preserved

Initial reviewed commits: Trading `2e3d1a585c61b026efb979a9e70293206cc538c3`; Sentinel `70eb081dcb2c9670ba882f1a994233c11468d37c`.

| Component/source | Existing behavior | Phase 54 boundary |
|---|---|---|
| Trading `services/governance/imaf.js` | Ten-stage canon, Observation Ladder, four unresolved operational definitions; `validateImafEntry` returns allowed false | Preserve Time→Liquidity→Participation→Acceptance/Rejection→Accepted Structural Transition→Price Delivery→Narrative→Execution→Risk→Review |
| Trading `packages/ict-model/index.js`; `services/signal-engine/ict-proposal.js` | Versioned research pivots, same-candle sweep closeback, displacement, FVG and OTE; proposal only | Legacy `sweep` is **not D68-compatible** because it permits the acquisition candle itself. Do not modify historical evaluator; separate the new subsequent-candle research predicate |
| Trading `services/structure-research/pivots.mjs`, `evidence.mjs`, `replay.mjs` | Phase 53 candidate geometry, ancestry groups, deterministic replay | Geometry is not structural significance/MSS authority; ancestry-disjoint groups are not automatically sufficient independent confirmations |
| Trading `services/governance/research-operational.js`, `research-expiry.js` | Draft operational response and pinned expiry models | Draft definitions remain draft; do not substitute their numerical assumptions for D71 owner-approved limits |
| Trading `services/market-data/session-timeframe-evidence.js`, `timeframe-evidence.js`, `calendar-manifest.js` | Explicit availability, completeness/aggregation and supplied calendar validation | No implicit provider authenticity, no finer bars derived from coarse bars, no calendar authority inferred |
| Trading `research/governance/IMAF-OPERATIONAL-QUESTIONS.json` | Four `approvedDefinition: null` values | Remain null; no parallel approved strategy registry |
| Trading `services/risk-gateway/index.js`; `packages/config/execution-modes.js` | Risk/account/execution mode gates, paper limits and live disabled policy | No research import into execution, no changes to limits or authorization |
| Sentinel `backend/evaluation/session_governance_v02/` | Isolated existing session interpretation | Retain limitations; Phase 53 acceptance report discloses four-window enforcement gaps. Descriptive research sessions never certify entry eligibility |
| Sentinel `backend/evaluation/synthetic_oversight/` | Separate contract/durable/independent supervisory assessment layers | Research records are informational and cannot become executable approvals |

## Decisions 66–71 trace

- **66:** Separate objective boundary acquisition from response review, rejection candidate and qualified sweep. Do not equate an extremum crossing with model qualification.
- **67:** Acquisition, subsequent return, displacement, structural transition and price delivery remain separate evidence stages. Event reuse must be disclosed; MSS cannot prove the original sweep and then use that same sweep as its independent premise.
- **68:** Strict subsequent completed-candle close: buy acquisition requires close below boundary; sell requires close above; equality fails. MNQ outright tick is 0.25. This is a newly authorized research predicate, not activation of an existing null governance definition.
- **69:** Finite interval is selected before acquisition and preserved; late data cannot revive an expired acquisition. New identifiers cannot erase prior history.
- **70:** Completed-candle count and actual elapsed availability time are independent bounds. Missing records/session gaps cannot silently extend either. Availability assumptions on historical exports remain explicit.
- **71:** The four supplied timeframe mappings and 1/2/3/5 paired research limits are hypotheses. No number becomes authoritative from synthetic results or a maximized return frequency.

## Session/risk distinctions

Preserve 7:30–7:35, 7:50–7:55, 8:10–8:15 and 8:30–10:00 America/Chicago windows, morning discovery/entry cutoffs, afternoon discovery rules, mandatory flattening, one trade per exchange day and 48-hour error pause as governing requirements. Do not claim all are newly operationally validated by an isolated calibration engine. Existing account restrictions and strategy restrictions are distinct; the effective permission is their intersection, never a research result. Broader-session observations are descriptive only. DST conversion does not establish an authoritative exchange trading day.

## Verification claims and remaining limits

This report's architecture statements are source inspection, not proof of operational deployment. Exact fresh test counts, no-network commands, changed-file inventory and preservation checks belong in `IMPLEMENTATION_REPORT.md` and generated Phase 54 evidence; do not reuse Phase 53's reported 574 as current verification. No provider, database, account or live execution tests were performed by the data-readiness workstream. Existing unrelated user edits must remain byte-preserved. No empirical limit is supportable while readiness is INSUFFICIENT_HISTORICAL_DATA.
