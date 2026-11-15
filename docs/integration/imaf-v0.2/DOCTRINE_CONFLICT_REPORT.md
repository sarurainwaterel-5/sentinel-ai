# Doctrine conflict report — v0.2

**DRAFT — NOT APPROVED FOR EXECUTION.**

> Session-policy amendment: [SESSION_GOVERNANCE_V0.2.md](SESSION_GOVERNANCE_V0.2.md)
> records the later owner-selected CT cutoffs and model-specific discovery/expiry
> choices. Read [OWNER_DECISION_REGISTER_UPDATED.md](OWNER_DECISION_REGISTER_UPDATED.md)
> for D13–D16 and current remaining questions. Earlier NY-window/D12 questions below
> describe the pre-amendment review; they do not override the later selected policy.
> Null model/canonical predicates remain null and existing runtime behavior unchanged.


All alternatives are for owner review; none is selected or activated here. Existing
research behavior remains historical and unchanged. Source keys and classifications
are resolved in CANONICAL_DOCTRINE_MATRIX.md and SOURCE_MANIFEST.json.

## C01 — Acceptance versus rejection (D1–D3; P04/P06–P08)

Evidence: P `/definitions/0/proposal` uses the first qualifying close pair and a
single contradictory close; M2 D1/D3 requires provisional return/displacement and
qualifying reclaim plus opposite acceptance. C CC9/72 asks acceptance or rejection
without specifying numerical tests. Old single-close invalidation is CONTRADICTORY
if promoted to selected canonical rejection invalidation. Qualifying numerical
semantics and simultaneous opposing interpretations are UNRESOLVED.

Options: (A) keep neutral/ambiguous observations unresolved until one context-qualified
response is evidenced; (B) retain an initial provisional response with explicit later
contradiction/suspension records while waiting for qualifying acceptance. Neither
option makes a temporary crossing invalidation. Owner must define acceptance,
reclaim/return qualification and ambiguity handling. Do not let the same assumed
response prove its opposite acceptance. Related questions: D1–D3 register.

## C02 — Structural break versus accepted transition (D2/D5; P07/P09–P11)

Evidence: C CC4/67 explicitly rejects line-break sufficiency; M2 D5 requires persistence
AND delivery. P `/definitions/1/proposal/sequence` has a two-close research transition;
E RESEARCH_MSS_AFTER_SWEEP does not implement accepted transition. Labeling either
as full canonical acceptance is CONTRADICTORY. D2's structural confirmation route
could create a response↔transition cycle if it means the same accepted transition.

Options: (A) define structural rejection confirmation as independently observed raw
structure/persistence under eligible context, distinct from accepted transition;
(B) use time-separated assessments, with preliminary response supporting later
transition and later evidence updating rejection confidence, without using the later
update as proof of its own prerequisite. Owner must select structural-route meaning
and persistence/delivery sufficiency. No universal requirement for both D2 routes.

## C03 — Participation versus price-delivery evidence (D4/D5; P05/P10)

Evidence: C physical59–62 requires independent convergence; C CC5/68 describes delivery
following participation and transition. M2 D4 allows subsequent delivery to inform
participation. Reusing the same displacement/FVG as independent proof or using the
finished narrative to prove participation is unsupported. P's disjoint-bar proposal
is one research construction, not approved sufficiency.

Options: (A) distinguish pre-transition raw delivery observations from the later
completed Price Delivery stage, and disclose dependency overlap; (B) distinguish
initial participation inference from a later corroboration record. These can coexist,
but evidence sufficiency and independence criteria still require selection. Owner
must decide whether disjoint bar sets are necessary, sufficient or merely a research
constraint; no new minimum count is selected.

## C04 — Higher versus lower narratives (D6/D7/D10; P01/P12/P13/P22)

Evidence: M2 explicitly permits retracement/acquisition/potential reversal and rejects
majority votes; P narrative relation5 currently chooses WAIT for conflicts. E
EXPLICIT_RANGE_DISCOUNT_PREMIUM only checks range location. Automatic rejection of
all countertrend motion is CONTRADICTORY; exact category boundaries are UNRESOLVED.

