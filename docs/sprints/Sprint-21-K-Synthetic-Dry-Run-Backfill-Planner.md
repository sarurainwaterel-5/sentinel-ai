# Sprint 21-K — Isolated synthetic dry-run backfill planner

Baseline: `ff415b94232337782b018bcabffd39c9fc1b29ee`, branch `codex/sprint-21-b-contracts`. Scope: reviewed/reconstructed Sprint 21-J draft, pure planner, focused tests and this milestone record. No deployable revision, ORM metadata, startup migration gate, executor, worker, real adapter or authentication/public route wiring is introduced.

## Draft review findings

The named Sprint 21-J draft was absent from the clean checkout. Its absence was reported before reconstruction; `Sprint-21-J-Catalog-Schema-Migration-Gate-Draft.md` is explicitly a reconstruction from current requirements, not a recovered or approved original. The review separates identity from equal content, exact scope from grants, lifecycle from content/index generations, a retained tombstone from deletion of a row, and synthetic completion from actual index verification. It requires complete ordered manifests, transactional outbox/version acceptance, and migration authorization bound to target, artifact, inventory, backup, rehearsal and reconciliation evidence. Known prior source/chunk hashes cannot change at the same content epoch. No historical lifecycle guarantees are inferred when prior evidence is absent.

Existing Alembic source head is `032_teaching_missions`; no live revision was inspected. Docker startup runs Alembic head automatically. The draft remains under docs and no migration, model, Alembic environment or startup file was changed. `backend/backfill_documents.py` was inspected as text only: it performs discovery and database/client initialization at module scope and is explicitly not reused/imported.

## Planner interface and behavior

`evaluation.governed_answers.backfill_planner.plan_backfill` takes only explicitly supplied `records`, `mappings`, `file_fixtures` and `chunk_fixtures`, plus optional trusted expected input/policy digests. Top-level records/mappings/chunks are tuples of dictionaries; file fixtures are a dictionary of opaque safe fixture IDs to bytes or explicit missing values. Records use exact scope, stable document ID, current epochs/revision, optional prior floor/tombstone/content hashes, declared ordered chunk count/hashes, and optional explicitly synthetic index evidence.

The planner computes file digests from supplied original bytes and chunk digests from the supplied exact chunk bytes. It does not extract, decode, normalize, re-chunk, embed, search, inspect files, import storage/services or read settings/environment. It cannot establish that chunks were extracted from a real original or that a real index contains them. The synthetic manifest binds identity, exact scope, original file digest, content epoch, and ordered locator/hash/length rows. Synthetic index evidence must match that manifest and current lifecycle/content generations; actual-API markers or arbitrary verified/approval fields are rejected.

Dispositions:

- `pending_verification`: consistent supplied fixture data with complete matching synthetic index evidence. Planned state is pending, reason `real_index_verification_required`; never indexed or eligible.
- `quarantined`: malformed records, duplicate identity, missing/conflicting mapping, scope mismatch, incompatible identity/history, epoch regression, invalid/unavailable bytes, incomplete or mismatched chunks, noneligible legacy status, or missing/unverified/stale index evidence. Prior tombstones remain explicitly retained even when resurrection is quarantined.
- `retained_tombstone`: a consistent explicit tombstone with valid identity/scope/epochs. No file/chunk bytes are required; it does not authorize deletion or database mutation.

Malformed mapping/chunk ownership, orphan locators, malformed/oversized envelopes and mismatched expected digests block the whole plan. Per-record schema errors are quarantined with fixed codes and no validation payload echo. No record, mapping or chunk conflict is silently deduplicated. Equal bytes under distinct IDs/scopes remain separate rows with an equal-content count; no grant is inferred.

## Determinism, privacy and bounds

Top-level record/mapping/chunk order and dictionary key order are irrelevant. Nested record arrays accept equivalent JSON list/tuple forms. Chunk locators and the declared ordered hash array are semantic: exchanging bytes at two locators or changing the hash order changes/rejects the plan. Type-tagged byte/hash/length material prevents a supplied metadata object from masquerading as bytes in the canonical input binding.

Reports contain safe IDs/scopes, epochs, hashes, sizes, planned rows, bounded reasons and counts, canonical input SHA-256, fixed policy version/SHA-256 and plan SHA-256. No raw file/chunk contents, paths, credentials, arbitrary metadata or exception text are emitted. `verify_plan` recomputes the entire report from supplied inputs/current policy, detecting even a report whose attacker recomputes its own digest. Digests are not signatures or authorization; expected bindings must come from a trusted review to detect substitution of both inputs and plans.

Limits are part of the policy digest: 100 records, 200 mappings/file fixtures, 2048 chunk fixtures, 128 chunks per record, 1 MiB per file, 64 KiB per chunk, 4 MiB aggregate supplied bytes, 1 MiB normalized metadata/report, depth 12 and 30,000 visited nodes. Traversal also conservatively charges 32 bytes per node plus string/key UTF-8 bytes against a 1 MiB budget before serialization; independent maxima need not all be simultaneously admissible. Duplicate IDs quarantine before chunk expansion, preventing duplicate records from multiplying large manifests. Blocked envelopes contain no planned rows. Limits bound supplied fixture processing; this is not an empirical performance or operating-system memory guarantee.

