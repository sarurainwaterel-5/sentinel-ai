# Sprint 21 current completion status — 2026-11-10

**Sprint remains open.** Implementation authorization is not a measurement,
independent semantic acceptance, migration approval on an exact final target,
or acceptance of unseen runtime answers. Production answering remains disabled;
ADR-037 stays Proposed and proposition-to-inference stays closed.

Baseline: `95523a4158e7d0dc012fa890c1472d1e2aae913f` (21-N), published and fetched
before this integration work. Three agents implemented storage, authority and
transport, and release evidence checks; root composed HTTP and operator rehearsals.
Independent reviews found malformed stored epochs/revisions and transport input
edge cases, which were corrected and tested before preservation.

## Completed in this integration checkpoint

| Work | Actual evidence and scope |
|---|---|
| SQL catalog/outbox | Durable SQLite file transactions, independent writers with expected-version checks, rollback of catalog/outbox together, retained tombstones, exact scope, bounded stored bytes, schema and corruption checks |
| Credential verification | Actual salted scrypt and constant-time hash comparison against disposable SQL principals/grants; versioned rotation/revocation; session ownership checks; no production credentials copied |
| Authenticated source inspection | Explicit isolated FastAPI factory → real credential/grant SQL store → hash-checked catalog/source bytes → authority/catalog recheck; lifecycle and permission races withhold the result |
| Provider transport | Explicit three-client/model OpenAI Responses adapter, bounded structured outputs, refusal/incomplete/timeout/malformed denial, no SDK retries or fallback; installed SDK exercised through local HTTP mocks |
| Current denial gate | Separate from frozen historical inventory; recomputes bound 108-trial report metrics, coverage, types, timestamps and hashes; an internally consistent report can qualify only for human review |
| PostgreSQL 16 | Actual disposable database schema/transactions/CAS/revocation/tombstone/late-event checks, plus logical artifact restoration with matching inventory hash |
| Application backup rehearsal | Read-only source inventory, private real relational backup, successful restore into a separate network-isolated PostgreSQL container, additive schema applied only to that clone; all legacy row counts/hashes preserved |

The API factory is not registered in the deployed application. Its source response
is explicitly inspection of pending bytes, not governed answer evidence or proof
of an actual vector index. Its answer path consumes the denial gate and returns
503 before catalog/provider work. Actual provider transports are deliberately not
relabeled as `unit_test` or fed into frozen offline coordinators.

The transport follows the [official structured-output API documentation](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
and [Python SDK reference](https://developers.openai.com/api/reference/python).
Different clients/model strings are configuration separation, not proof of
independence or semantic accuracy. Actual model compatibility remains unmeasured.

## Observed target and review artifacts

Observed application target: container `sentinel-local-postgres-1`, database
`sentinel_ai`, PostgreSQL `160014`, Alembic `032_teaching_missions`. The public
inventory had 76 documents, 8 teaching missions, 1 reflection-history row and
1 revision row. Its 76 catalog records cover 9 exact scopes, with no malformed
scope fields in that observation. Existing indexed statuses do not supply missing
governed epochs or complete ordered chunk manifests.

Local evidence is saved outside this Git checkout under the parent workspace's
`outputs/sprint21-integration/` directory:

- `postgres-rehearsal-report.json` and `postgres-logical-backup.json`: synthetic
  SQL transaction and exact logical backup/restore evidence.
- `application-restore-rehearsal.json`: observed source revision, private backup
  digest, proposal SQL digest, public row counts/hashes and preservation checks.
- `catalog-inventory-summary.json`: 76 records, 9 scopes, canonical inventory hash;
  source bytes/ordered manifests remain unverified and governed eligible count is 0.
- `provider-preflight.json`: reviewed labels accepted; zero API calls executed,
  null metrics, dedicated judge key/model configuration missing.

The `private/` subdirectory is mode 0700; the real database backup and catalog
metadata artifacts are mode 0600. They contain application data, stay outside Git,
and are not release artifacts. Relational backup alone does not capture uploads,
vectors, authentication configuration or external stores. Source inventory was
observed after the dump, not under a distributed snapshot. Both disposable
containers were removed after inspection; existing application services/data
were preserved.

The exact additive SQL artifact is
`docs/governance/isolated-postgres-catalog.sql`, SHA-256
`58948fc27bf237bd481369eaf1e8d151c5331ea70e95cc0340f72ab534baf51d`.
This was applied to a clone under `sentinel_catalog_proposal`, not registered in
Alembic and not applied to the application. See the
[storage plan](../governance/isolated-sqlite-storage-plan.md) and
[release integration audit](Sprint-21-Release-Integration-Audit.md).

## Still required before sprint acceptance

1. Dedicated explicit generation, judge and relevance/context deployments and
   secure credentials. The process currently lacks dedicated judge key/model;
   the general application key is not silently reused. The owner was asked for
   model choices and a secure configuration path; none has been supplied yet.
2. Exact source-byte and ordered index-manifest reconciliation for the 76 legacy
   documents, supported lifecycle-writer coverage, final scope/principal mapping,
   and reviewed application migration bindings. No historical epochs or grants
   may be inferred from legacy metadata.
3. Actual application PostgreSQL/catalog/index/retrieval/provider composition and
   deployed gate consumption, followed by real integration/race acceptance.
   Isolated SQLite inspection and PostgreSQL schema rehearsals do not satisfy it.
4. Execute the pre-registered independent 108-call benchmark using the existing
   approved 36-label record. Preserve failing measurements; do not weaken policy.
5. Governed runtime answer/question/full-context and citation results, human
   inspection of the exact rendered outputs, final empirical acceptance and
   explicit bound production authorization after review. Agents cannot sign these
   attestations on behalf of the reviewer.

## Validation

**1,098 tests passed** across separate runs: 975 existing regressions, 120 new
SQL/auth/HTTP/gate/transport tests, and 3 PostgreSQL rehearsal tests (including the
actual disposable server, not a skip). The final new suite passed in 32.28s;
existing regressions in 166.59s; PostgreSQL tests in 1.28s. All four historical
governance integrity inspectors returned valid with empty errors; readiness stayed
blocked and authority flags false. Unstaged/staged whitespace checks passed.

New checks, run from the repository with `PYTHONPATH=backend` and
`PYTHONDONTWRITEBYTECODE=1` using `/home/rain/sentinel-ai/backend/venv/bin/python`:

```sh
timeout 120 /home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_sqlite_catalog.py backend/tests/test_isolated_sqlite_identity.py backend/tests/test_isolated_acceptance_app.py backend/tests/test_runtime_release_gate.py backend/tests/test_openai_governed_transport.py
/home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_postgres_rehearsal.py
```

The PostgreSQL command requires an explicitly supplied
`SENTINEL_ISOLATED_POSTGRES_DSN` for database `sentinel_sprint21_rehearsal` on
PostgreSQL 16; it must never target application storage. Without it the actual
server test skips, which is not acceptance. The 975-test regression selection
is the 21-N selection plus its 64 principal-composition tests. No frontend files
were changed. No live model calls occurred. Initial SDK test platform discovery
was slow in the sandbox; the local mock test supplies a test-only SDK platform
value and final serialization/parsing checks pass. Shell startup intermittently
emitted its existing stream-fd warning; test summaries reported no warnings.
