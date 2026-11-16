# Phase 55B — independent verification

**RESEARCH ONLY — NOT APPROVED FOR EXECUTION.** Review date: 2026-11-16.

## Scope and evidence

The independent reviewer read the Phase 55B directive, inspected existing `services/return-calibration/engine.mjs` and `services/return-calibration/README.md`, reviewed the new historical loader, normalization, reconstruction, adapter and replay sources, and wrote separate adversarial test files. No broker service, order API, production configuration or raw dataset was modified.

Independent direct Parquet inspection confirmed Dataset A has 11,349 records, `ts: timestamp[ns, UTC]`, float64 OHLC, uint32 volume/trade count, and no intrinsic instrument or dated-contract column. Its observed coverage is 2026-11-01 23:00 UTC through 2026-11-12 04:08 UTC. This is a partial month, not full November coverage. ZIP inspection found 61 members and 4,319,380 declared uncompressed bytes. Its README declares ratio-adjusted continuous futures and US/Eastern bar-open timestamps. The first April 6 futures 1-minute member has 13,529 rows, including 1,380 MNQ rows. Provider declarations and intrinsic schema do not independently authenticate the observations or establish rights.

## Independent tests and review corrections

`services/historical-research/independent.test.mjs` contains 17 tests covering all three active mappings and 12 candidates, suspended 15-second exclusion, input-manifest self-authorization rejection, source/hash binding, adjusted/unknown-price rejection at the Phase 54 gate, unknown contract, off-grid unadjusted prices, OHLC/lineage tampering, missing/duplicate records, unknown availability, future window OHLC suppression and deterministic frozen output. A synthetic external-review fixture proves the permitted code path without claiming real provider authorization; downstream MSS stays unresolved and execution denied.

`services/historical-research/test_independent_inspection.py` contains 14 tests covering ZIP traversal/symlinks, DST ambiguous/nonexistent local times, Eastern conversion, MNQ filtering, duplicate/volume validation, adjusted precision preservation, unadjusted tick rejection, unknown availability, minute alignment, checksum syntax and absence of MNQ observations.

Independent inspection identified missing minute-alignment rejection, insufficient checksum syntax validation and empty-MNQ normalization behavior; the loader owner added checks. An initial independent test also incorrectly assumed a zero-count Counter field would be serialized and was corrected to accept its absence as zero. These earlier results are development feedback, not final passes. Final executed counts and exact commands are recorded below and in the implementation report.

## Verification limits

The injected attestation registry is an explicit local trust boundary, not a signature, provider-authenticated registry or production permission system. A caller controlling both data and registry can create research attestations; the supplied real inputs have no such verified entries. Replay hashes prove deterministic byte binding, not license authenticity or immutable production audit storage.

Reviewed session windows are explicit claims. IANA timezone handling verifies timestamp conversion, not exchange-calendar completeness. Unknown historical receipt times remain unknown; modeled bar-close availability must never be represented as observed receipt. Historical gaps are not automatically errors or nontrading intervals without a matching authoritative calendar. Neither adjusted series can be interpreted as dated-contract execution fills. Genuine calibration remains blocked; numerical limits remain pending.

## Final execution results

The independent JavaScript suite was rerun after the causal reconstruction correction: **17 passed, 0 failed, 0 skipped**, log `/tmp/phase55b-independent-final.tap`.

```bash
node --import '/home/rain/Documents/ChatGPT/Sentinel IR SRE/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs' services/historical-research/independent.test.mjs
```

The independent Python suite was rerun after loader fixes: **14 passed, 0 failed**, log `/tmp/phase55b-independent-python-final.tap`.

```bash
# Run from services/historical-research; temporary pyarrow dependency is outside the repository.
PYTHONPATH=/tmp/phase55b-python python3 -m unittest -v test_independent_inspection.py
```

These 31 independent cases are distinct from the implementation owners' suites. JavaScript ran with the existing deny-network preloader. Python tests use local/synthetic files and standard-library functions, with no provider requests. The complete baseline and implementation-suite counts belong to the main implementation report; they are not independently relabeled as these 31 cases.
