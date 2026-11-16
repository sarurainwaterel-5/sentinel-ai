# Phase 55B — provenance and license review

**RESEARCH ONLY — NOT APPROVED FOR EXECUTION.** Reviewed 2026-11-16. Public provider statements describe products; they do not authenticate the supplied bytes or establish the owner's acquisition rights.

## Findings and classifications

Both user-supplied inputs remain `PROVENANCE_UNRESOLVED`, `LICENSE_UNRESOLVED`, and `RESEARCH_USE_BLOCKED` for automated strategy calibration pending file-specific acquisition and license evidence. This classification does not assert infringement. Inspection and engineering validation are authorized by this mission; calibration requires the additional gate specified by the owner.

| Input | Claimed provider | Public methodology evidence | File-specific gap |
|---|---|---|---|
| `cme.mnq.bars.1m.2026-11.parquet` | Historical Futures Data | [Official documentation](https://historicalfuturesdata.com/en/docs) describes bar OHLCV from additive back-adjusted continuous ticks, UTC epoch-aligned intraday buckets, skipped empty buckets, and roll/manifest/validation hashes. | No authenticated download receipt, matching generation manifest/roll ledger, or rights statement bound to this monthly MNQ file established. No contract identity should be invented from its filename. |
| `intraday_sample.zip` | MarketParquet | [Official methodology](https://marketparquet.com/data-quality) and [schema documentation](https://marketparquet.com/documentation) describe ratio back-adjusted root-symbol futures, naive US/Eastern bar-open timestamps, and omitted nontrading minutes. | No authenticated acquisition record or license confirmation bound to this archive established. Official methodology is a provider claim, not independent file authenticity proof. |

Source timestamps and adjustment designations may be recorded as provider-documented interpretations, clearly separated from intrinsic Parquet metadata. Neither dataset is established as unadjusted dated-contract executable prices. Preserve separate series; no raw or trivially transformed bars belong in a public repository. Quarter-tick compatibility alone does not establish an unadjusted series.

## Official license evidence and limits

[MarketParquet license](https://marketparquet.com/license) permits internal modeling/research and use by operated AI agents, permits non-reconstructable derived results, and prohibits raw/trivially transformed data redistribution. Its scope section ties the license grant to an account/organization and archive payment. [Terms effective 2026-11-04](https://marketparquet.com/terms) acknowledge an anonymous intraday sample and state research/internal-use permissions, but do not establish that this supplied ZIP is that sample or resolve the precise sample grant for this owner. A freely downloadable file is insufficient evidence by itself.

[Historical Futures Data pricing](https://historicalfuturesdata.com/en/pricing) describes purchased access for internal research/backtesting, excluding redistribution/resale/shared account access. Its [sample page](https://historicalfuturesdata.com/en/samples) permits private/internal sample evaluation, research and backtesting, excluding commercial use and sharing cleaned data. That page describes a specific ES/NQ sample pack; do not silently apply its scope to this MNQ monthly file. The [documentation](https://historicalfuturesdata.com/en/docs) confirms free-account monthly access, which is access information rather than proof of this file's authorized acquisition or applicable full usage terms.

These are paraphrased provider assertions checked on the review date, not legal conclusions or exchange certification. No paid purchase, login, provider API request, download, or credential use was made for this review. Only public documentation pages were browsed.

## Minimum evidence to unblock

Record an acquisition URL/reference and owner acquisition date if known; exact SHA-256 binding to supplied bytes; applicable license text/version with evidence it covers this exact sample/monthly product and the intended private research; provider timestamp/bar-label semantics; and release/roll linkage where available. Unknown acquisition dates remain null; filesystem modification times are not substituted. Do not mark authenticity verified solely from matching names/schema/prices.

The machine-readable manifest and validation reports retain actual file hashes, inspected coverage, columns, quality flags and unresolved classifications. An operator cannot turn a bare boolean into proof: any future verified status must reference reviewable acquisition/license evidence. Calibration remains blocked until provenance, licensing, identity, adjustment treatment, timestamp and quality requirements are all satisfied. Live execution and production deployment remain denied even after research authorization.
