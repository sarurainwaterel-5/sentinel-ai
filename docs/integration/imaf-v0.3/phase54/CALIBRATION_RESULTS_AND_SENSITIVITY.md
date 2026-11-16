# Phase 54 — Synthetic calibration results and sensitivity

RESEARCH ONLY — NOT APPROVED FOR EXECUTION. **Empirical result: INCONCLUSIVE.**

The deterministic demonstration contains **12 synthetic acquisition candidates** (three invented histories per mapping), producing48 paired candidate assessments:36 return-inside observations and12 expired observations. These are software fixtures, not12 real trades,48 independent samples or evidence of profitability. The three artificial chronological groups intentionally return after1,2 and3 bars to exercise candidate sensitivity; their calendar dates include future synthetic timestamps and do not claim observed market history.

Real historical eligible event count: **0**. Empirical return rate, median, distribution, confidence interval, significance, volatility sensitivity and out-of-sample stability cannot be estimated. The machine-readable real-data fields are null/empty with INSUFFICIENT_HISTORICAL_DATA. A caller declaring REAL_HISTORICAL_DATA is insufficient authentication; a trusted historical ingestion/provenance gate is still required before real inference.

## Synthetic paired-limit demonstration

The following entries are output directly from the synthetic experiment. The count bound and duration vary together, so they do not identify separate causal sensitivity to count versus time. Additional custom pairs must be explicit and precommitted. Larger windows mechanically include more returns; this alone does not establish usefulness or justify choosing a limit.

| Mapping / candidate | Synthetic events | Returns | Expired | Unresolved | Median return latency (seconds) |
|---|---:|---:|---:|---:|---:|
| 15M→1M:15M-1M-1 | 3 | 1 | 2 | 0 | 60.0 |
| 15M→1M:15M-1M-2 | 3 | 2 | 1 | 0 | 90.0 |
| 15M→1M:15M-1M-3 | 3 | 3 | 0 | 0 | 120.0 |
| 15M→1M:15M-1M-5 | 3 | 3 | 0 | 0 | 120.0 |
| 1H→5M:1H-5M-1 | 3 | 1 | 2 | 0 | 300.0 |
| 1H→5M:1H-5M-2 | 3 | 2 | 1 | 0 | 450.0 |
| 1H→5M:1H-5M-3 | 3 | 3 | 0 | 0 | 600.0 |
| 1H→5M:1H-5M-5 | 3 | 3 | 0 | 0 | 600.0 |
| 4H→15M:4H-15M-1 | 3 | 1 | 2 | 0 | 900.0 |
| 4H→15M:4H-15M-2 | 3 | 2 | 1 | 0 | 1350.0 |
| 4H→15M:4H-15M-3 | 3 | 3 | 0 | 0 | 1800.0 |
| 4H→15M:4H-15M-5 | 3 | 3 | 0 | 0 | 1800.0 |
| 5M→15S:5M-15S-1 | 3 | 1 | 2 | 0 | 15.0 |
| 5M→15S:5M-15S-2 | 3 | 2 | 1 | 0 | 22.5 |
| 5M→15S:5M-15S-3 | 3 | 3 | 0 | 0 | 30.0 |
| 5M→15S:5M-15S-5 | 3 | 3 | 0 | 0 | 30.0 |

Each mapping uses candidate counts1,2,3,5 paired with its execution-bar duration. Full sorted latency distributions, paired values, source labels, boundaries, evidence IDs, timing and per-assessment outcomes are preserved in the private JSON outputs. Aggregate latency across mixed timeframes/candidate reuse is a descriptive test diagnostic and should not be interpreted as a market estimate.

## Chronological validation and uncertainty

The demonstration explicitly labels training, validation and held-out intervals in chronological order; it never randomly splits observations. It produces training16/16, validation12/16 and held-out8/16 **synthetic assessment** returns because fixtures intentionally change latency. These are constructed examples, not evidence of instability in MNQ or out-of-sample performance.

Candidate evaluations are correlated repeated measurements of the same events. Exact duplicate events are removed, conflicting/shared-ancestry groups quarantined, boundary-crossing outcomes censored, and outside-plan samples isolated. Disjoint declared ancestry does not establish statistical independence. Consequently independent sample count and confidence intervals remain null; no significance test or expectancy claim is made.

All fixtures have morning descriptive labels; there is no observed inter-session comparison. No approved, precommitted volatility-regime definition or historical regime coverage exists; regime results remain unresolved. Session observation flags use America/Chicago and are independently tested across DST. They are not full strategy/session/account eligibility.

## Reproduction and retained evidence

Implementation and commands: Trading `services/return-calibration/README.md`. The private workspace `outputs/imaf-phase54/` contains synthetic input, calibration JSON, an exact-input/source/runtime-bound archive and replay output; `final/` is the final source-bound generation if an earlier archive predates the final resource guard. Earlier archives are retained as historical artifacts and correctly become unavailable under changed source bindings. Raw test logs remain in `logs/`.

Owner-supported numerical limits: **none**. Weakly supported numerical limits: **none**. All16 requested candidates remain **inconclusive** pending licensed real history, independent boundary/event provenance, precommitted temporal partitions, regime/coverage definitions and defensible uncertainty analysis. Return-inside observation does not establish a model-qualified sweep, MSS, accepted structure, full IMAF setup or trading authorization.
