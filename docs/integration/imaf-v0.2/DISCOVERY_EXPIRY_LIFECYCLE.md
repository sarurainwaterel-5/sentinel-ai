# Discovery and expiry lifecycle — session amendment

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Selected lifecycle and predicate status

Discovery selection **D**: model-specific qualifying liquidity interaction.
Expiry selection **C**: model-specific finite, nonextending deadline.

DISCOVERED → DEVELOPING → CONFIRMED / INVALIDATED / EXPIRED.

These choices resolve the type of discovery/expiry policy. They do not define the
qualifying interaction, finite-deadline formula or model-specific confirmation/
invalidation conditions. Those executable predicates remain `null`; no duration,
price threshold, six-bar rule,30-minute limit or11:00 cutoff is adopted.

## Original setup record — proposed engineering requirements

Pin setup/event identity, model/version, origin MORNING/AFTERNOON, event time, actual
availability, discovery time, evidence refs, original finite expiry, cutoff, source/
calendar versions and subsequent state records. A hash proves consistency, not source
authenticity. No new identity can be created from morning evidence after10:00 or by
renaming an old setup at noon. A genuine afternoon event must occur in the afternoon,
not merely be a morning event whose receipt was delayed until noon.

The offline fixture aligns discovery with supplied event availability and requires
closed canonical instants. This is a conservative causal convention pending each
model's predicate; it does not independently discover liquidity or approve model
semantics. New DISCOVER snapshots must be current, in DISCOVERED state. Entry
snapshots must carry supplied CONFIRMED state, but the interpreter does not certify
its underlying IMAF reasoning. Earlier snapshots can be supplied as prior_setup to
detect identity/expiry changes, state regression and terminal revival.

## Session and lifecycle interaction

| Condition | Required interpretation |
|---|---|
| New morning event at10:00 | Morning discovery prohibited |
| Pre10:00 setup develops at10:05 | May develop within original expiry; this is not new discovery or proof of confirmation |
| Morning entry at10:15 | Prohibited even when setup is confirmed/unexpired |
| Morning setup remains valid at12:05 | Cannot become afternoon new-entry opportunity |
| New afternoon qualifying event at12:00 | Discovery can be reviewed; independent identity/expiry/IMAF/risk/count still required |
| Expiry missing or model expiry undefined | No executable eligibility; no default duration |
| At original expiry | Fixture uses exclusive expiry: no continued temporal eligibility; model-specific bound still null |
| Later candles / restart / new array / copied ID | Cannot extend the pinned expiry or revive expired history |
| Position entered before10:15 | Setup entry cutoff is not a forced position exit |
| Remaining position at15:00 | Mandatory flatten condition; expiry/target cannot postpone it |

The explicit lifecycle is formal specification; the isolated interpreter checks
snapshots and rejects selected bad transitions, not a complete production transition
engine. It does not independently issue CONFIRMED or INVALIDATED from market data.
The test archive is a one-decision receipt per setup, not a lifecycle database.
Changing that setup input creates a conflict in the archive; causal updates belong
to a future reviewed append-only lifecycle-event design.

## Identity and replay scope

Offline archive duplicates return the original record. A different setup ID reusing
the same known acquisition event conflicts within supplied archive history. A changed
original setup/expiry conflicts. This is not a distributed/global identity service;
a caller omitting historical records cannot be proven fresh. Production identity,
source authentication, global deduplication and authoritative account accounting are
not implemented by this increment.

Archive exact snapshot, supplied synthetic calendar/version, specification/module
hashes, Node/ICU/tz versions and assessment. Restart replay uses original inputs;
changed files or runtime bindings mean REPLAY_UNAVAILABLE; reproduced disagreement
means REPLAY_MISMATCH. Original receipt is not rewritten. Existing Phase2 SQL/core
contracts and prior replay artifacts are untouched. No receipt grants authority.

## Remaining selections

For each scoped model: define qualifying interaction, evidence/availability rule,
finite expiry construction and who supplies its authoritative bound, confirmation/
invalidation and genuinely distinct acquisition criteria. Morning opening/window
eligibility remains required. Equal-time contradictions and finer state transitions
need explicit model semantics before implementation; supported fixtures do not prove
these rules universally resolved. See OWNER_DECISION_REGISTER_UPDATED.md.
