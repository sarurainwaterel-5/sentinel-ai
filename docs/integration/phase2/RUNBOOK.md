# Durable synthetic oversight runbook

Run from Sentinel AI root with Node 22.22.1+ supporting node:sqlite. Tested SQLite
3.46.1; the binding emits an experimental warning on Node 22. No secret, network,
market service, TradingView session or production database is needed.

Create an owned private directory outside Git. Commands require explicit paths:

```sh
mkdir -m 700 /absolute/private/NEW-oversight-directory
node backend/evaluation/synthetic_oversight/durable-cli.mjs --command init \
  --db /absolute/private/NEW-oversight-directory/history.sqlite
```

Generate a canonical synthetic-only proposal using `canonical(syntheticProposal())`
from Phase 1 `protocol.mjs`; retain it in a local regular UTF-8 file without an
added trailing newline. Do not supply real proposals/account exports.

```sh
node backend/evaluation/synthetic_oversight/durable-cli.mjs --command submit \
  --db /absolute/private/NEW-oversight-directory/history.sqlite \
  --input /absolute/private/proposal.json --at 2026-11-15T12:00:00.000Z
```

Repeat the exact file to get DUPLICATE and the original assessment. A changed file
with the same proposal ID returns CONFLICT and no replacement assessment. For an
explicit correction use a new proposal/event ID, initial SUBMITTED revision 1 and
`--supersedes ORIGINAL_ASSESSMENT_ID`; it creates a separate linked record.

```sh
node backend/evaluation/synthetic_oversight/durable-cli.mjs --command replay \
  --db /absolute/private/NEW-oversight-directory/history.sqlite \
  --id ORIGINAL_ASSESSMENT_ID --at 2026-11-15T13:00:00.000Z
node backend/evaluation/synthetic_oversight/durable-cli.mjs --command history \
  --db /absolute/private/NEW-oversight-directory/history.sqlite
```

The example times are fixture times. Evaluation uses the original fixture clock;
replay uses --at only as the replay-observation timestamp. Replay MATCH requires
identical historical evaluator, schema, durable-wrapper hashes and Node version,
plus the original evidence inventory. Unknown/missing dependencies or evidence
return REPLAY_UNAVAILABLE; no current evaluator substitution occurs. This release
supports its current exact version, not arbitrary archived executable code. Restore
a reviewed historical bundle separately to replay a different historical version.

REPLAY_MISMATCH retains both the original and the reproduced informational result;
it cannot overwrite the original. Match/mismatch/unavailable outcomes are appended
as REPLAY rows when the database is trustworthy and writable. If database integrity
or availability prevents a replay transaction, return REPLAY_UNAVAILABLE with
recorded:null: persistence cannot be confirmed, and no fallback log/assessment is
invented. Verify/recover storage before retrying. Keep backups and trusted head
copies if operating beyond these disposable synthetic tests; no automated repair
or backup restoration is implemented here.

CLI success exit 0 means initialization, committed storage/original duplicate,
verified history or an exact replay match. Other results exit 2. It never indicates
trading authorization. SQL FULL/DELETE transactions protect process-crash recovery;
real power-loss/storage-hardware fault testing has not been performed.

## Integration entry points

In Trading AI's `services/synthetic-oversight/adapter.mjs`, explicitly call
`initializeDurableSupervisor({consumerRoot,databasePath})` for a new private database,
then `openDurableSupervisor(...)`. Both reuse pinned Sentinel code/migration.
Missing dependency or storage returns no store/assessment, never the Phase 1 memory
supervisor. Existing `openSyntheticSupervisor` remains an explicitly separate API.

## Executed tests / reproduce

```sh
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/durable.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/durable-security.test.mjs
node --import ./backend/evaluation/synthetic_oversight/deny-network.mjs backend/evaluation/synthetic_oversight/durable-cli.test.mjs
```

From Trading AI root, with the reviewed local Sentinel checkout:

```sh
SENTINEL_SYNTHETIC_CONSUMER_ROOT=/absolute/path/sentinel-ai \
node --import /absolute/path/sentinel-ai/backend/evaluation/synthetic_oversight/deny-network.mjs \
  services/synthetic-oversight/durable.test.mjs
```

The tests use actual temporary disk databases and independent child processes;
child results use private file IPC because piped subprocess stdout was not reliably
forwarded in the host test environment. The fault driver is test-only and is not
imported by runtime. No mock database underlies restart/concurrency claims.

See [validation](VALIDATION.md), [schema](SCHEMA_AND_MIGRATIONS.md),
[security](SECURITY_BOUNDARIES.md), [architecture](PERSISTENCE_ARCHITECTURE.md) and
[readiness](READINESS.md). Keep all runtime databases and outputs outside Git.
