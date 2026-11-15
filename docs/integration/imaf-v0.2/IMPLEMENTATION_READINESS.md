# Implementation readiness — canonical v0.2 session increment

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Verdict

The **session specification and supported offline fixture increment is complete**.
The new interpreter is isolated from application/runtime execution behavior. Canonical
model predicates, exchange/account authenticity and production readiness remain
incomplete. Execution authorization remains **DENIED**.

Canonical documentation review from commit2ea3809 remains the doctrinal baseline.
This amendment records D13–D16 and narrows previously unresolved session semantics;
it does not approve the full canonical evaluator, activate null definitions or replace
historical Phase2/3 contracts. Earlier broad claims of documentation-only work apply
to that earlier mission, not these newly authorized offline fixture files.

## Required deliverables and completion

| Requirement | Evidence |
|---|---|
| Selected CT morning/noon/flatten/day policy | SESSION_GOVERNANCE_V0.2.md |
| Model-specific discovery/finite nonextension | DISCOVERY_EXPIRY_LIFECYCLE.md; specification.json predicates null |
| Exclusive boundaries / inclusive starts | SESSION_BOUNDARY_TESTS.md;70 executed policy/time cases |
| Position handling and replay A–J | POSITION_LIFECYCLE_TESTS.md;5 replay cases incl actual child-process restart |
| Calendar/DST/NY input review | CALENDAR_AND_DST_REVIEW.md |
| Decisions13–16 | OWNER_DECISION_REGISTER_UPDATED.md, editorial grouping of supplied owner policy |
| Safety boundary |3 new security cases; no runtime imports/changes, source hashes/pins unchanged |
| Preserved daily/noon restrictions | Explicit synthetic day/version/count checks; missing evidence blocks |
| Validation |78 new +68 existing regression executions =146 passed,0 failed,0 skipped |

## Ready vs incomplete

Ready for review: exact session cutoffs, no cutoff-only morning flatten, fresh afternoon
origin requirement, noon count continuity, mandatory15:00 condition, conditional
synthetic temporal tests, replay under original input/spec/calendar/runtime hashes.

Incomplete: morning opening/model windows; exact model qualifying liquidity event,
expiry algorithm/bound authority, confirmation/invalidation and distinct acquisition
proof; full IMAF/independent risk; authenticated exchange-day calendar and account
count/consumption event; actual holiday/early-close coverage; operational order/fill
reconciliation, early-close handling and live flatten feasibility. Null predicates
are reported, not bypassed. Model choiceD/expiry choiceC selects types, not algorithms.

## Read-only compatibility assessment

Existing Trading research-operational.js/research-expiry.js and v0.1 proposal use
separate draft parameters; do not import the new policy there or adopt those numbers.
Existing Sentinel Phase3 evaluator checks NY decision windows and NY-date synthetic
counts; it does not implement this CT session policy or full exchange-day accounting.
No such existing behavior was changed. Existing schema/protocol/SQL migrations,
consumer pins and four-question registry are untouched. Existing strategy/durable
and Trading consumer regressions pass with original pins.

Existing Phase2/3 replay retains exact historical bindings. New offline archives are
separate test artifacts, not a migration or parallel authoritative account ledger.
Original dependency availability remains necessary; replay never reinterprets old
history under this amendment. Production integration would require separately
reviewed authorization, contract decisions and executable tests; it is not begun.

## Remaining owner decisions and smallest next step

Select one scoped model/version and its qualifying interaction, morning windows and
finite expiry rule or authoritative bound source. Exact question is in the updated
decision register. Keep unselected model predicates null. Verified calendar authority,
product/version and authoritative account count/consumption semantics are separate
requirements before real daily-compliance claims. Already-selected cutoff times do
not require re-approval. No universal expiry duration is requested or inferred.

Estimated complexity: small for the isolated boundary interpreter (implemented);
model predicate and calendar/account integration complexity cannot be established
until definitions/sources are selected. No model/production implementation follows
automatically from this report. Stop after validation and reporting.

## Verification limits

All146 executed case assertions passed with active network denial. One earlier expiry
fixture was corrected after a failed assertion; final results and raw logs are
retained. No full application/browser/backend, broker, real market-data, official
calendar, actual account or production execution testing. Supported fixtures are
neither validated trading edge nor genuine forward-trade evidence. No push/merge,
deployment, broker connection, secret, risk-limit change or execution activation.