Every output preserves `production_enabled=false`, `release_authorized=false`, `semantic_grounding_verified=false`, `authenticated_scope_verified=false`, `index_verified=false`, `dry_run=true`, `execution_source=unit_test` and proposition-to-inference closed. No existing inference/conclusion code, frozen human review/manifest/threshold, ADR-037, main or PR #1 changes.

## Validation record

Focused tests exercise deterministic proposals, permutation policy, byte/hash errors, exact scope/wildcards, duplicate identity/mappings, identical cross-scope copies, complete ordered manifests, unverified/stale index claims, tombstones/epochs/prior content, expected-input/policy/report tampering, authority bypasses, malformed/oversized data, bounded diagnostics and denied I/O/environment/service entry points. Relevant existing offline suites and governance inspectors must pass before preservation. These tests are synthetic policy/integrity evidence, not source truth or empirical semantic/index accuracy.

## Remaining blockers and next bounded milestone

The planner does not inspect live inventory, select/verify a real backup, rehearse migrations, approve a target, apply a backfill, reconcile live vectors or create lifecycle history. Actual principal transport/hash verification, transactional catalog adapters, lifecycle writer coverage, outbox reconciliation, real retrieval/providers, publication guarantees, empirical/final acceptance and explicit release authorization remain outstanding.

Recommended next milestone: an isolated in-memory lifecycle/outbox and reconciliation simulator with expected-generation acceptance and crash/reordering tests. Keep it outside ORM/Alembic registration, use supplied synthetic state only, and continue to prohibit real database work. No next milestone begins in this sequence.

## Final verification — 2026-10-15

Final focused run: **98 passed in 1.15s**. Final relevant regression run: **734 passed in 16.24s**, comprising the previous 636 regressions and 98 new planner cases. Packet, review, presentation and readiness evidence inspectors all returned valid, with no errors; readiness remained blocked, production/release/grounding flags false and inference closed. `git diff --check` and staged whitespace validation are required before preservation. No pytest warnings were reported in these final results; sandbox shell startup intermittently printed `Failed to create stream fd: Operation not permitted`, while the verification commands completed successfully. No empirical semantic/index evaluation or real migration occurred.

Exact verification commands, executed from `/home/rain/sentinel-ai`:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_backfill_planner.py
test ! -e /tmp/sentinel-21k-final-regression-20261015
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/sentinel-21k-final-regression-20261015 backend/tests/test_backfill_planner.py backend/tests/test_identity_resolution.py backend/tests/test_scoped_async_coordinator.py backend/tests/test_scope_catalog_contracts.py backend/tests/test_answer_async_coordinator.py backend/tests/test_answer_provider_budget.py backend/tests/test_answer_evidence_scope_guard.py backend/tests/test_answer_presentation_inspector.py backend/tests/test_answer_presentation_guard.py backend/tests/test_answer_release_readiness.py backend/tests/test_answer_review_inspector.py backend/tests/test_answer_acceptance_packet.py backend/tests/test_governed_answer_routes.py backend/tests/services/cognition/reasoning/test_answer_contracts.py backend/tests/services/cognition/reasoning/test_answer_orchestrator.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend backend/venv/bin/python -c 'import json; from evaluation.governed_answers.inspect_packet import inspect_packet, ROOT, PACKET; from evaluation.governed_answers.inspect_review import inspect_review; from evaluation.governed_answers.inspect_presentation import inspect_presentation; from evaluation.governed_answers.evaluate_readiness import evaluate_readiness; reports=[inspect_packet(ROOT,json.loads(PACKET.read_text())),inspect_review(ROOT),inspect_presentation(ROOT),evaluate_readiness(ROOT)]; result={"integrity":[r.get("packet_integrity",r.get("review_integrity",r.get("presentation_integrity",r.get("evidence_integrity")))) for r in reports],"errors":[r["errors"] for r in reports],"readiness":reports[-1]["readiness_status"],"production_enabled":reports[-1]["production_enabled"],"release_authorized":reports[-1]["release_authorized"],"semantic_grounding_verified":reports[-1]["semantic_grounding_verified"],"inference":reports[-1]["proposition_to_inference"]}; print(json.dumps(result)); assert result["integrity"] == ["valid"]*4 and not any(result["errors"]); assert result["readiness"] == "blocked" and result["production_enabled"] is result["release_authorized"] is result["semantic_grounding_verified"] is False and result["inference"] == "closed"'
git diff --check
git diff --cached --check
```

The temporary-directory precondition applied to this recorded run; for a later rerun choose a new absent directory rather than deleting unrelated test artifacts. The integrity command only imports existing offline inspectors. Database/migration test modules and application startup were not executed.
