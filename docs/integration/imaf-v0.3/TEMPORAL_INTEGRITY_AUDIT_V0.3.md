# Temporal integrity audit v0.3

**DRAFT — NOT APPROVED FOR EXECUTION.**

## General temporal rule

Required: each claim states when supporting observations actually became available,
not just the source event's chart timestamp. Retain event interval/close, receipt,
confirmation-known time, original information cutoff, evaluation time, derivation
and calendar/rule versions. Derived claims cannot precede their latest required
input. Revised/late evidence appends a later assessment. No future candle or profitable
outcome can justify an earlier decision. C-LADDER/C-PART/C-REV; D17/D21–D36.

OHLC extrema identify possible within-bar events but not high/low traversal order.
If ordering matters and timestamped finer observations are unavailable, ordering is
UNKNOWN. Separate facts can be observed on one bar without asserting causal sequence.
The model-name arrows are not proof of that sequence.

## Claim-by-claim audit

| Claim | Earliest eligible knowledge / required timestamps | Inspected implementation and limitation |
|---|---|---|
| Discovery | Model-qualified sweep/interaction observed in allowed window; preserve event and actual availability; qualified predicate null | Session fixture aligns discovery to event availability by conservative convention; no OHLC detection and four D17 windows absent |
| Boundary creation | Complete source window or approved derivation + receipt/calendar review; no future range | Trading context.sessionPools/dealingRange derives from closed caller-selected windows; session-timeframe helper incorporates source receipt/review; source authority not proved |
| Swing confirmation | Right-side or other selected confirmation available, not pivot event time; significance separately known | Trading confirmedSwings has confirmedIndex; E adds source availability; widths are research choices, not significance proof |
| MSS | Pre-established eligible significant swing plus observed breach/close known by cutoff | Both research detectors use known pivot and close; canonical significance/break-type qualification absent |
| FVG formation | Geometric profile inputs fully closed/available; relevance later and separate | Three-bar research gap known at final close; later retracement required; geometry not institutional participation |
| Rejection/acceptance confirmation | Context route eligible prospectively, all response evidence available; no retrospective route | Trading research-operational uses subsequent closed/received pair with draft limits; canonical route/acceptance remains null |
| Structural persistence | Separate post-break completed observations and known contrary acceptance/integrity | Draft close count not approved; no universal count inferred |
| Delivery confirmation | Additional observations after the original MSS-establishing observation, with source lineage | E uses same mss/displacement candle for research; does not implement canonical independent later confirmation |
| Setup expiry | Finite model deadline authority/version fixed for original identity; no later candles extend | Offline fixture requires explicit bound; Trading draft calculates its own old parameters; actual canonical bound unresolved |
| Session | Exact CT discovery windows, entry cutoffs, fresh noon origin,15:00 condition; source NY offsets normalized | Outer session helper works for prior scope;13 current-window probes find5 v0.3 mismatches; no policy patch |
| Exchange day | Verified effective calendar interval/day ID and current authenticated count; no midnight/noon reset | Real calendar/manifest validators exist; supervisory calendar/count fixtures not authoritative |
| Restart replay | Original snapshot/cutoff/spec/evaluator/calendar/runtime dependencies; later input ignored | Actual process restart tests pass; dependency changes unavailable; production backup/restore and historical bundle loading incomplete |

## Close time versus receipt time

Trading `calculateIctProposal`/market-data.validateCandles checks closed/aligned bar
history and availableAt on supplied pools, but its standalone candle contract does
not establish per-bar actual receipt time. Therefore its closed-bar prefix property
is not proof of authentic historical availability. Reuse existing
session-timeframe-evidence helper, which retains source availableAt, window close and
review timestamp, after reviewed integration/source linkage; no replacement calendar
or aggregation engine is recommended. E explicit candle available_at rejects future/
unreceived data but trusts supplied synthetic timestamps. Neither local hash is a
provider signature.

## New discovery windows: executed read-only comparison

M4 D17 selects [07:30,07:35),[07:50,07:55),[08:10,08:15),[08:30,10:00) Chicago.
A one-off synthetic audit supplied the existing helper with07:30 opening and evaluated
13 boundary/gap times. Five mismatches:07:35,07:40,07:55,08:15,08:25 return
CONDITIONAL_RESEARCH_REVIEW despite being outside D17 windows. All remain execution
DENIED. Probe output retained at workspace outputs/imaf-v03-audit/
window-compatibility-probes.json. These are observed compatibility discrepancies,
not passing v0.3 assertions. Existing suites pass their historical scope only.

## Replay and lifecycle limits

No original expiry/source/calendar artifact or policy version is rewritten. New
recovery requires fresh event/identity under current restrictions, not re-evaluation
of an expired snapshot as a new opportunity. Existing session archive is one receipt
per setup, not full mutable lifecycle management; original source DB and old logs are
untouched. Missing model deadline or authoritative calendar/account evidence blocks
qualification/eligibility even when timezone conversion and replay are deterministic.

No intrabar reconstruction, real-data arrival authentication, actual exchange calendar,
production restore or live flatten test was executed. Exact source/cutoff obligations
must be part of the next scoped predicate contract before canonical causal claims.
