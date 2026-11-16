# Phase 54 independent verification

**DRAFT — NOT APPROVED FOR EXECUTION. Execution authorization: DENIED.**

## Scope and independence

The independent verification workstream read the complete supplied Phase 54 attachment, inspected the current Trading worktree and Phase 53 provenance/replay components, and reviewed existing Sentinel session tests. Trading started at `2e3d1a5` with the previously disclosed nine unrelated modified/untracked paths. The directive attachment ends immediately after “Add deterministic tests”; no absent continuation is presumed.

The independent suite is separate from the implementation tests. Its expectations are derived from hand-constructed completed candles, strict integer tick prices, known-before-acquisition boundaries and explicit finite configuration commitments. Synthetic fixtures establish engineering behavior only, never historical MNQ observations, numerical calibration authority, institutional participation or full setup qualification.

## Review criteria

- A boundary and candidate configuration must be known strictly before the acquisition bar opens; unknown intrabar order cannot justify retrospective selection.
- Buy-side acquisition requires a strictly higher high; sell-side acquisition requires a strictly lower low. Equality is insufficient.
- Return requires a strictly later completed candle and strict close inside. The acquisition candle and an equal close cannot qualify.
- Completed candle availability determines recognition. Both candle count and elapsed UTC duration must hold; missing bars and session gaps cannot reset or silently extend the bound.
- Research candidate limits cannot become execution permission, and downstream unresolved structural predicates cannot become successes.
- Late/future evidence must not rewrite earlier terminal observations. Replays must use original inputs and deterministic clocks, including across a real process restart.
- Event deduplication and statistical partitions require independent review beyond deterministic engine arithmetic. Multiple labels, configurations and timeframe views do not establish independent market samples.
- Existing four Central Time discovery windows, account risk controls and mandatory restrictions remain unchanged. Descriptive session tagging is not session eligibility or calendar authority.

## Executed results

The independently authored `services/return-calibration/adversarial.test.mjs` ran directly under Sentinel’s existing deny-network preload. Final result: **44 tests, 44 passed, 0 failed, 0 skipped, 0 cancelled**. Raw log: `/tmp/phase54-independent-final.tap`.

```sh
node --import '/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs' services/return-calibration/adversarial.test.mjs
```

Working directory: `/home/rain/Documents/ChatGPT/Sentinel Trading AI`.

The suite constructs its own two-candle input rather than importing implementation fixture expectations. It covers strict buy/sell acquisition, acquisition-candle exclusion, equality exclusion, invalid ticks/schema/source/version/bounds, duplicate IDs/timestamps, reversed records, gaps, incomplete bars, unavailable future prices, input preservation, delayed acquisition receipt, inclusive exact elapsed boundary versus one millisecond late, independent candle-count expiry, shared ancestry, terminal-history preservation, unauthenticated real-source claims, replay prefixes, malformed objects/getters, DST transitions and seasonal windows, duplicate-event denominators, conflicting candidate definitions, chronological partitions and synthetic inference restrictions.

## Defects found and resolved

The first expanded 32-case run passed 31 and failed one genuine fail-closed defect. A hostile `source` getter threw during input validation; the catch path then called `fail(input)`, which reread that getter and escaped. The engine now constructs malformed-input failures without consulting the failed input. The failing run is retained at `/tmp/phase54-independent-initial-failure.tap`; the final regression passes. A separate replay getter regression also passes. Unavailable future OHLC access is tested with a throwing getter: no access occurs before visibility.

Independent review of the initially staged statistics identified four reporting issues before final acceptance: candidate rows inflated acquisition counts; the same candidate label could pool different numerical bounds; outside-plan observations entered planned summaries; and slow candidates unnecessarily censored earlier candidate results. The installed implementation now reports unique acquisition-event count separately from assessment observations, rejects conflicting candidate definitions, excludes outside-plan rows from planned summaries, and censors each assessment by its own evidence timing. Independent regressions verify the first three; source review verifies the per-assessment censoring.

## Restart and archive review

The reviewer read `statistics.mjs`, `archive.mjs`, `cli.mjs`, `experiment-fixtures.mjs` and `statistics.test.mjs`, then independently reran the implementation statistics/restart suite under the same preload:

