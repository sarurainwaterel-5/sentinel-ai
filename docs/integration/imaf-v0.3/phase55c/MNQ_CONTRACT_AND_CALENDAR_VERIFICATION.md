# MNQ contract and calendar verification

Research checked 2026-11-16. This report evaluates exchange documentation and the existing Phase 55B implementation. It does not authenticate either provider's records, approve a research license, or conduct calibration.

## Exchange identity and contract rules

| Question | Finding | Evidence status |
|---|---|---|
| Instrument | MNQ is CME Micro E-mini Nasdaq-100 Index futures. | VERIFIED exchange product identity; application to each local artifact remains a separate provenance question. |
| Multiplier | USD 2 per Nasdaq-100 index point. | VERIFIED |
| Outright minimum increment / value | 0.25 index point / USD 0.50 per contract. Intermonth spreads have a distinct increment. | VERIFIED; does not establish a grid for adjusted continuous prices. |
| Dated-contract settlement | Cash settlement to an index special opening quotation; scheduled third Friday, with preceding-business-day contingencies. Expiring trading terminates at the primary listing exchange opening. | VERIFIED rule; individual contract dates require the exchange date table. |

Authority: [CME Rulebook Chapter 361, rules 36100, 36101, 36102.A–C/G, 36103](https://www.cmegroup.com/content/dam/cmegroup/rulebook/CME/IV/350/361.pdf). The chapter uses Chicago time unless stated otherwise, generally associates the 17:00 opening with the following trading day, and preserves regulatory/unscheduled halt conditions. A regular schedule cannot prove that no exceptional halt occurred.

The [CME Micro E-mini fact card](https://www.cmegroup.com/trading/equity-index/files/cme-micro-e-mini-futures-fact-card.pdf) lists five quarterly expiries in March, June, September and December and the regular Sunday–Friday 17:00–16:00 Chicago envelope. The resulting overnight maintenance interval is 16:00–17:00; Friday close to Sunday open is a weekend closure. This is a regular-hours reference, not a historical product/date event log.

The [CME equity roll table](https://www.cmegroup.com/trading/equity-index/rolldates.html) gives 2026 U.S. equity expiration/roll pairs: March 20/16, June 18/15, September 18/14, December 18/14. June is a useful warning against mechanically assuming every expiration is a third Friday. Participants can roll at other times. Therefore neither an April date nor a November date proves that a provider selected June or December contracts. Generic MNQ must never be silently replaced with MNQM26 or MNQZ26.

## Source conflict: obsolete daily halt

The [CME Micro E-mini FAQ](https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html), question 8, still mentions a 16:15–16:30 Eastern halt (15:15–15:30 Chicago). That paragraph conflicts with the dated [CME June 11, 2021 regulatory filing 21-244R](https://www.cmegroup.com/market-regulation/rule-filings/2021/6/21-244R_2.pdf), which eliminated that daily halt effective June 27, for the June 28, 2021 trade date. The filing's Exhibit A includes Micro E-mini Nasdaq-100 futures, Chapter 361, MNQ. The FAQ halt is CONTRADICTED for this use. Do not add that obsolete break to the 2026 reconstruction. This finding does not remove event-triggered regulatory halts or the daily maintenance break.

## Relevant dates and DST

[NIST's 2026 DST rules](https://www.nist.gov/pml/time-and-frequency-division/popular-links/daylight-saving-time-dst) specify March 8 at 02:00 local through November 1 at 02:00 local. Thus April 6–10 is CDT (UTC−05:00). November 1's evening opening and all observed November records occur after the return to CST (UTC−06:00). The repeated 01:00 hour occurs before the observed Dataset A start. A fixed UTC offset across both samples is incorrect.

The table converts the exchange schedule using Python `zoneinfo.ZoneInfo('America/Chicago')`. Root independently captured the dynamic CME MNQ product/date rows described below; this agent independently executed these timezone conversions. The distinction between documentary scheduled hours and proof of actual matching activity remains explicit.

| Nominal session | Chicago edges | UTC edges | Trading-day interpretation |
|---|---|---|---|
| First April regular envelope | Sun April 5 17:00 → Mon April 6 16:00 | April 5 22:00Z → April 6 21:00Z | April 6 |
| Last April regular envelope | Thu April 9 17:00 → Fri April 10 16:00 | April 9 22:00Z → April 10 21:00Z | April 10 |
| First November regular envelope | Sun November 1 17:00 → Mon November 2 16:00 | November 1 23:00Z → November 2 22:00Z | November 2 |
| Final observed November partial envelope | Wed November 11 17:00 → Thu November 12 16:00 | November 11 23:00Z → November 12 22:00Z | November 12; supplied records stop earlier |

April 6–10 are Monday–Friday. November 1/8 are Sundays; November 7 is Saturday. A Sunday evening local record may belong to Monday's trading day and is not invalid merely because its local or UTC calendar date is a weekend. Do not assign trading day solely with `UTC.date()` or `Chicago.date()`.

## Holiday and early-close evidence limits

The [CME 2026 Globex holiday index](https://www.cmegroup.com/trading-hours.html) places Good Friday adjustments on April 2–4 and Thanksgiving on November 26–28. Its static page mixes Globex, trading-floor, settlement, BrokerTec and EBS schedules; those tables must not be substituted for one another. In particular a Veterans Day November 11 entry in a different product/clearing table does not establish an MNQ early close.

Root then obtained actual MNQ-specific dynamic calendar rows through the CME browser UI. The selected dates and the displayed neighboring date groups were:

| Selected date | Displayed dates | Official source |
|---|---|---|
| April 6 | April 5–7 | [CME MNQ April 6 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-04-06&foi=F&pageNumber=1&search=MNQ) |
| April 9 | April 8–10 | [CME MNQ April 9 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-04-09&foi=F&pageNumber=1&search=MNQ) |
| November 2 | November 1–3 | [CME MNQ November 2 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-11-02&foi=F&pageNumber=1&search=MNQ) |
| November 5 | November 4–6 | [CME MNQ November 5 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-11-05&foi=F&pageNumber=1&search=MNQ) |
| November 8 | November 7–9 | [CME MNQ November 8 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-11-08&foi=F&pageNumber=1&search=MNQ) |
| November 11 | November 10–12 | [CME MNQ November 11 view](https://www.cmegroup.com/trading-hours.html#tradeDate=2026-11-11&foi=F&pageNumber=1&search=MNQ) |

Root reports that the captured MNQ rows show regular 17:00 OPEN and 16:00 CLOSED, Sunday 16:00 PREOPEN, weekday 16:45 PREOPEN, no Saturday November 7 session, and next-weekday trade-date assignment for evening openings. Scheduled exchange hours for these dates are therefore VERIFIED against the product/date UI evidence retained by root. This update reconciles the initial static-page limitation; it is not a claim that this subagent independently repeated every UI capture. Preopen is not continuous matching. Friday close remains the weekly close, rather than implying a Friday evening reopening. No early close is shown in the captured target-date MNQ schedules.

These are scheduled hours, not an event-by-event historical halt log or proof that the provider emitted each expected minute. Exceptional-halt completeness remains UNRESOLVED. Dataset calendar qualification also remains UNRESOLVED until provider bar labels, timezone/series binding, completeness handling, trading-day semantics and the owner's candle anchors are bound to the specific files.
The [2026 Good Friday clearing advisory](https://www.cmegroup.com/tools-information/holiday-calendar/files/2026/2026-good-friday-clearing-advisory.pdf) describes an abbreviated equities session on April 3 and separate settlement handling. It is not evidence that Monday April 6 is closed, nor a source for that Monday's exact opening/closing minutes. No early-close minute is invented here. Binding the captured scheduled hours to these datasets and exceptional-halt completeness remain UNRESOLVED for the dataset qualification.

## Comparison with Phase 55B

Inspected Trading `services/historical-research/session-plan.mjs` and supervisory `phase55b/MULTI_TIMEFRAME_RECONSTRUCTION.md`, `DATASET_VALIDATION.md`. `buildSessionPlan` checks explicit UTC endpoints against Chicago local clock, date and offset; it does not select an exchange calendar, infer holidays or assign an authoritative trading day. Its `calendar_verified:false` and `EXPLICIT_REVIEW_CLAIM_NOT_AUTHENTICATED` are accurate. The separately documented 17:00–16:00 engineering hypothesis matches both the regular envelope and the now-captured target-date scheduled hours, but its original self-supplied source/reviewer labels cannot independently certify those hours. The new external schedule evidence must be bound separately; it cannot retrospectively authenticate provider bars or owner approval.

The generator forms elapsed UTC windows anchored to the supplied session opening. This is a research alignment policy; CME regular-hours documentation does not independently approve the owner's 4H/1H/15M candle anchors. Preserve the owner's policy and obtain an explicit approved version if empirical use is later contemplated. Preserve incomplete session-end windows rather than promoting them to full candles. Missing source minutes must remain unresolved; do not fill maintenance or halted intervals with invented OHLCV.

Dataset B's April span begins at April 6 04:00Z, six hours after the nominal first session open, and ends April 10 20:59Z (a last one-minute bar-open label immediately before nominal 21:00Z close). The first session is therefore truncated under that explicit hypothesis. The reported four 60-minute internal discontinuities are consistent with normal maintenance, but consistency is not independent provider/calendar authentication. Dataset A starts exactly at the nominal November Sunday opening and ends November 12 04:08Z, well before the final nominal session close; it cannot establish a complete November month. These comparisons use Phase 55B observed coverage and do not independently reread the raw Parquet in this calendar workstream.

## Dataset contract and price conclusions

| Dataset | What existing artifact inspection establishes | Qualification limit |
|---|---|---|
| A | UTC timestamps, no intrinsic instrument or dated-contract field; MNQ exists in its filename. Quarter-grid observations passed. Provider-level additive-continuous description is not file-specific proof. | Exact MNQ identity, bar-open/close convention, roll selection and adjustment binding UNRESOLVED. Quarter-grid fit does not prove unadjusted exchange trades. |
| B | Archive README describes US/Eastern bar-open timestamps and ratio-adjusted continuous futures; selected rows carry MNQ but no dated contract. | DOCUMENTED_BUT_NOT_INDEPENDENTLY_VERIFIED artifact/provider claim. Exact component contracts, roll timing, ratio factors and adjustment-version/as-of policy UNRESOLVED. |

Neither local series is established as a specific expiring executable contract. Preserve B's supplied off-grid prices; do not round them to an unadjusted tick grid. Keep adjusted price-pattern research separate from executable-price/P&L testing and from unadjusted inputs. An adjustment constructed using later roll information can affect causal interpretation; a research protocol needs the provider's adjustment timing and as-of definition, not merely the word “continuous.” Exchange rules identify the product but cannot authenticate a vendor's continuous-series construction.

## Minimal next evidence

1. Bind each raw SHA-256 to provider-origin evidence and its instrument, bar-label, timezone, series construction and permitted scope.
2. Bind the now-captured MNQ-specific historical schedule rows to a versioned reviewed calendar manifest with source/version and Chicago/UTC edges; investigate exceptional halts and preserve the owner's candle-anchor policy separately.
3. Record source trading-day semantics and continuous-series component/roll/adjustment details; retain null dated-contract fields until supported.
4. Keep dataset-level calendar qualification unresolved and empirical research blocked until the applicable provider/owner evidence is reviewed. The existing Phase 55B plan output may remain `calendar_verified:false`; record the separately verified exchange scheduled-hours dimension without promoting unbound provider observations into complete causal candles.

No ingestion rewrite, live execution, threshold adoption or empirical calibration is justified by these findings. Existing deterministic DST logic can remain; evidence metadata and tests should enforce the unresolved boundaries. The source conflict warrants documentation, not an invented 2026 daily break.
