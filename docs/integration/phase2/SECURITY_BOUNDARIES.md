# Phase 2 security and governance verification

Execution remains DENIED. Historical-authority vocabulary describes immutable
synthetic records only. No assessment is an executable approval.

- Unchanged Phase 1 proposal schema requires SYNTHETIC and exact false execution/
  live flags. Original nested assessments are checked with verifyJournal(); outer
  SQLite JSON CHECKs require false authority. Security tests cover stored, duplicate,
  conflict and replay paths and attempted SQL true-authority insertion.
- Runtime imports only SQLite, local filesystem/path, crypto and the existing pure
  protocol. It imports no broker, risk authorizer, order placer, Trading ledger,
  live-data client, HTTP library, child-process or model API. Tests assert that import
  boundary and absence of environment discovery/fetch/spawn in the durable runtime.
- All Node suites actively deny sockets/fetch/HTTP(S)/DNS. Existing Trading tests
  also pass under that guard. Test-only child processes run the same guard and
  operate solely on private temporary SQLite files.
- New database initialization is explicit/exclusive; parent must be private and
  non-symlink, database regular/private, no default app path. 0600 DB files under
  0700 directories isolate retained synthetic history. No .env, password, account
  session, API key, DATABASE_URL or production database is discovered or reused.
- Immediate transactions, primary/unique keys and atomic audit+claim commit prevent
  competing original decisions. Failures return no assessment. No map/cache/file-log
  fallback becomes authority after a database error.
- UPDATE/DELETE triggers protect originals/claims/migration metadata. Supersession
  is an append with a prior-assessment reference and a new identity. Replay uses
  separate records; no original row or trading control is updated.
- Source/schema/wrapper/runtime fingerprints and evidence inventory gate replay.
  Missing dependencies produce REPLAY_UNAVAILABLE. Corrupt/unwritable history cannot
  safely append a replay result; recorded:null makes that lack of confirmation explicit.
- Trading imports the same hash-pinned durable module and migration. Its separate
  durable API does not invoke the legacy Phase 1 memory supervisor on error.
- Existing Trading risk controls/IMAF entry locks, Sentinel ADR-037 Proposed and
  inference boundary remain unchanged. No deployment or production configuration
  was modified; existing unrelated Trading user changes were preserved.

The storage canonicalizer has larger envelope bounds to hold original canonical
wire and history; it does not broaden the Phase 1 wire contract. Expected-schema
comparison uses an ephemeral SQLite memory DB only for schema inventory; financial
or assessment authority never falls back there.

Threat-model limits: local filesystem/operator trust, not a signed external source;
a malicious administrator can replace a database and recompute an unsigned chain.
Read-time verification detects ordinary corruption/claim mismatches and trigger
changes, but there is no independent signed head, remote authentication, arbitrary
archived-code loader or OS-level hostile-plugin sandbox. A test network guard is
not an OS firewall. Physical disk/power and multi-host failover guarantees are not
claimed. These limits do not create an execution route.

Evidence: durable-security.test.mjs, durable.test.mjs, durable-cli.test.mjs,
Trading durable.test.mjs and adapter tests; exact outcomes in VALIDATION.md.
