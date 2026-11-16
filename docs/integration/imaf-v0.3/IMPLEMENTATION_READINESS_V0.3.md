# Implementation readiness and prioritized owner queue v0.3

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Verdict

**Audit/consolidation complete; full first-model validation NOT READY.** Research
geometry, independent recomputation, offline outer session guards and local replay
exist and are tested. Canonical sufficient predicates, source/account authority,
full model lifecycle and production recovery remain incomplete. Execution authorization:
**DENIED**. Nothing in a conceptual decision activates a predicate or an order path.

## Completed deliverables and counted scope

Nine requested v0.3 reports are linked from IMAF_CANONICAL_SPEC_V0.3_DRAFT.md.
Twenty owner decisions D17–D36 are individually recorded with all required fields.
Twenty-two existing canonical records plus2 scoped session hooks audited =24 scoped
predicate-definition records, all24 null; this is not24 distinct conceptual algorithms.
Four independent Trading approval slots remain null. No approved parallel registry.

Ten conflict/scope findings F01–F10 and eight circularity risks CY01–CY08 documented.
No direct contradiction with reviewed manuscript doctrine found under the stated
scope; material incompatibilities exist if old research constraints are called v0.3.
First-model exact new windows are specified but not implemented by the session helper.

## Actual test results — executed in this audit

| Raw TAP log | Tests | Pass | Fail | Skip |
|---|---:|---:|---:|---:|
| v03-session-replay.tap | 5 | 5 | 0 | 0 |
| v03-session-security.tap | 3 | 3 | 0 | 0 |
| v03-session.tap | 70 | 70 | 0 | 0 |
| v03-strategy-durable.tap | 8 | 8 | 0 | 0 |
| v03-strategy-security.tap | 4 | 4 | 0 | 0 |
| v03-strategy.tap | 57 | 57 | 0 | 0 |
| v03-trading-consumer.tap | 3 | 3 | 0 | 0 |
| v03-trading-context.tap | 2 | 2 | 0 | 0 |
| v03-trading-expiry.tap | 12 | 12 | 0 | 0 |
| v03-trading-imaf.tap | 13 | 13 | 0 | 0 |
| v03-trading-operational.tap | 16 | 16 | 0 | 0 |
| v03-trading-signals.tap | 10 | 10 | 0 | 0 |
| v03-trading-timeframe.tap | 17 | 17 | 0 | 0 |
| **Total case executions** | **220** | **220** | **0** | **0** |

These existing test files were run directly with the existing deny-network preload,
not merely inspected. All13 suites completed. This count is case executions, not a
claim that all canonical predicates have testable definitions. Separate13 read-only
window comparisons yielded8 matches and5 v0.3 compatibility mismatches; those five
are unresolved audit findings, **not passed v0.3 tests**. All probe outputs remain
DENIED. Documentation structural/link/source/hash/graph checks are separate checks,
not added to220. Raw logs/probes/manifest retained at workspace outputs/imaf-v03-audit/.

Reproduce Sentinel suites with:

```sh
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/session.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/replay.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/security.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/evaluator.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/durable.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/security.test.mjs
```

Trading: use the same absolute Sentinel deny-network preload with direct Node files:
services/synthetic-oversight/strategy.test.mjs (explicit SENTINEL_SYNTHETIC_CONSUMER_ROOT),
tests/unit/research-operational.test.js, research-expiry.test.js,
session-timeframe-evidence.test.js, signals.test.js, context.test.js and imaf.test.js.
No --test worker aggregation, no live services. Full app/backend/browser/broker tests,
real market/account/calendar coverage and production backup/restore not run.

## Top five blocker groups

1. **Measurable canonical model predicates and independence.** Boundary/range/swing
   significance, acquisition vs response, displacement, accepted persistence+delivery,
   contextual FVG/narrative/route/invalidations remain incomplete. Exact four-window
   enforcement also needs a separately scoped offline change, not reapproval of times.
2. **Model-specific finite expiry.** Deadline authority/source or maximum lifetime
   explicitly unresolved; supplied fixture bounds cannot fill the canonical rule.
3. **Authoritative market/instrument/evidence provenance.** Real source and receipt/
   tick/context truth, available volume/order-flow applicability not independently verified.
4. **Exchange calendar and authoritative account count.** Existing validators/ledger
   reusable, actual covered schedule/day and current account/consumption semantics unverified.
5. **Operational recovery and release authority.** Production backup/restore, external
   checkpoint and historical bundle archival remain unverified; live authorization DENIED.

The seven mission operational blockers remain individually open: market source,
exchange-aware calendar, authoritative count, finite expiry, model confirmation
thresholds, production backup/recovery and live authorization. Grouping does not
hide or clear any of them. No source/account value is relabeled authoritative.

## Short dependency-ordered owner decision queue

| Priority / decision | Why / affected behavior | Missing criterion or evidence | Existing doctrine enough? Owner input? | Offline / paper / live impact |
|---|---|---|---|---|
| Q1 causal structural-reference contract for first model | Unlock P01/P02/P09/P12/P14/P22, significance before MSS and valid range/OTE rather than fitted geometry | Exact controlling range/boundary selection, candidate→confirmed→significant swing rules, when each is known; annotated positive/negative/ambiguous causal examples | Doctrine provides constraints, not complete measurements. Owner must select measurable profile; no invented width/tolerance | Existing geometric offline tests continue; additional canonical synthetic qualification blocked. Paper/live blocked |
| Q2 finite original expiry rule/source | Unlock P17/S-EXP and model lifecycle/temporal tests under original identity | Explicit model deadline authority or finite maximum construction, availability and same-instant boundary/contradiction treatment; no universal default invented | D17 explicitly unresolved. Owner selection required | New scoped lifecycle synthetic tests need this to claim model-specific expiry; paper/live blocked |
| Q3 independent confirmation and response-route sufficiency | Unlock P03/P05/P06/P07/P09/P10/P11/P13/P14 | Distinct information beyond MSS, prospective route eligibility, persistence/delivery/contextual contradiction thresholds and category criteria | Manuscript/decisions establish necessity, not sufficient algorithms. Owner selection required after Q1 | Existing observation tests useful; full canonical confirmation/qualification blocked at all stages |
| Q4 source/calendar/account and recovery authority | Enables authoritative eligibility and future operational readiness without duplicate engines | Reviewed source/product/calendar versions, authentic current trade-count event semantics, backup/restore acceptance and retained historical bundles | Source/operator verification plus scoped approvals required; cannot be settled by prose or synthetic labels | Synthetic research can continue with labeled fixtures; paper/live remain blocked; no broker work authorized |

**Smallest next owner decision:** Q1, the causal boundary/range/swing reference contract,
with timestamped positive/negative/ambiguous examples. This unlocks several geometric
and significance tests without approving execution or the entire model. Pair Q2 only
when the next increment needs to validate the complete model lifecycle rather than
reference observations. Do not ask the owner to choose the model or morning windows
again: D17 already selects them. No further long abstract option questionnaire.

A minimal next implementation proposal could also fix the already-selected four-window
offline gate and tests without new trading-doctrine choices, but it still needs a
separately scoped implementation task. This audit does not change executable code.

## Change control and completion boundary

Only integration documentation is created/updated. Existing strategy, session helper,
contract semantics, runtime routing/risk/authorization, null definitions, source data,
replay histories and user edits preserved. No broker/data calls, push, merge or deploy.
Local documentation commit permitted only after validation. Review reports are drafts,
not a live release or production-readiness approval. Stop at audit and reporting.
