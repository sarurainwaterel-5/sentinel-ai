# Sprint 21-L — Isolated in-memory lifecycle/outbox reconciliation simulator

Baseline: `3856a6e7826b30d16086ad3afdb5fc41404f4709`, branch `codex/sprint-21-b-contracts`.

## Contract inspection and compatible design

Repository HEAD/origin matched the supplied checkpoint and the checkout was clean. AGENTS.md, 21-J/K schema/planner, 21-G/H scope/catalog integration, 21-I identity, acceptance/readiness policy and legacy lifecycle/indexing source were inspected before implementation.

The concrete conflict is legacy `KnowledgeManagementService` updating vector payloads before relational status. This simulator models catalog ineligibility plus outbox insertion first, without modifying that service or claiming to repair its real consistency. The 21-K planner remains pending-only. This separate module exposes `fixture_eligible` only after explicit synthetic reconciliation; production/authentication/grounding/index-verification flags remain false. Existing 21-G content/index equality is preserved: index epoch is the last acknowledged content generation, not a dispatch counter. Restore/reindex can leave content/index numbers equal, but still require a new exact lifecycle/event/manifest receipt. No scope moves or grants are inferred.

## Explicit state and version bindings

`lifecycle_simulator.py` defines strict hash-only manifests, exact four-field scopes, stable document IDs, retained tombstones, catalog versions, outbox events, receipts, scope revisions and an ordered journal. No raw file/chunk contents or arbitrary metadata fields are accepted. There is no database, ORM, Alembic, route, startup, environment, discovery or service import.

Construct `LifecycleSimulator(state=..., expected_state_sha256=...)` from an explicitly supplied snapshot. `empty_state()` is an explicit synthetic genesis helper, never a fallback for missing/invalid snapshots. Restoration validates schema, closed authority flags, policy/version hash and external expected digest; it then replays the entire supplied journal from genesis and compares every derived document/event/scope/receipt row. Duplicate identities/events, orphan references, impossible generations, malformed manifests, unauthorized flags, altered receipts or mismatched journal/state are rejected. A malformed restored state leaves the simulator blocked, not reset to an empty state.

This stronger journal requirement deliberately rejects arbitrary pre-indexed catalog seeds without their simulated history. Snapshots are canonical ordered exports; journal order is semantic. Digests are not signatures: rewriting the whole consistent journal and replacing its trusted external anchor cannot be distinguished from another supplied fixture. The simulator cannot prove historical state outside the supplied trace.

Every mutating operation requires an exact current state SHA-256. Catalog commands additionally require the expected document digest (including all epochs/state/manifest) and exact scope revision. Dispatch/acknowledgement/reconciliation require the expected event digest. Identical previously accepted commands or receipts, and identical reconciliation operations, are idempotent no-ops; those do not mutate versions or journal and do not recertify old evidence. Conflicting duplicate IDs/receipts are rejected. Callers must execute serially; this class is not a thread-safe transaction engine.

## Lifecycle and simulated atomicity

Catalog commands are create, replace content, reindex, archive, restore and delete. Create starts lifecycle/content at 1, index at 0 and a pending index event. Every later accepted command advances lifecycle and scope revision; replacing content also advances content. Index epoch never regresses and advances to current content only on exact successful index reconciliation. Complete manifests require declared count and unique contiguous ordered chunk locators, digests and positive bounded lengths. Equal content across distinct IDs/scopes is allowed and never merges identity.

Each command constructs its catalog row, outbox event and journal entry in a private candidate state, validates/bounds it, and installs one serialized in-memory state only after success. Injected failure before that assignment leaves all three unchanged. Crash after assignment/before the caller receives the result permits identical command replay without a second event. This demonstrates in-memory all-or-nothing behavior, not a real database transaction.

Archive immediately enters archiving/ineligible and queues cleanup. Delete immediately retains a tombstone/ineligible and queues cleanup; the identity is never reused or restored. Successful cleanup settles archive to archived; delete remains tombstoned. Failure/uncertainty cannot make evidence eligible. Restore requires archived state, advances lifecycle, remains ineligible/restoring and queues a fresh index event. Failed indexing can receive an explicit new reindex/replace intent with a new generation; failed cleanup is not automatically repaired. Invalid state transitions deny rather than fallback.

