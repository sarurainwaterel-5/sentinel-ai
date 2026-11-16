# First-model readiness v0.3

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Verdict

**PARTIAL RESEARCH GEOMETRY; FULL MODEL VALIDATION NOT READY.** Initial model selected
by D17 is Liquidity Sweep → MSS → Displacement → FVG Retest. The name does not impose
a universal event sequence. Geometric observations, canonical interpretation,
strategy qualification, session eligibility, account/risk authority and execution
remain separate. Execution authorization: DENIED.

## Existing capabilities, by evidence rather than claims

| Portion | Observed/classified now | Replay and synthetic validation | Independent comparison / exact limit |
|---|---|---|---|
| Known boundary/range | Trading explicit sessionPools/dealingRange; Sentinel supplied session extrema/range midpoint | Closed-source geometry and prefix fixtures pass | Source window/range selection injected; all required canonical boundary families/hierarchy not independently selected |
| Wick penetration / sweep | OHLC can show penetration; research sweep requires strict same-bar return | Research strict equality/sweep tests pass | D20/21 potential acquisition is not the same class as research sweep/rejection; significance unresolved |
| Swing and structural break | Research strict pivot and completed close beyond known opposite pivot | Confirmation/prefix/future-bar cases pass | Candidate/confirmed/significant distinction and canonical break eligibility not implemented |
| Displacement | Pinned prior-only body/range profile, integer/rational Sentinel checks | Exact-threshold and insufficient baseline tests pass | Research0.7/1.5 etc are hypotheses, not selected canonical thresholds; contextual qualification null |
| FVG geometry / later retest | Three closed bars, gap and later first retracement; OTE intersection research | Valid/invalid gaps, future availability and later-entry cases pass | Relevant/setup-qualified FVG requires missing independent context/acceptance/narrative;78.6 not entry authority |
| Canonical rejection / acceptance / transition | Provisional research receipts and explicit unresolved observations | Draft closed-pair algorithms tested in own versions | No approved route, independence, persistence+delivery sufficiency or canonical contextual invalidation |
| Model discovery/expiry/session | Supplied event/bound fixtures, CT outer cutoffs, no noon reset/carryover; conditional only | Session A–J/restart tests pass | Model discovery/expiry hooks null; first-model four-window gate not implemented,5 observed mismatches |
| Historical assessments | Original snapshots/spec/hashes/clock/runtime and local durable ledger | Reopen/replay/corruption/unavailable cases pass | No verified production backup/restore; no new historical-version fallback |
| Account/risk/calendar | Trading independent risk policy/account checks and calendar/manifest validators exist | Supplied-state tests/gates useful; no actual account mutation by audit | Synthetic counts/manifests are not authoritative market/account evidence; one exchange-day allowance not independently proved |

## What independence means here

Sentinel's pure strategy evaluator does not import Trading ICT detection functions;
it recomputes supplied OHLCV observations independently. Trading adapter consumes
that pinned Sentinel module, so agreement between adapter and direct call is the
same evaluator, not a second independent confirmation. A meaningful detector comparison
requires equivalent input snapshots, tick units, source cutoff, profile and candidate
reference policy. Existing components make such research comparisons possible; this
audit did not run a new comprehensive cross-detector canonical comparison or establish
full-model validity from adapter tests.

## Narrow implementation assumptions vs current model scope

Trading ict-proposal and E couple MSS and displacement to the same bar, then a gap
ending on the next bar and later entry. Trading execution-input geometry currently
supports1M/5M plus injected1H/4H context; Sentinel research validates all four exact
pairs. The four-pair registry does not prove production context generation. Target
choice differs: Trading nearest opposing candidate vs E opposite extreme in the
supplied pool. These are versioned research restrictions, not the general contextual
model selected by owner. Same-bar observations must not be represented as independent
subsequent confirmation or a known intrabar order.

## Exact blockers by predicate

[P01](PREDICATE_READINESS_REGISTER_V0.3.md#p01)/[P12](PREDICATE_READINESS_REGISTER_V0.3.md#p12)/[P22](PREDICATE_READINESS_REGISTER_V0.3.md#p22) controlling objective, range/significance and contextual ranking; [P02](PREDICATE_READINESS_REGISTER_V0.3.md#p02)/[P09](PREDICATE_READINESS_REGISTER_V0.3.md#p09)
boundary construction and candidate/confirmed/significant swing; [P03](PREDICATE_READINESS_REGISTER_V0.3.md#p03) displacement
qualification; [P04](PREDICATE_READINESS_REGISTER_V0.3.md#p04)/[P06](PREDICATE_READINESS_REGISTER_V0.3.md#p06)/[P07](PREDICATE_READINESS_REGISTER_V0.3.md#p07)/[P08](PREDICATE_READINESS_REGISTER_V0.3.md#p08) contextual response/route/acceptance/invalidation;
[P09](PREDICATE_READINESS_REGISTER_V0.3.md#p09)/[P10](PREDICATE_READINESS_REGISTER_V0.3.md#p10)/[P11](PREDICATE_READINESS_REGISTER_V0.3.md#p11) persistence and independent delivery; [P05](PREDICATE_READINESS_REGISTER_V0.3.md#p05) multi-evidence participation;
[P13](PREDICATE_READINESS_REGISTER_V0.3.md#p13)/[P14](PREDICATE_READINESS_REGISTER_V0.3.md#p14)/[P15](PREDICATE_READINESS_REGISTER_V0.3.md#p15) narrative/qualified arrays/balance; [P16](PREDICATE_READINESS_REGISTER_V0.3.md#p16)/[P17](PREDICATE_READINESS_REGISTER_V0.3.md#p17) and scoped [S-DISC](PREDICATE_READINESS_REGISTER_V0.3.md#s-disc)/[S-EXP](PREDICATE_READINESS_REGISTER_V0.3.md#s-exp) actual
model discovery/expiry; [P18](PREDICATE_READINESS_REGISTER_V0.3.md#p18)/[P19](PREDICATE_READINESS_REGISTER_V0.3.md#p19)/[P20](PREDICATE_READINESS_REGISTER_V0.3.md#p20) calendar/account/risk authority. [P21](PREDICATE_READINESS_REGISTER_V0.3.md#p21) separates
outcome/process review. No missing algorithm is supplied by conceptual approval.

Canonical novel leaf rules remain nested in compound records; the count24 does not
mean every atomic detector was specified. Top-level narrative recovery D36 also
requires fresh independently evidenced event/context with restrictions reapplied,
not direction reversal or a revived setup. Minimum next decision set appears in
IMPLEMENTATION_READINESS_V0.3.md; no implementation begins in this audit.
