# Historical normalized research schema

`imaf.historical.normalized.v1` — research only; execution DENIED.

Top-level: `version`, `dataset_id`, original-container `source_sha256`, `provenance_status`, `license_status`, `research_use`, `rows`, `authority`. The Python normalizer always emits unresolved provenance/license and blocked research use; a caller-supplied identity cannot verify authorization.

Each row contains:

| Field | Meaning |
|---|---|
| id | SHA-256 of container checksum, original row index, instrument, UTC open; stable for identical input order |
| instrument | MNQ, explicit source selection; Dataset A requires independent identity evidence |
| contract | Nullable dated contract; continuous series do not invent one |
| contract_identity_basis | UNRESOLVED or CALLER_DECLARED_NOT_INDEPENDENTLY_VERIFIED |
| open_at / close_at | Explicit UTC one-minute boundaries; naive source values only interpreted via declared Eastern bar-open convention |
| available_at | Null when historical receipt evidence is missing |
| modeled_availability_at | Close timestamp under explicit engineering bar-completion hypothesis |
| availability_basis | BAR_CLOSE_ENGINEERING_HYPOTHESIS_NOT_PROVIDER_RECEIPT |
| open / high / low / close / volume | Original numerical observations preserved; never rounded to force adjusted prices onto an executable tick grid |
| price_adjustment | UNADJUSTED, RATIO_ADJUSTED, ADDITIVE_ADJUSTED or UNRESOLVED |
| underlying_event_ids | Stable source-row identity; aggregation must union identities, never count labels as independent evidence |
| quality_flags | Explicit unresolved contract or quality metadata |

Normalization rejects malformed/nonfinite/inconsistent OHLC, invalid volume, duplicates, decreasing or off-minute timestamps, unknown timestamp labels, empty selected MNQ series, malformed source checksums and malformed explicit contract names. Unadjusted prices require the quarter-point grid. Ratio-adjusted prices preserve source decimals. Eastern DST folds and nonexistent local times fail closed rather than guess. No interpolation, silent sorting, deduplication, bar filling or prices correction occurs.

Quality inspection is permitted engineering validation. Normalization alone grants neither calibration eligibility nor execution authority. Dataset A remains unnormalized because its exact timestamp label and instrument binding are unresolved. Dataset B normalization is private engineering evidence only; empirical use remains blocked until file-specific research authorization and provenance are verified.