## Dispatch, crash windows and reconciliation

There is one global simulated in-flight reservation across all documents: dispatched, recovery-ready or acknowledged work blocks another dispatch until reconciled. No transport, worker, callback execution, concurrency or automatic scheduler exists. Every dispatch is an explicit supplied operation. Dispatched/unacknowledged work must first receive an expected-version `recover` operation explicitly declaring the synthetic prior dispatch stopped; this records `replay_ready` while retaining the reservation. That declaration models a crash boundary, not proof of real transport cancellation. One subsequent explicit `replay=true` retains the same immutable event request identity. Direct concurrent redispatch, a third recorded dispatch, replay of failed/completed work or replay without matching versions is denied. Restart itself dispatches nothing.

A supplied receipt must bind event/document ID, exact scope, lifecycle/content/index target, ordered manifest and immutable request digest, with `execution_source=unit_test`. Missing/foreign/stale/unbound/malformed acknowledgements deny. Receipt success is stored first; acknowledgement alone does not grant fixture eligibility. Reconciliation checks the event is still the current document head with matching versions/manifest. Only a successful current index receipt makes the fixture indexed/eligible and advances scope revision. Failure/uncertainty settles indexing to failed/ineligible; failed archive cleanup stays archiving/ineligible.

Replacing/archiving/deleting during an old dispatch makes that event stale. Late completion is rejected. Explicit reconciliation marks obsolete work superseded and releases its local reservation without claiming vector cleanup or physical cancellation; new work must still be explicitly dispatched and acknowledged. An older already-stored acknowledgement cannot promote a newer catalog generation. Reordered operations, pending work without acknowledgement and stale expected versions cannot become eligible.

Simulated crash points are operation boundaries: before/after catalog commit, before/after dispatch, after acknowledgement and after reconciliation. A lost physical dispatch outside this state machine is not measurable; limits count recorded simulator dispatches, not real network attempts. The model cannot prove exactly-once remote effects, storage durability, fencing of a late vector write, index correctness, distributed atomicity, authorization or publish-time revocation.

## Bounds, reports and acceptance mapping

Policy-bound maxima are 16 identities/scopes, 64 events, 256 journal steps, 32 ordered chunks per manifest, two recorded dispatches per event and 512 KiB serialized state/operation. Shared bounded JSON validation adds depth/node/traversal budgets; not all independent maxima need be simultaneously admissible. No history, tombstone or evidence is silently dropped when limits are reached. Processing is deterministic and bounded by supplied state, not an empirical performance or operating-system memory guarantee.

Fresh reports/snapshots include deterministic state/policy/report hashes, bounded status/reason codes, fixture-eligible IDs and event counts. No raw fixture bytes, credentials or exception text are emitted. Rejected operations leave the previously valid state unchanged; they create no new eligibility. Invalid initial/restored state exposes no fallback eligible state. All reports/snapshots preserve `production_enabled=false`, `release_authorized=false`, `semantic_grounding_verified=false`, `authenticated_scope_verified=false`, `index_verified=false`, `execution_source=unit_test`, and proposition-to-inference closed.

| Milestone acceptance | Demonstration |
|---|---|
| Stable identity, scope and tombstone retention | Distinct scoped IDs with equal manifests; rejected moves; delete/recreate/restore denial |
| Monotonic versions and complete manifests | Expected state/document/event/scope hashes; content replace and archive/restore; malformed locator/count/hash denial |
| Catalog/outbox atomicity | Pre-commit injected failure; lost-response duplicate command after restart |
| Idempotent events and single flight | Duplicate commands/receipts/reconciliation are no-ops; conflicting duplicates and concurrent reservations deny |
| Exact completion and fail-closed eligibility | Wrong document/scope/versions/manifest/request, unknown outcome, failure and uncertainty tests |
| Crash/replay/reconciliation | Pending/dispatched/acknowledged/completed snapshots, explicit one-time replay, obsolete and late event denial |
| Supplied state validation and tampering | Anchored full-journal replay, duplicate/orphan rows, invalid generations/receipts/policy, forged flags and over-limit snapshots |
| No application authority or I/O | Closed flags, metadata injection denial, prohibited I/O entry-point tests, no runtime imports |

