# Sprint 21-M — Read-only simulator/catalog fixture adapter

Baseline: `806c61368cdd6ec73753c72daa02956b08855bad`, branch
`codex/sprint-21-b-contracts`. The configured GitHub branch was fetched and
matched this baseline before implementation. Work uses a separate checkout in
the Sentinel IR SRE workspace; the original checkout is preserved.

## Scope and acceptance

This milestone bridges explicitly supplied synthetic lifecycle snapshots into
the existing offline scope/catalog contracts and scoped async coordinator.
It does not add application routes, storage adapters, migrations, workers,
retrieval clients or provider calls. The adapter does not mutate the simulator.

The source state must pass the existing externally anchored full-journal replay
validation. Catalog mappings preserve exact four-field scope, scope revision,
document identity, lifecycle/content/index epochs and ordered chunk hashes.
Non-indexed rows and retained tombstones remain visible to the eligibility guard.
Only reconciled fixture-eligible indexed documents can supply evidence.

`SimulatorCatalogAdapter` takes `state`, `expected_state_sha256`, a strict
`AuthoritySnapshot`, and a tuple of `DocumentByteFixture` records. It exposes
`authority_reader`, `catalog_reader`, `evidence(scope=..., document_ids=...)`,
`replace_snapshot(...)`, and a sanitized deterministic `report()`.

Full replay validates construction and every explicit replacement. Updates must
extend the entire previously accepted journal prefix; old or divergent histories
are rejected. An invalid update terminally blocks the adapter instead of serving
the previous eligible state. Identical snapshots are allowed. A new adapter still
depends on its caller's trusted external anchor; checksums are not signatures.

Each reader parses a detached copy of the retained canonical JSON and checks its
full digest plus external state anchor. Replaying the same validated history at
every checkpoint proved redundant and exhausted the coordinator's default
deadline in initial tests; installation validation plus immutable retained JSON
avoids that repeated work. The adapter is serial fixture code, not a thread-safe
reader or transaction engine.

Synthetic principal grants are supplied explicitly; document metadata does not
grant access. File bytes and every ordered chunk are supplied separately and
checked against the simulator manifest. This proves byte agreement within the
fixture, not that chunks were actually extracted from the supplied file or that
a real index contains them.

Evidence issuance checks all ordered chunks for each selected document, strict
UTF-8 decoding, exact byte lengths and hashes. Manifest matching occurs when
evidence is requested; catalog/report availability alone does not certify bytes.
Each file is at most 1 MiB, each chunk at most 64 KiB, with at most 32 chunks
per fixture, 16 fixture documents and 2 MiB of total supplied bytes. Evidence
is bounded to 25 chunks. Simulator bounds remain unchanged. Reports contain
state, authority, fixture-bundle, combined-input and report digests, with no raw
bytes, text, credentials or exception details.

The existing coordinator rechecks readers around each provider await and before
returning its offline result. Tests exercise lifecycle changes during those
awaits. These checkpoints detect observed changes; they are not a distributed
publication barrier or a guarantee about changes after the final check.

## Authority and remaining gaps

All results remain `execution_source=unit_test`; production, release, semantic
grounding, authenticated scope and real index verification remain false.
Proposition-to-inference remains closed. Synthetic checks do not establish
empirical semantic accuracy, production readiness or Sprint 21 completion.

Real identity/storage/retrieval/provider integration, migration authorization,
transactional outbox guarantees, index verification, publish-time consistency,
empirical acceptance and final release authorization remain outstanding.
ADR-037, frozen review records, thresholds, existing inference behavior, main
and PR #1 are outside this milestone.

Next candidate milestone: compose the existing offline principal-resolution
contracts with explicitly supplied authority snapshots and exercise permission
revocation races alongside lifecycle changes. Prerequisites are validated 21-I
synthetic principal fixtures, exact permission epochs and independently supplied
grants. This remains offline work; real authentication/storage integration needs
a separately bounded implementation and authorization.

## Validation

Independent implementation, test and review agents worked on this milestone.
Final review found no material correctness or security issues.

| Acceptance | Demonstration |
|---|---|
| Exact mapping | Four-field scope, scope revision, all epochs, file and ordered chunk digests preserved |
| Explicit synthetic authority | Missing grants and foreign scopes denied without inferring access |
| Byte binding | File/chunk hash, length, order, completeness and UTF-8 checks |
| Lifecycle invalidation | Archive/delete/replace/reindex during each of three provider awaits withholds output and stops further calls |
| No resurrection | Valid rollback/divergent journals rejected; invalid replacement terminally blocks readers even if caller catches the exception |
| Identity and ineligibility | Equal bytes retain distinct IDs; pending/failed/archived/tombstone rows remain visible but cannot supply evidence |
| Bounded inspectability | Fixture/selection limits and deterministic authority/byte/input/report digests, without raw fixture data |
| Existing governance | Four integrity inspectors and closed readiness/release flags remain required |

Final commands and results are recorded below. Commands run from this checkout;
the existing original repository virtualenv supplies dependencies. Tests import
the new checkout through `PYTHONPATH=backend`.

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_simulator_catalog_adapter.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/sentinel-21m-regression-20261110a backend/tests/test_lifecycle_simulator.py backend/tests/test_backfill_planner.py backend/tests/test_identity_resolution.py backend/tests/test_scoped_async_coordinator.py backend/tests/test_scope_catalog_contracts.py backend/tests/test_answer_async_coordinator.py backend/tests/test_answer_provider_budget.py backend/tests/test_answer_evidence_scope_guard.py backend/tests/test_answer_presentation_inspector.py backend/tests/test_answer_presentation_guard.py backend/tests/test_answer_release_readiness.py backend/tests/test_answer_review_inspector.py backend/tests/test_answer_acceptance_packet.py backend/tests/test_governed_answer_routes.py backend/tests/services/cognition/reasoning/test_answer_contracts.py backend/tests/services/cognition/reasoning/test_answer_orchestrator.py
git diff --check
git diff --cached --check
```

The previous milestone documents the unchanged four-inspector command. It was
executed here using the same existing virtualenv and this checkout's backend:
all four integrity values were `valid`, all error lists empty, readiness
`blocked`, production/release/semantic-grounding false and inference `closed`.

Final results on 2026-11-10: **48 new tests passed in 23.61s** and **863 existing
offline regression tests passed in 172.05s** (911 total). No pytest warnings were
reported. The shell intermittently emitted the existing `Failed to create stream
fd: Operation not permitted` startup message; validation commands completed.
Unstaged and staged whitespace checks passed. No live benchmark, database,
migration, deployment or production-enablement work ran.
