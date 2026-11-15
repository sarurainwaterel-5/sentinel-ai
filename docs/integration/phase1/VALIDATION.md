# Phase 1 executed validation

Executed November 15, 2026 with Node v22.22.1 and the existing Sentinel Python venv.
All counts below are individual cases, not file aggregates.

| Executed suite | Passed | Failed | Skipped | Evidence |
|---|---:|---:|---:|---|
| Sentinel synthetic contract | 45 | 0 | 0 | `protocol.test.mjs`, shared `contract-tests.mjs`; network-denied direct Node run |
| Sentinel synthetic security | 4 | 0 | 0 | `security.test.mjs`; network-denied direct Node run |
| Trading cross-repository adapter/shared contract | 49 | 0 | 0 | `services/synthetic-oversight/adapter.test.mjs`; same 45 cases plus 4 adapter/security cases, network denied |
| Existing Sentinel oversight/CSV tests | 81 | 0 | 0 | `test_trading_oversight_contract.py`, `test_trading_oversight_report.py`, `test_trading_oversight_safety.py`, `test_tradingview_evidence.py`; 2.09 seconds |
| Existing Trading unit/adversarial suite | 367 | 0 | 0 | `tests/run.js`; network denied, 9788.318497 ms |

The 45 shared cases are intentionally executed in both repositories. These are
546 case executions in the listed runs, not 546 unique test definitions. The new
suites contain 53 unique cases (45 shared + 4 security + 4 Trading adapter).
Trading `npm test` also passed 367/0/0 before the explicit network-denied run; it
is not counted again in the table. Full TAP logs, demo and source/log hashes are
retained privately under workspace `outputs/phase1-synthetic-integration/`.
The Python result is recorded from the executed tool result; no raw pytest log
was saved by that invocation. No log has been reconstructed and labeled as raw.

## Required failure scenarios

| Scenario | Executed expectation |
|---|---|
| Valid synthetic proposal | COMPLIANT within SYNTHETIC_FIXTURE_ONLY; authorization DENIED |
| Invalid schema | INVALID with errors; no exception escapes assessment |
| Missing evidence | INSUFFICIENT_EVIDENCE; missing/dangling hash references INVALID |
| Duplicate proposal | Exact event replay returns same ID/record, no new entry; different event at revision 1 INVALID |
| Stale data timestamp | INSUFFICIENT_EVIDENCE; future or malformed time INVALID |
| Unsupported version | INVALID, UNSUPPORTED_VERSION |
| Conflicting strategy metadata | NON_COMPLIANT; unsupported strategy version REVIEW_REQUIRED |
| Oversight unavailable | Simulated unavailable check -> REVIEW_REQUIRED; missing actual local dependency -> UNAVAILABLE/no assessment |
| Invalid risk metadata | Missing/malformed/negative types INVALID; coherent excessive loss or bad geometry NON_COMPLIANT |
| Replay previously assessed | Original immutable record returned, including after withdrawal; cannot reopen lifecycle |
| Invalid lifecycle | Missing initial state, repeated initial event, scope change and revision after withdrawal INVALID |
| Evidence and audit corruption | Hash/body mismatch, duplicate refs, record mutation/reordering rejected |
| Resource exhaustion | Bounded new attempts return explicit capacity error without overwrite; known replay remains available |

## Not executed and not claimed

No full Sentinel backend regression, PostgreSQL integration suite, dashboard/browser
suite, deployment test, real TradingView export mapping, market-data test, broker
connectivity, durable/multi-process idempotency or genuine-forward performance was
run. The new adapter never accesses a database. Existing unrelated dirty Trading
source/test changes were retained; the 367-test result describes this actual checkout,
not a clean historical commit or deployed producer.

Commands are in [the runbook](RUNBOOK.md). Source boundaries and trust limits are in
[security verification](SECURITY_BOUNDARIES.md). The demo exercises both actual local
entry points and asserts equal assessment content and consistent journal hashes.