Options: (A) use the original larger objective as the governing hypothesis while
classifying lower movement and its contradictions; (B) append a separately justified
context revision when new evidence invalidates that objective. Neither a favorable
lower target nor a winning outcome can retroactively change the original bias.
Owner must define category/revision thresholds and what confirms directional change.

## C05 — Session discovery versus confirmation (D12; P16/P17)

Evidence: P has 09:30–11:00 discovery only; E EXPLICIT_NY_TRADING_WINDOW checks decision
time in early windows or a supplied later opportunity. M2 permits early discovery
and later confirmation. Treating E's decision window as this lifecycle is
CONTRADICTORY; endpoint and discovery-event semantics are UNRESOLVED.

Options: (A) use acquisition closed-bar availability as discovery; (B) use a separately
defined causal discovery event with its own availability. Both must be in a reviewed
window; neither may backdate late receipt. Owner must select event, interval endpoints
and explicit later opportunity bounds. A window ending need not mean setup expiry;
confirmation after it still requires the original finite valid bound. No 11:00 or
other default post-09:30 cutoff is selected.

## C06 — Setup expiry versus later liquidity events (D12; P17)

Evidence: M2 requires finite nonextension; P `/expiryPropagation` forbids extending
an old setup. Existing research-expiry.js enforces its pinned research bound and
rejects explicitly nested recomputation, but cannot authenticate a fresh caller ID.
Old six-interval/30-minute values remain draft only. New-ID relabeling must not extend
an existing setup. Event ordering and genuine new-acquisition identity are UNRESOLVED.

Options: (A) supersede an old setup with a separately evidenced acquisition and new
identity, retaining the old record/bound; (B) retain separate concurrent hypotheses
with independent original expiries, subject to all strategy/account restrictions.
Owner must choose overlap/supersession policy, distinct-event criteria, finite expiry
construction and same-instant expiry/confirmation precedence. No second allowance is
created by a second setup. Terminal resurrection is not silently assumed.

## C07 — Calendar date versus exchange trading day (D11; P18/P19)

Evidence: S/E ONE_TRADE_PER_NY_DAY uses a NY date; P calendarRule requires exchange,
holiday, rollover/DST coverage; M2 proposes CME exchange trading day by default.
The NY date convention is CONTRADICTORY if called canonical exchange-day accounting.
No reviewed exchange schedule is supplied or acquired by this mission.

Options: (A) adopt a specifically versioned reviewed exchange calendar for the scoped
product; (B) use a separately approved strategy exception, explicitly versioned and
not inferred. Account days remain independently binding in either case. Owner must
select calendar authority/product/effective scope and the consumption event; no
rollover time, holiday schedule or midnight reset is invented. Unknown coverage
remains insufficient evidence.

## C08 — Strategy versus account restrictions (D11; P19/P20)

Evidence: R.boundaries.maxEntriesPerSession and existing hard controls remain; M2
adds an approved-calendar day rule. A strategy calendar cannot reset an account's
restriction, and a permissive account window cannot clear the strategy restriction.
The independent conjunction is owner-selected; allowance-consumption semantics and
account evidence authority are UNRESOLVED.

Options: (A) count a defined committed entry event per strategy day and retain each
account's separate consumption rules; (B) count a defined attempt/authorization event
for the strategy when specifically approved, again preserving account rules. Owner
must select exact event identity, retry/partial-fill/correction treatment and whether
restrictions are keyed by account/strategy scope. No option weakens existing limits,
removes independent risk controls or converts an analytical status into a receipt.

## Required resolution order

Resolve the bounded temporal contract first (D12), then initial response qualification
(D1) for a small observational-only increment. D2–D5 remain mandatory before confirmed
rejection/transition claims; D6–D11 remain mandatory for full narrative/account
compliance. Document review is complete with these conflicts visible; implementation
readiness is not established merely by listing options.
