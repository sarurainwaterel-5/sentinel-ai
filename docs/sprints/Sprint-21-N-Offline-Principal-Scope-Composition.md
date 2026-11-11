# Sprint 21-N — Offline principal/scope composition

Baseline: `236275095bf264b3661a26f12da83bae52881ee6`, branch
`codex/sprint-21-b-contracts`. Local and fetched remote matched before work;
the checkout was clean. Implementation, tests and independent review were split
across three agents in the Sentinel IR SRE workspace checkout.

## Bounded integration

This milestone composes the existing 21-I synthetic principal resolver with
the 21-H scoped async coordinator and the 21-M catalog fixture adapter.
Caller-selected identity and authority snapshots are not inputs to this new
composition. The principal's stable ID, exact permission epoch and complete
four-field grants come from the resolver's bound strict principal record.

All authorization headers and verifier behavior in tests are deliberately
synthetic. No existing administrator credentials, environment files, password
hashes, HTTP routes, sessions, database, vectors or real providers are accessed.
This is a fixture composition rather than application authentication.

The composed request has one deadline covering resolution, subsequent checks,
provider work and final return. Synchronous callbacks are checked before and
after work; this cannot forcibly interrupt a blocked callback. Existing provider
call and byte budgets apply. One resolution/verification attempt is allowed per
request, with no retry, fallback or re-verification to regain lost permission.

The principal is rechecked through the injected authority reader at existing
coordinator checkpoints. Catalog changes continue through the existing lifecycle
adapter. Observed authority or catalog changes withhold output. Rechecks remain
optimistic observations, not a real distributed publication barrier, immutable
authorization service, rate limiter or proof of real credential verification.

## Preserved boundaries

Production, release authorization, authenticated scope verification, semantic
grounding and empirical acceptance remain false. Proposition-to-inference stays
closed. ADR-037 remains Proposed; frozen review records, acceptance thresholds,
runtime behavior, main and PR #1 are unchanged.

Real principal/hash verification, storage/retrieval/provider integration,
transactional outbox guarantees, verified indexing, publish-time consistency,
empirical/final acceptance, runtime release-gate wiring and explicit production
authorization remain outstanding. This milestone does not complete Sprint 21.

## Verification

`OfflinePrincipalScopedCoordinator` accepts the three scripted provider roles,
`principal_reader`, `verifier`, `catalog_reader`, optional `limits` and `clock`.
Its `evaluate_fixture` accepts `authorization_values`, `scope`, `request_id`,
`question`, `evidence`, and `relationships`. A new resolver is created for each
invocation. A denied request cannot regain authority through access restoration;
a separate invocation is a new request and requires its own verification.

The authority reader derives `AuthoritySnapshot` only from the validated
resolver-owned context, not a second independently supplied grant snapshot. This
avoids conflicting authority inputs while retaining complete grant/epoch binding.
Scope and exposed constructor capabilities are bound throughout the request.
The outer deadline starts before resolver construction and is checked again
after the inner coordinator returns. Only principal-context and authority hashes
are added to component metadata; raw authorization values, principal JSON and
callback exception text are excluded. Failure drops partial component reports
and all answer/claim/preview fields. Caller cancellation propagates and no later
provider stage starts.

| Acceptance | Demonstration |
|---|---|
| Exact principal-derived authority | Stable ID, permission epoch and the complete grant tuple affect authority digest |
| Fail-closed resolution | Malformed/duplicate credentials, password rejection, disabled principals, revoked/foreign scope and malformed capabilities stop before provider work |
| Single verification | One verification on success; rechecks do not retry credentials |
| Live authority/lifecycle checks | Disable, revoke, credential rotation, permission epoch, principal ID, archive and simultaneous revocation/archive at every provider await |
| Capture races | Catalog callbacks changing grants/verifier policy and verifier callbacks changing principal state deny |
| Terminal denial | Restoring grants after observed inner denial cannot regain output at outer final checkpoint |
| Deadline and capability binding | Resolution/catalog/provider time counted together; invalid/backward clocks and swapped capabilities denied |
| Cancellation | Cancellation at all three stages propagates and prevents later work |
| Closed authority | Synthetic flags remain false, public answer fields remain empty and inference stays closed |

Independent review of implementation and adversarial tests found no material
correctness or security issues. Existing modules were not modified: this change
adds only the composition module, its tests and this document.

Commands run from the workspace checkout using the original dependency virtualenv:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider backend/tests/test_principal_scoped_coordinator.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=backend /home/rain/sentinel-ai/backend/venv/bin/python -m pytest -q -p no:cacheprovider --basetemp=/tmp/sentinel-21n-regression-20261110a backend/tests/test_simulator_catalog_adapter.py backend/tests/test_lifecycle_simulator.py backend/tests/test_backfill_planner.py backend/tests/test_identity_resolution.py backend/tests/test_scoped_async_coordinator.py backend/tests/test_scope_catalog_contracts.py backend/tests/test_answer_async_coordinator.py backend/tests/test_answer_provider_budget.py backend/tests/test_answer_evidence_scope_guard.py backend/tests/test_answer_presentation_inspector.py backend/tests/test_answer_presentation_guard.py backend/tests/test_answer_release_readiness.py backend/tests/test_answer_review_inspector.py backend/tests/test_answer_acceptance_packet.py backend/tests/test_governed_answer_routes.py backend/tests/services/cognition/reasoning/test_answer_contracts.py backend/tests/services/cognition/reasoning/test_answer_orchestrator.py
git diff --check
git diff --cached --check
```

The unchanged four-inspector command recorded in Sprint 21-L was also run with
this checkout's `PYTHONPATH=backend` and the dependency virtualenv above. Packet,
review, presentation and readiness integrity all returned `valid`; all error
lists were empty. Readiness remained `blocked`, production/release/semantic
grounding false and proposition-to-inference `closed`.

Final results on 2026-11-10: **64 new tests passed in 17.35s** and **911 existing
offline regression tests passed in 141.09s** (975 total). No pytest warnings were
reported. The shell intermittently emitted its existing `Failed to create stream
fd: Operation not permitted` startup message; validation completed normally.
Unstaged and staged whitespace checks passed. No live benchmark, storage work,
migration, deployment or production enablement was performed.
