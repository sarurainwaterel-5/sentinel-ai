# Phase 2 executed validation

Final completed runs on November 15, 2026, Node 22.22.1, SQLite 3.46.1.
All Node runs below preload Phase 1 deny-network.mjs. No external service or mock
SQLite database was used for persistence claims.

| Executed suite | Passed | Failed | Skipped | Evidence |
|---|---:|---:|---:|---|
| New persistence/migration/restart/concurrency/replay | 29 | 0 | 0 | durable.test.mjs; 21.384 seconds; real disk DBs and independent processes |
| New durable security | 3 | 0 | 0 | durable-security.test.mjs |
| New offline CLI | 3 | 0 | 0 | durable-cli.test.mjs |
| New Trading durable cross-repository integration | 3 | 0 | 0 | Trading services/synthetic-oversight/durable.test.mjs |
| Existing Sentinel Phase 1 contract | 45 | 0 | 0 | protocol.test.mjs |
| Existing Sentinel Phase 1 security | 4 | 0 | 0 | security.test.mjs |
| Existing Trading shared contract/adapter | 49 | 0 | 0 | Trading adapter.test.mjs (45 shared + 4 adapter) |
| Existing Sentinel Python oversight/CSV | 81 | 0 | 0 | four existing test_trading* files; 2.27 seconds |
| Existing Trading unit/adversarial | 367 | 0 | 0 | tests/run.js; 10.528 seconds, networking disabled |

38 new unique test definitions passed. Listed runs total 584 case executions;
45 shared Phase 1 cases intentionally run in both repositories, so this is not
584 unique tests. There are no failures/skips in the final completed runs.

Raw final TAP/Python logs, source hashes and an actual retained CLI demonstration
are outside Git in workspace `outputs/phase2-durable-oversight/verification.json`
and adjacent files. The demo initializes disk history, submits, exits, resubmits
from a separate process (DUPLICATE), and replays from another process (REPLAY_MATCH).
It retains the original exact assessment despite a later supplied clock.

## Required failure/restart demonstrations

| Requirement | Actual executed mechanism / result |
|---|---|
| Successful assessment restart | Independent child exit/reopen; identical original row/assessment returned. |
| Duplicate after restart | DUPLICATE; one DECISION/claim, unchanged ID and body. |
| Conflict after restart | Changed canonical content -> CONFLICT row; original still duplicates unchanged. |
| Concurrent duplicate | Six independent processes -> one STORED, five DUPLICATE, one original ID. |
| Concurrent conflicting content | Two processes -> one STORED, one CONFLICT, one original decision. |
| Concurrent distinct proposals | Four processes -> four consistent serialized audit/claim records. |
| Transaction rollback | Test driver throws on claim INSERT after audit INSERT against actual SQLite; both roll back, then same process retry stores once. |
| Interrupted persistence | SIGKILL before COMMIT -> no decision, safe retry; SIGKILL after COMMIT before acknowledgement -> original DUPLICATE. |
| Payload corruption | Disposable fixture modified without matching hash -> duplicate/replay fail closed; no invented assessment. |
| Unsupported historical version | Separately recorded REPLAY_UNAVAILABLE / UNSUPPORTED_HISTORICAL_CONTRACT. |
| Missing historical evaluator | Unrecognized archived hash -> REPLAY_UNAVAILABLE, never current-version fallback. |
| Missing historical evidence | Self-consistent fault fixture missing original evidence inventory -> REPLAY_UNAVAILABLE. |
| Replay mismatch | Self-consistent historical fault fixture disagrees with deterministic reproduction -> separate REPLAY_MISMATCH, original untouched by replay. |
| Database unavailable | Missing file/closed handle returns no store/assessment; never memory fallback. |
| Temporary database failure/recovery | Independent process holds exclusive SQLite lock; submit fails closed after busy timeout, then succeeds after lock-holder termination. |
| Immutable history | Real SQL UPDATE/DELETE attempts on all history/claim/migration tables rejected by triggers; unique claim insertion enforced. |
| Explicit corrections | New identity with supersedes reference appends linked decision; old response unchanged; unknown target rejected. |
| Runtime mismatch | Stored original runtime differs -> REPLAY_UNAVAILABLE. |
| Unchanged Phase 1 bounds | Valid >8192-byte canonical wire persists/replays; history remains readable beyond 128 records. |

Historical corruption/mismatch fixtures are deliberately built with direct SQL in
disposable test stores, temporarily removing/restoring immutable triggers and
recomputing hashes where needed. This exercises replay diagnostics, not a runtime
history-editing API. Runtime exposes no update/delete or test fault hook.

## Preliminary failures and correction

The first process tests could not parse piped child stdout in this host environment;
the run was stopped and not counted as a successful test run. A separate file-write
probe established actual child execution; private result-file IPC then allowed
complete restart/concurrency/crash verification. The original partial log is retained.
A CLI test also found the missing-database result omitted explicit assessment:null;
that response was corrected and the complete affected suites rerun successfully.
The preliminary CLI failure log is retained separately from final results.

## Not executed / limitations

No production migration, PostgreSQL integration suite, full Sentinel backend suite,
dashboard/browser suite, real TradingView CSV mapping, broker/live-data test, physical
power-loss/storage-hardware test, hostile-administrator tamper test, distributed
multi-host service or backup-restore exercise was run. These are untested components,
not hidden test skips. Current scope is local on-disk synthetic oversight. Node's
SQLite binding remains experimental on this tested runtime.
