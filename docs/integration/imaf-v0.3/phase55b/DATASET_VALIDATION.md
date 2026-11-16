# Phase 55B historical dataset validation

Research only. Execution DENIED. Inspection performed on the supplied local files; provenance and license are unresolved. No automated empirical strategy calibration was run.

## Dataset A

`/home/rain/Downloads/cme.mnq.bars.1m.2026-11.parquet`: 11,349 rows. Actual UTC timestamp range **2026-11-01 23:00 through 2026-11-12 04:08**, inclusive. This is partial November coverage, not an entire month. Columns: `ts timestamp[ns,tz=UTC]`, OHLC double, `volume uint32`, `trade_count uint32`. Instrument and dated contract columns are absent: MNQ attribution is a filename claim, not independently established record identity. UTC is encoded; exact file-specific bar-open/close labeling remains unbound.

Observed OHLC, finite positive prices, integer nonnegative volume, quarter-point grid, ordering and unique timestamp checks passed. Eight discontinuities contain 3,360 absent minute slots. These are observations, not a claim of missing exchange trading candles: no authoritative session/holiday manifest is bound. UTC-weekend rows: 120; Chicago-weekend rows: 840. Sunday futures activity cannot be treated as invalid merely because its calendar date is a weekend. File-specific adjustment is unresolved; provider-level additive-continuous documentation does not prove this particular file's methodology. Authenticity, acquisition date, research license and redistribution rights remain unresolved. **Canonical normalization blocked** by unresolved instrument identity and timestamp label. Raw file preserved.

## Dataset B

`/home/rain/Downloads/intraday_sample.zip`: 64,680 total rows in five futures 1-minute members, **6,540 MNQ rows**. Other symbols: CL, E6, ES, GC, MES, NQ, RTY, YM, ZN. Other archive assets and timeframes remain intact and were not substituted for the selected 1-minute research input. Selected MNQ UTC range **2026-04-06 04:00 through 2026-04-10 20:59**, inclusive. Fields: naive microsecond `timestamp`, string `symbol/asset_type`, double OHLCV. Archive README explicitly describes **US/Eastern bar open**, continuous **ratio-adjusted futures**. No dated contract identifier exists.

Observed OHLC, volume, ordering and duplicates passed. All 6,540 selected MNQ rows are off the unadjusted quarter-point grid, consistent with the declared adjustment designation; they are preserved as supplied and cannot represent executable contract fills. Four discontinuities contain 240 absent minute slots; exchange-calendar classification remains unresolved. Chicago-weekend count 60 is calendar evidence, not automatic invalidity. Safe ZIP processing validates every member before bounded in-memory reads; no paths are extracted.

A private engineering-only normalized 6,540-row representation preserves source prices and ratio-adjustment. Historical receipt times are unknown. The separate bar-close availability model is a declared engineering hypothesis and is never relabeled as observed provider availability. Licensing and exact artifact acquisition provenance remain unresolved: **RESEARCH_USE_BLOCKED**. The README's “free sample” description is not an explicit license grant.

## Reproducible evidence

Private local evidence (not committed market data): `outputs/imaf-phase55b/private/dataset-inspection.json` contains checksums, actual schemas, per-file counts, symbol counts and every gap; `marketparquet-mnq-normalized.json` is the separately generated engineering artifact. Implementation: Trading `services/historical-research/inspect_dataset.py`, `normalize.py`, `test_inspect.py`. Parser dependency pyarrow 26.0.1 installed only under `/tmp/phase55b-python-deps`; no runtime or repository dependency changes.

The dataset reports establish local content consistency, not provider authenticity, exchange completeness, regulatory permission or profitable strategies. Both artifacts remain `PROVENANCE_UNRESOLVED`, `LICENSE_UNRESOLVED`, `RESEARCH_USE_BLOCKED`.
