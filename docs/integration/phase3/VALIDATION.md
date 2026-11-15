# Executed validation — 2026-11-15

Verdict: independent research subset verified; full IMD/IMAF compliance INCOMPLETE.

All Node suites below were executed directly with the Phase 1 deny-network preload,
not inferred from inspection. Trading tests used the explicit pinned Sentinel root.
Raw TAP is retained in workspace outputs/phase3-independent-imaf/test-results/.

| Log | Tests | Pass | Fail | Skip |
|---|---:|---:|---:|---:|
| phase3-durable.tap | 8 | 8 | 0 | 0 |
| phase3-existing-trading.tap | 367 | 367 | 0 | 0 |
| phase3-previous-cli.tap | 3 | 3 | 0 | 0 |
| phase3-previous-contract.tap | 45 | 45 | 0 | 0 |
| phase3-previous-durable-security.tap | 3 | 3 | 0 | 0 |
| phase3-previous-durable.tap | 29 | 29 | 0 | 0 |
| phase3-previous-security.tap | 4 | 4 | 0 | 0 |
| phase3-previous-trading-contract.tap | 49 | 49 | 0 | 0 |
| phase3-previous-trading-durable.tap | 3 | 3 | 0 | 0 |
| phase3-security.tap | 4 | 4 | 0 | 0 |
| phase3-strategy.tap | 57 | 57 | 0 | 0 |
| phase3-trading.tap | 3 | 3 | 0 | 0 |
| phase3-existing-python.txt (existing Sentinel synthetic oversight tests) | 81 | 81 | 0 | 0 |

72 new unique cases: evaluator 57, durable strategy 8, security 4, Trading adapter 3.
584 existing regression executions; 656 total case executions, zero failures/skips.
The shared 45-case contract suite runs in both repositories: 656 is not a unique-test
count. Trading existing research integration/unit selection contributed 367 cases;
Sentinel existing Python synthetic tests contributed 81. Full backend/Postgres,
browser, hardware failure, live feeds and broker suites were not run.

## Required scenarios

| Scenario | Executed verification |
|---|---|
| Bullish / bearish | Independently calculated entry/stop/target; research PASS, REVIEW_REQUIRED, full IMAF INCOMPLETE |
| Sweep without MSS | Close-break predicate fails; platform confirmation cannot rescue it |
| MSS without displacement | Body/range and prior baseline predicates fail independently |
| Invalid FVG | Three closed candles fail gap requirement |
| Unsupported pairing | INVALID before observations; all four required mappings tested |
| Session violation | Early half-open end and explicit post-09:30 bounds checked |
| Missing candles | INSUFFICIENT_EVIDENCE, no fabricated confirmation |
| Contradictory structure | NON_COMPLIANT and disagreement references |
| Stale evidence | INSUFFICIENT_EVIDENCE at changed decision cutoff |
| Future leakage | Future receipt/unclosed/appended candles rejected |
| Duplicate | Original assessment returned; changed snapshot creates conflict |
| Restart/replay | Separate child processes reproduce archived result exactly |
| Conflicting strategy metadata | Unsupported version fails; malformed type INVALID |
| Unavailable risk | INSUFFICIENT_EVIDENCE; stale/future state cannot establish compliance |
| DST | Summer/winter, repeated/skipped hour and elapsed 48-hour pause checked |

Boundary tests also cover strict pivot ties, delayed receipt, first retracement,
proposal evidence integrity, type/bounds checks, input immutability, pin mismatch,
corruption, dependency unavailability and immutable replay disagreement.

Sources: strategy/evaluator.test.mjs, strategy/durable.test.mjs,
strategy/security.test.mjs under backend/evaluation/synthetic_oversight and Trading
services/synthetic-oversight/strategy.test.mjs. Test success does not resolve any
missing doctrine in SPECIFICATION_COVERAGE.md.
