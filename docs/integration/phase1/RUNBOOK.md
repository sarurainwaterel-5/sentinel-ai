# Synthetic oversight Phase 1 runbook

For durable local history and offline replay use the additive
[Phase 2 runbook](../phase2/RUNBOOK.md). This page documents the separate original
in-memory API; it is never a fallback for Phase 2 database failures.

This is an in-process, read-only external-state harness, not a network service.
No credential, database, account session, broker, market feed or model is needed.
Requires Node 22+; dependencies are Node built-ins and the local schema.

## Run in Sentinel AI

From this repository root:

```sh
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/protocol.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/security.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/demo.mjs
```

Run Node test modules directly so the TAP output reports individual contract cases.
A `node --test` worker run can report one file aggregate rather than the intended
case counts on this runtime. Recorded counts below use the direct commands.

## Run across repositories

From the Trading AI repository root, replace `/absolute/path/sentinel-ai` with the
local reviewed Sentinel AI checkout (not its backend directory):

```sh
SENTINEL_SYNTHETIC_CONSUMER_ROOT=/absolute/path/sentinel-ai \
node --import /absolute/path/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs \
  services/synthetic-oversight/adapter.test.mjs
```

For programmatic use import `openSyntheticSupervisor` from Trading's adapter and
supply explicit `consumerRoot` and canonical UTC `evaluationTime`. This does not
read environment credentials or start a service. The only environment variable in
the test command selects a local checkout. Pin mismatch/missing files return
UNAVAILABLE and no fabricated assessment. Fix/review the local dependency before
retrying; never treat outage as compliance.

## Contract and assessment interpretation

- `syntheticProposal()` creates an explicitly synthetic, single-proposal fixture.
  `canonical()` serializes it; `assess(rawWire)` validates it before evaluation.
- The schema requires version, environment, event/proposal/correlation/account IDs,
  event type/revision, event and data timestamps, instrument, integer tick prices,
  quantity, risk/strategy metadata, hashed fixture evidence and false authority.
- `COMPLIANT` means this fixture meets the synthetic checks. `NON_COMPLIANT` means
  coherent input fails a fixture rule; `INSUFFICIENT_EVIDENCE` means absent references
  or stale data; `REVIEW_REQUIRED` covers unsupported fixture policies or simulated
  oversight outage. `OBSERVED` covers a valid withdrawal; `INVALID` covers schema,
  hash/reference, instrument, chronology or lifecycle errors.
- Every assessment includes ID, proposal/event IDs, version, supplied evaluation
  timestamp, result, verified evidence refs, governance checks, errors, correlation,
  fixture compliance domain, authority flags and chain binding. Invalid schema
  cannot establish a trusted identity; proposal/event/correlation are then null.
- Authorization is always DENIED; IMAF remains unresolved. No `allowed` or execution
  receipt field exists. Results cannot be submitted to the existing risk gateway.

## Audit and idempotency scope

The bounded journal and event/proposal maps live only in the harness instance.
This phase does not claim durable restart deduplication, distributed consensus,
service authentication or concurrent multi-process operation. Identical event+wire
returns the original record without adding a journal entry, even after withdrawal.
Conflicts are separately journaled INVALID attempts. Missing evidence can advance
an informational proposal revision; it never advances an execution state.

`journal()` returns copies; `verifyJournal()` verifies sequence, hashes, IDs and
false authority. This is self-consistency, not an authentic source or trusted
external head. Re-evaluating the same full input sequence with the same clock and
configuration reproduces identical records. Retain the head separately if later
building durable persistence; prefix truncation cannot be detected without an
external expected head. The test rejects removal of the first record or reordering,
not arbitrary loss of a valid trailing suffix.

At default 256 records (explicit maximum 4096), new attempts return
JOURNAL_CAPACITY_REACHED with no assessment and no overwrite; known duplicates
still return their original assessment. Create a separate test instance for a new
session. Do not discard state to bypass a real policy gate: no real policy gate is
connected here.

## Validation and boundaries

See [compatibility](CONTRACT_COMPATIBILITY.md), [executed results](VALIDATION.md),
[security](SECURITY_BOUNDARIES.md) and [next-phase readiness](READINESS.md).
No production route/configuration, old evaluator, Trading ledger, IMAF lock, risk
receipt, broker interface or account setting is changed. Do not use real proposals,
account files or TradingView exports in this synthetic protocol. Real export mapping
remains pending in the separate Sprint 22 workflow.