```sh
node --import '/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs' services/return-calibration/statistics.test.mjs
```

Result: **16 tests, 16 passed, 0 failed, 0 skipped, 0 cancelled**, raw log `/tmp/phase54-independent-statistics.tap`. These are repeat executions of the implementation’s 16 test definitions, not 16 additional unique definitions. The restart case actually launches separate record and replay Node processes, changes the current input file, then reproduces the archived request and result. Exclusive output creation refuses to overwrite an existing reply. Integrity failure, unavailable source/runtime bindings and result mismatch remain visible outcomes. Hash integrity is not an authenticated signature, independent custody or production append-only audit proof.

## Interpretation and remaining limits

The engine uses the disclosed **RESEARCH_COMPLETION_ANCHORED** timing convention: elapsed time begins at the scheduled acquisition-bar close, while qualifying return recognition uses completed-bar availability. Delayed acquisition receipt cannot extend the interval. Candle-open acquisition timestamps, scheduled close, receipt and unresolved actual intrabar acquisition are distinct. This is a conservative research convention rather than approval of exact intrabar sweep timing or numerical strategy limits.

No verified real historical dataset is established by these tests. `REAL_HISTORICAL_DATA` input is a caller claim, remains unauthenticated, contributes zero approved empirical samples and cannot create a supported numerical recommendation. Sample independence, confidence intervals, volatility regimes, out-of-sample empirical stability, full IMAF qualification and profitability remain unestablished. Synthetic cohort partitions demonstrate code paths only.

The descriptive session formatter uses IANA Chicago timezone rules and retains all four selected morning observation windows. It does not implement an exchange calendar, operational session eligibility, account restrictions or an order permission. Existing session/risk code remains outside this additive research implementation. No broker, order, network-provider or credential path is imported by the reviewed new modules. Execution authorization remains **DENIED**.


## Final root review follow-up

After root review identified additional missing-evidence and ancestry risks, the engine was corrected to withhold a boundary whose raw ancestry overlaps its acquisition, and to classify a late-discovered missing expected bar as data-integrity unresolved rather than a clean failed return. If no subsequent bars are supplied at all, elapsed expiry may remain a timing fact, but `MISSING_EXPECTED_COMPLETED_CANDLES` prevents it from entering a resolved statistical denominator. This distinguishes failure to observe a return from evidence that a return did not happen. Already observed valid returns remain unchanged by later gaps; data-quality revisions never authorize expired-event revival.

Three additional independent regressions exercise these exact cases, including direct statistics-denominator verification for an absent window. The final **43-case** independent suite was executed against the corrected engine; all passed. The **16-case** statistics/restart suite was rerun again after these changes and passed. The earlier 40-case result is superseded by the current 43-case result, not added to it. No pre-existing expectation required weakening.


## Final engineering work bound

The final source also rejects estimated work above one million research steps, both for a single evaluation and for the aggregate replay cutoff count. The estimate is candle count × sum(candidate candle limits + 1), multiplied by replay cutoffs where applicable. This is a resource guard, not an approved trading interval. The added independent regression verifies excessive engine work and excessive multiplied replay work return denied INVALID results before frames are produced. Final source execution: **44 independent cases passed, 0 failed, 0 skipped**, and the separate **16-case** statistics/restart rerun again passed. These final runs supersede all earlier success counts.


## Final cross-request budget and authoritative rerun

Root’s final availability review additionally bounded the sum of estimated work across all experiment requests to one million steps. Without this aggregate bound, separately valid requests could multiply work up to the experiment request limit. The independent reviewer inspected this rejection before execution and reran the frozen-source suites once more: **44 independent cases passed, 0 failed, 0 skipped**, and **17 statistics/restart cases passed, 0 failed, 0 skipped**. The seventeenth statistics case covers aggregate cross-request rejection. These are the final authoritative suite counts; earlier 16-case statistics runs are historical intermediate executions, not extra unique tests. Current logs remain `/tmp/phase54-independent-final.tap` and `/tmp/phase54-independent-statistics.tap`.
