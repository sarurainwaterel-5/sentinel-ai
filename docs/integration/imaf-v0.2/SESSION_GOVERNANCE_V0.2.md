# Session governance v0.2 — selected policy and offline interpretation

**DRAFT — NOT APPROVED FOR EXECUTION.**

Session profile: `IMAF-SESSION-GOVERNANCE-v0.2`, version `0.2.0-session-draft.1`.
Source: owner session mission, SHA-256 pinned as M3 in SOURCE_MANIFEST.json. This is
an amendment to the existing canonical v0.2 review package, not a parallel approved
strategy registry. Model discovery/expiry predicates and four governance definitions
remain null. Execution authorization remains **DENIED**.

## Owner-selected policy

All policy wall-clock times use **America/Chicago**, with timezone/DST conversion,
not fixed UTC subtraction. Source bars may carry America/New_York timestamps;
comparison uses unambiguous UTC instants with original zone/offset retained.

| Interval / boundary | Discovery / entry meaning | Existing positions |
|---|---|---|
| Morning opening | Inclusive once the model/session opening is explicitly supplied; no opening time selected in this mission | Existing independent risk applies |
| Before10:00 | Qualifying morning discovery possible subject to model/session evidence | Manage predefined plan |
| Exactly10:00 and later | No new morning setup identity; earlier setups may develop within original expiry | Manage predefined plan |
| Before10:15 | Earlier qualifying morning setup may be considered for entry, subject to all other gates | Manage predefined plan |
| Exactly10:15 until noon | No new morning position | Do not flatten solely at10:15; target/stop/risk management remains |
| Exactly12:00 and later | Afternoon discovery reopens inclusively; requires new afternoon qualifying event, new identity/discovery, finite nonextension and independent IMAF assessment | Noon does not reset daily allowance |
| Exactly15:00 | No entry/discovery eligibility; remaining open positions subject to mandatory daily flatten | Overrides unfilled target/stop; no live order sent by fixtures |

Morning setup validity does not allow morning entry after10:15. Morning setup identity
or event cannot become an afternoon entry candidate, even if its expiry is later.
Afternoon entries remain subject to independent IMAF/risk/calendar/count evidence.
The flatten deadline is an obligation for existing exposure, never entry permission.
Earlier target/stop closes may follow the plan; an unfilled target does not postpone
15:00 flatten. Existing independent protective/risk controls remain binding.

One trade per **approved exchange trading day**, not local date and not morning plus
afternoon. Noon changes session scope, not count identity. Calendar/account count
unknown means no presumed allowance. Account restrictions remain independently
binding; this mission does not define the authoritative allowance-consumption event.

## Implemented offline behavior

New isolated files: `backend/evaluation/session_governance_v02/` — specification,
pure snapshot interpreter, synthetic fixtures, test-only archives/worker and tests.
They have no import from an application, broker, order service or existing execution
module. No existing runtime/schema/consumer pin was modified. Run only explicitly as
an offline fixture tool; no application route, background job or production config.

The interpreter handles DISCOVER, ENTRY and MANAGE snapshots. It checks supplied
identity/expiry/state history but does not detect a liquidity event, evolve a complete
strategy state machine, validate model confirmation or authenticate accounts. Supplied
CONFIRMED state is a synthetic assertion, not independent IMAF validation. No model
predicate is activated. Available outcomes are a separate fixture result domain,
not additions to the six supervisory outcomes or executable approvals.

`CONDITIONAL_RESEARCH_REVIEW` means only that supplied synthetic temporal prerequisites
fit. It always reports unverified strategy/model predicates, unauthenticated account
risk and DENIED execution. Missing expiry/evidence/calendar/count yields insufficient
evidence or a specific prohibition. Prohibition can be known from a hard cutoff even
if other evidence is unavailable; that does not imply those other checks passed.

## Proposed conventions vs selected doctrine

Selected: exact CT cutoffs, inclusive starts/exclusive ends, morning management,
fresh afternoon origin, finite nonextension, exchange-day daily rule and15:00 flatten.
Proposed only: fixture canonical millisecond UTC contract; discovery aligned to the
supplied qualifying-event availability; caller supplies morning opening and original
finite expiry; fixture result labels and content-hash archive. The event-availability
alignment is a conservative test convention, not a selected universal model rule.
Model-specific event/expiry predicates remain null. Fixture9:00 opening and long
expiry examples are test data, never adopted defaults or durations.

## Compatibility and unresolved scope

Earlier v0.2 NY windows remain recorded as earlier owner context, not silently erased.
This amendment governs the selected CT cutoffs; it does not choose the model-specific
morning opening or prove that every instant before10:00 is discovery-eligible. Any
remaining model observation windows must be explicitly reconciled. 12:00 reopening
is selected, but not an assumption that model/IMAF conditions are met.

Trading's old09:30–11:00 NY/six-bars/30-min draft and Sentinel Phase3 decision-time NY
windows are historical research versions. Neither implements this CT lifecycle.
Existing Phase2/3 records retain exact original dependencies; no history reinterpretation,
schema migration, policy activation or entry-lock release. See related lifecycle,
calendar, decision and readiness documents in this directory.
