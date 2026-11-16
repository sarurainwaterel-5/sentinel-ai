# Multi-timeframe reconstruction

Fresh engineering input:6540 selected MNQ1M records from the supplied MarketParquet ZIP, normalized without changing OHLCV. Ratio adjustment, unknown dated contract and unknown actual receipt remain explicit.

`session-plan.mjs` validates each supplied UTC interval against its America/Chicago local date, clock and offset. It anchors full5M/15M/1H/4H windows at that explicit session open, validates ordering/non-overlap and preserves source/reviewer references. It does not infer a calendar, holiday or missing record. DST tests cover both Chicago clock transitions and actual OHLCV reconstruction with complete minute lineage. Winter/summer offsets are checked rather than substituting a fixedUTC offset.

The real-data engineering demonstration used an explicitly labeled nominal17CT–16CT schedule hypothesis, not an authenticated exchange calendar or owner-approved market definition. The first nominal session is truncated in the supplied observations. Five daily 3-hour 4H-session ends are labeled incomplete and excluded from full 4H bars.

| Frame | Independent OHLCV matches | Incomplete windows |
|---|---:|---:|
|5M|1308|72|
|15M|436|24|
|1H|109|6|
|4H|23|2|

Total:1876 matching engineering-only full windows,104 unresolved windows,5 separate partial ends. The independent check recalculated open/maximum high/minimum low/last close/summed volume directly from minute rows, checked exact source lineage, adjustment and null contract, and repeated reconstruction identically. Incomplete results carry no OHLCV. No source candles were filled/interpolated.

Unknown historical `available_at` staysnull in normalized records. Explicit engineering modeling uses bar close separately and takes maximum source/plan availability. Outputs areENGINEERING_ONLY_MODELED_AVAILABILITY, neverCOMPLETE, and cannot pass the empirical adapter. Future or incomplete OHLCV is suppressed. These distinctions are tested; no unobserved historical receipt is invented.

Private exact inputs/plans/results: `outputs/phase55b-verification-20261116/data/fresh-reconstruction.engineering-only.json`. An authoritative reviewed calendar, source-specific timestamp convention and approved historical availability policy remain required for empirical interpretation.
