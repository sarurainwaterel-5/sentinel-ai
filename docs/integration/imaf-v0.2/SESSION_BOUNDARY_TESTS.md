# Session boundary tests — executed offline results

**DRAFT — NOT APPROVED FOR EXECUTION.**

## Executed suites

| Suite | Executed | Passed | Failed | Skipped |
|---|---:|---:|---:|---:|
| session_governance_v02/session.test.mjs | 70 | 70 | 0 | 0 |
| session_governance_v02/replay.test.mjs | 5 | 5 | 0 | 0 |
| session_governance_v02/security.test.mjs | 3 | 3 | 0 | 0 |
| Existing Phase3 strategy/evaluator.test.mjs | 57 | 57 | 0 | 0 |
| Existing Phase3 strategy/durable.test.mjs | 8 | 8 | 0 | 0 |
| Existing Trading services/synthetic-oversight/strategy.test.mjs | 3 | 3 | 0 | 0 |
| **Total case executions** | **146** | **146** | **0** | **0** |

78 new offline cases plus68 existing compatibility regressions. Direct Node test files
were executed with the existing deny-network preload; no network-dependent tests.
Raw TAP and a verification manifest are retained in workspace
`outputs/imaf-session-v02/test-results/`. Scenario snapshots/results in `scenarios.json`.
An early test iteration had one failure because its expiry equaled discovery (an
invalid bound); the fixture was corrected to a positive interval tested exactly at
expiry. Final executed results above have no failures/skips.

## Tested boundaries

| Boundary / condition | Executed expected interpretation |
|---|---|
| Explicit fixture morning opening | Inclusive; no model morning start supplied→insufficient |
|09:59:59 /10:00 /10:00:01 CT discovery | Conditional research / prohibited / prohibited |
|10:14:59.999 /10:15 CT morning entry | Conditional temporal review / prohibited |
|11:59:59 /12:00 /12:00:01 CT fresh discovery | Prohibited / conditional research / conditional research |
|14:59:59.999 /15:00 /15:00:01 CT entry | Conditional temporal review / prohibited / prohibited |
|15:00 existing position | Mandatory flatten condition, no routed order |
| Original expiry exact equality | No continued eligibility; no renewal/revival |
| Receipt after decision / future event | No temporal qualification; no backdating |
| UTC without milliseconds / excessive precision / invalid day | INVALID |
| Undefined expiry/discovery model evidence | Insufficient, null predicates preserved |
| Unknown holiday/early-close/rollover | Insufficient for new-entry inference |
| Stale/missing/mismatched count | No presumed allowance |
| Explicit fictional next trading-day interval | Old-day count rejected; only matching version/day examined |
| Chicago DST, NY explicit offsets | Distinct instants/valid local clocks; actual seasonal policy boundary assertions |

Timestamp precision and explicit end exclusivity prevent granting an entry at10:15
or15:00. A sub-millisecond string is rejected, not rounded backward into eligibility.
Test profile uses supplied finite bounds; it never derives a model expiry duration.

## Reproduce

From Sentinel root:

```sh
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/session.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/replay.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/session_governance_v02/security.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/evaluator.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/strategy/durable.test.mjs
```

From Trading root, with explicit local Sentinel path:

```sh
SENTINEL_SYNTHETIC_CONSUMER_ROOT=/absolute/path/sentinel-ai \
node --import /absolute/path/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs \
  services/synthetic-oversight/strategy.test.mjs
```

## Unsupported / not executed

No production runtime, application route, full backend/database/browser suite, real
exchange-calendar/account validation, broker, order routing, real fills, live feed,
full IMAF/model discovery/expiry predicate or operational flatten test. Conditional
fixture outcomes do not count toward forward-trade evidence or production readiness.
No tests skipped to hide these gaps; they are outside supported fixture scope.
