# Phase 54 — Historical data readiness

RESEARCH ONLY — NOT APPROVED FOR EXECUTION.

Review date: November 16, 2026 (America/Chicago). **Readiness: INSUFFICIENT_HISTORICAL_DATA.** No usable, licensed historical MNQ bar dataset was established in the bounded local inspection. This is a search result, not proof that no dataset exists elsewhere. Synthetic fixtures support software validation only; no interval recommendation is empirically supported.

## Sources inspected and limits

The inspection used repository/file-name inventories and targeted source/document reads in `/home/rain/Documents/ChatGPT/Sentinel Trading AI`, `/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai`, `/home/rain/Documents/ChatGPT/Sentinel IR SRE/outputs`, and `/home/rain/Downloads`. Extension/name screening covered CSV, JSONL, Parquet, Feather, MNQ, OHLC, candles, historical, fixtures, recordings and manifests; dependency/Git/virtual-environment directories were excluded. JSONL files under Sprint 21 extraction were identified by their extraction paths, not ingested as market data. Downloads contains two generically named Supabase query CSVs; their contents were not read or treated as market exports. Generic opaque files, private databases and credentials were not scanned. No claim of a full filesystem or database audit is made.

| Evidence | Verified finding | Research consequence |
|---|---|---|
| Trading `tests/fixtures/market-data.js` | Explicitly invented integer-quarter-tick bars and test-only sessions | SYNTHETIC_TEST_DATA, not exchange history |
| Trading `tests/fixtures/strategy-paper.js` | Invented causal OHLC input | SYNTHETIC_TEST_DATA |
| Trading `services/structure-research/replay-fixtures.mjs` | Phase 53 synthetic source | SYNTHETIC_TEST_DATA |
| Local `outputs/sprint22-paper-oversight-20261115/synthetic-input/synthetic-framing-example.csv` and `synthetic-csv-capture/evidence-001.csv` | Synthetic import examples | No historical sample contribution |
| Local `outputs/sprint22-paper-oversight-20261115/tradingview-account-read/export-inspection.md` | Prior observed empty-account UI yielded no CSV | Account observation is not historical bars; no new browser/provider retrieval occurred |
| Trading `docs/runbooks/ibgateway-linux-setup.md`, dated November 8 metadata/permission probe | Documented MNQZ6 minimum tick 0.25; realtime request code 354, no bid/ask | A prior documented probe, not independently repeated now, establishes no available history, entitlement or license |
| Trading `services/market-data/README.md`, `src/tradovate.js`, `src/ibkr.js` | Read-only adapters and explicit prerequisites exist | Adapter implementation is not an entitled data source or acquired dataset |
| Trading `docs/runbooks/lucid-tradovate-access.md` | Requires approved entitlement, contract mapping and provenance | No Tradovate/CQG/Lucid entitlement inferred |

No broker, provider service, live market-data feed or private database was contacted. No market observations were fabricated. Connected service entitlement was not assumed; existing provider connectors were inspected as source code, not invoked.

## Contract specification check

The CME [Micro E-mini Nasdaq-100 page](https://www.cmegroup.com/markets/equities/nasdaq/micro-e-mini-nasdaq-100.margins.html) identifies the futures contract as $2 times the index with a minimum price increment of **0.25 index points**; the official [Micro E-mini FAQ](https://www.cmegroup.com/articles/faqs/micro-e-mini-equity-index-futures-frequently-asked-questions.html) gives **$0.50 per outright MNQ tick**. Consulted November 16, 2026. Options and calendar spreads have different specifications and are outside this harness. Existing Trading `services/risk-gateway/index.js` independently pins 50 cents per tick. A pinned tick specification does not authenticate a supplied contract or data source.

## Required acquisition package before real calibration

1. Owner-authorized, licensed offline export with provider/product/version, creation time, permitted programmatic research, retention and redistribution terms. Do not infer rights from a login, visible quote, or paper account.
2. Explicit expiry-specific MNQ contract identity, provider ID, exchange and expiration. Provide non-adjusted raw contract bars and a dated rollover mapping/rule; identify any continuous/back-adjusted series separately. Never aggregate different expiries silently. No rollover rule was established by this review.
3. Closed OHLCV at **15-second resolution** for the 5M→15S experiment; complete 1M, 5M and 15M bars can be derived only from complete finer bars using reviewed aggregation. Minute bars cannot recover 15-second paths. Preserve native inputs plus transformation lineage and hashes.
4. UTC instants with original timezone/offset and explicit bar-open versus bar-close convention; completion and actual availability timestamps, corrections/revisions, source row IDs and underlying event ancestry. Historical downloads often lack actual contemporaneous availability; label any assumed latency rather than claiming live causal fidelity.
5. America/Chicago exchange/session metadata and an authoritative exchange-trading-day/calendar version including holidays, maintenance, DST and half-days. UTC offset alone is insufficient. Date ranges must include session coverage and, if available, both DST regimes; never manufacture unavailable periods.
6. Quality manifest: row count, coverage, duplicates/corrections, ordering, missing bars, session gaps, OHLC consistency and quarter-tick alignment. Preserve gaps explicitly rather than filling prices or extending candidate windows.
7. Liquidity-boundary evidence selected/available before each acquisition: price, side, construction method/version, source rows, identity and availability. Provider bars alone do not approve a boundary-significance predicate.
8. Precommitted paired candidate limits and chronological partition boundaries recorded before outcomes. Preserve event-family ancestry across partitions/candidates; report dependent samples and refrain from significance claims without justified assumptions.

These are data requirements, not a provider purchase recommendation or authorization to contact a broker. No numerical sample-size threshold, volatility regime definition, statistical significance threshold or optimal interval is invented. Adequacy must be justified from actual coverage and uncertainty. Real sample count currently established: **0**; empirical latency, confidence intervals, session/regime differences and out-of-sample stability are **not estimable**.
