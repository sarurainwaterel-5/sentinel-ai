# Durable strategy replay results

Executed: eight strategy durability cases, 29 prior durability cases, three prior
CLI cases, three Trading durable cases. New review archives exact historical
snapshot, original proposal, full specification text, evaluator/spec hashes,
evaluation cutoff/result and Node/ICU/timezone provenance in one original decision.
Duplicate same snapshot returns that result. Changed snapshot under the same ID
creates STRATEGY_SNAPSHOT_CONFLICT and cannot replace the original.

Separate process restart and replay return REPLAY_MATCH with byte-equivalent
canonical strategy assessment. New source-file future candles are ignored: replay
uses the archived cutoff/snapshot. Corruption fails closed. Changed dependencies
return REPLAY_UNAVAILABLE; deliberately inconsistent assessment returns
REPLAY_MISMATCH, appended separately without rewriting the decision.

Retained demonstration: workspace outputs/phase3-independent-imaf/demo/scenarios.json
and history.sqlite. Three synthetic decisions include bullish, bearish and false
platform displacement claim; last decision replayed after store reopen with MATCH.
The demonstration uses a controlled 2026-11-16 clock, not current market observations.

Compatibility limitation: modifying Phase 2 durable.mjs changes its dependency hash.
An untouched original Phase 2 demo DB was copied to legacy-phase2-copy.sqlite;
replay on the copy returned REPLAY_UNAVAILABLE, as intended for unavailable historical
dependencies. Original file SHA-256 remained unchanged (legacy-compatibility.json).
Historical evaluator retention/loading is not implemented as a version registry;
retain exact historical source/runtime artifacts for operational replay. Do not
reinterpret an unavailable replay as successful migration. No schema migration.