These tests are scripted state-machine and integrity evidence only; they are not empirical semantic accuracy or real index/authentication verification. Frozen acceptance thresholds, review records, inference/conclusion behavior and ADR-037 Proposed remain unchanged. Main and PR #1 are not modified.

## Remaining gaps and next bounded integration

Real principal/hash verification, catalog schema/migration authorization and deployment gating, lifecycle writer coverage, transactional storage/outbox adapters, verified backfill/index reconciliation, authenticated retrieval, independent real providers and operational budgets, publication consistency, empirical/final acceptance and runtime release-gate consumption remain outstanding. Simulator completion is not Sprint 21 completion.

Recommended smallest next integration: a read-only in-memory simulator snapshot to existing scope/catalog fixture adapter, with archive/delete/replace races against the offline coordinator. Prerequisites: validated externally anchored simulator snapshots, exact epoch/scope/manifest mappings, explicit synthetic principal grants and separately supplied byte fixtures checked against hashes. Do not import arbitrary legacy/backfill rows with silent epoch resets or treat fixture eligibility as real verification. No real storage work begins here.

## Final verification — 2026-10-16

Focused final run: **129 passed in 17.05s**. Relevant regression final run: **863 passed in 32.13s**, comprising the previous 734 tests and 129 new simulator cases. All four existing governance integrity inspectors returned valid with no errors; readiness remained blocked, production/release/semantic-grounding flags false and inference closed. ADR-037 remained Proposed. Whitespace checks passed before staging, with staged validation required before preservation. No pytest warnings were reported in final summaries. Sandbox shell startup intermittently emitted `Failed to create stream fd: Operation not permitted`; verification commands completed successfully. No live benchmark or database/migration tests ran.

Exact verification commands, run from `/home/rain/sentinel-ai`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_lifecycle_simulator.py
test ! -e /tmp/sentinel-21l-regression-20261016
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/sentinel-21l-regression-20261016 backend/tests/test_lifecycle_simulator.py backend/tests/test_backfill_planner.py backend/tests/test_identity_resolution.py backend/tests/test_scoped_async_coordinator.py backend/tests/test_scope_catalog_contracts.py backend/tests/test_answer_async_coordinator.py backend/tests/test_answer_provider_budget.py backend/tests/test_answer_evidence_scope_guard.py backend/tests/test_answer_presentation_inspector.py backend/tests/test_answer_presentation_guard.py backend/tests/test_answer_release_readiness.py backend/tests/test_answer_review_inspector.py backend/tests/test_answer_acceptance_packet.py backend/tests/test_governed_answer_routes.py backend/tests/services/cognition/reasoning/test_answer_contracts.py backend/tests/services/cognition/reasoning/test_answer_orchestrator.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -c 'import json; from evaluation.governed_answers.inspect_packet import inspect_packet, ROOT, PACKET; from evaluation.governed_answers.inspect_review import inspect_review; from evaluation.governed_answers.inspect_presentation import inspect_presentation; from evaluation.governed_answers.evaluate_readiness import evaluate_readiness; reports=[inspect_packet(ROOT,json.loads(PACKET.read_text())),inspect_review(ROOT),inspect_presentation(ROOT),evaluate_readiness(ROOT)]; result={"integrity":[r.get("packet_integrity",r.get("review_integrity",r.get("presentation_integrity",r.get("evidence_integrity")))) for r in reports],"errors":[r["errors"] for r in reports],"readiness":reports[-1]["readiness_status"],"production_enabled":reports[-1]["production_enabled"],"release_authorized":reports[-1]["release_authorized"],"semantic_grounding_verified":reports[-1]["semantic_grounding_verified"],"inference":reports[-1]["proposition_to_inference"]}; print(json.dumps(result)); assert result["integrity"] == ["valid"]*4 and not any(result["errors"]); assert result["readiness"] == "blocked" and result["production_enabled"] is result["release_authorized"] is result["semantic_grounding_verified"] is False and result["inference"] == "closed"'
git diff --check
git diff --cached --check
```

The temporary-directory absence check applied to this recorded run. A future rerun must choose a new absent directory rather than deleting unrelated artifacts. The integrity command imports only existing offline evaluators. Simulator and tests remain outside application runtime and migration discovery.
