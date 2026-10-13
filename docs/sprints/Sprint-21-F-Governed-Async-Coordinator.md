# Sprint 21-F — Governed Async Coordinator Integration

Baseline: `7ba9a2896620a48a807bea94f26f9d702afa45aa`, branch `codex/sprint-21-b-contracts`.

`backend/evaluation/governed_answers/async_coordinator.py` adds `OfflineAsyncAnswerCoordinator.evaluate_fixture`. It accepts explicit scripted generation, statement and relevance providers plus the existing fixture authority/catalog readers. It creates one fresh `OfflineProviderBudget` at request entry and awaits each stage sequentially. No routes, clients, credentials, retrieval, database, embeddings, inference or real-provider configuration are composed.

## Authoritative gates and request binding

The existing scope guard and synchronous coordinator perform preflight with a local capture-only generator returning no candidate. This captures complete validated premises and relationships without dispatching external work. Input models are deep-copied and canonically bound; permission/catalog snapshots, original inputs, and exposed provider/client identities are rechecked after every successful await and before finalization. Reusing the scope guard avoids duplicate provenance or authorization rules. Repeated preflight performs local validation only; it does not charge provider calls or create an answer.

Generation and assessment roles must be different objects with no shared exposed client, including relevance. Identity checks do not establish statistical independence, credential isolation, or detect concealed clients: these remain responsibilities of a future separately reviewed composition factory. Providers are trusted injected offline capabilities, not arbitrary code in a security sandbox.

The async generation response is replayed through the existing provider generator and synchronous structural gate. A capture-only statement adapter records the exact minimal request produced by the authoritative free-form validator and intentionally returns unavailable; this intermediate evaluation is discarded. Structural rejection prevents statement dispatch. The real scripted statement response is then replayed through the same validator. Negative or inconsistent verdicts withhold and prevent relevance dispatch.

The existing presentation snapshot function constructs relevance context from the validated synchronous evaluation. Cache-only generation, statement and relevance adapters reject changed requests and cannot call providers. Final scoped evaluation reruns the existing grounding, statement, coverage and deterministic rendering checks. The existing budget finalizer independently matches all three successful requests/responses to the final exact candidate/context and checks its deadline. No earlier partial fixture becomes an answer after an operational failure.

Frozen coordinator, renderer, contracts, presentation guard and governance files are unchanged. The companion imports their existing snapshot/canonical helpers rather than changing hash-bound files to expose new interfaces. Future helper changes must respect version bindings.

## Outcomes, budgets and cancellation

Success returns the existing immutable `BudgetedPresentation` with exact fixture text and citations. Public answer text remains null, public claims remain empty, production and release flags remain false, empirical acceptance remains false, and proposition-to-inference remains closed. Generator metadata is excluded from statement/relevance decisions and cannot certify authority.

The additional `async_coordinator` component report contains the sequential budget receipts and a bounded rejection reason. Missing, stale, malformed, mismatched, rejected, uncertain or expired stage evidence withholds the entire fixture. No provider exception text is exposed. Budget reason codes remain available in receipts; composition reasons include `async_preflight_rejected`, `async_structural_rejected`, `async_statement_rejected`, `async_receipt_unbound` and `async_context_or_composition_failure`.

The additive provider-budget finalizer also rechecks the deadline/clock after exact receipt and rendering validation, before sealing success. This closes expiry during final validation itself; tests cover expiry and a backward clock at that boundary.

One shared budget covers calls, canonical UTF-8 request/response bytes, per-call deadlines and an aggregate deadline beginning before preflight. Synchronous validation time is checked at subsequent dispatch/finalization, not forcibly interrupted. There are no retries, fallback providers, concurrent stage dispatch or hidden calls during replay. Each invocation gets a fresh budget even when the coordinator object is reused.

Caller cancellation propagates; the budget cancels and quarantines pending scripted work. Timeout or cancellation-resistant late results cannot reopen the abandoned session or produce an answer. Cooperative asyncio cancellation cannot forcibly stop blocking/native work or remote spending. Existing byte limits do not establish token, monetary cost, process memory, transport or fleet-wide concurrency limits.

## Validation and remaining release gates

Focused offline tests cover successful fresh composition and exact citations; all eight statement defects; negative, uncertain and unbound relevance; per-stage failures; shared counts/sizes/deadlines; permission/catalog/relationship preflight; shared provider/client rejection; mutated input/scope/catalog/client identities at every await; cache and receipt mismatch; expiry and catalog races at final display; caller cancellation and resistant late responses; and fresh budgets on reuse. Relevant Sprint 21 regressions and frozen integrity inspectors must pass before committing.

Fixture readers and assessed relationships remain supplied by callers. This is not authenticated retrieval, catalog transaction integration, relationship assessment or actual semantic/relevance accuracy evidence. Actual asynchronous provider composition, transport/token/cost/concurrency policies, complete relationship-assessment accounting, 20.3-G empirical and final acceptance, runtime release-gate consumption, production answer/citation acceptance and explicit production authorization remain blockers. No benchmark, live provider, credentials, route enablement, deployment, ADR-037 edit, frozen record edit or PR #1 merge is part of Sprint 21-F.

Validated 2026-10-12: **456 relevant offline tests passed**, including **76 new coordinator tests** and the previous 380 regressions. Packet, human review, offline presentation and readiness evidence integrity were valid with no errors. Readiness remained blocked; production and release authorization remained false. No empirical accuracy or production readiness is claimed.

## Offline hardening review — 2026-10-13

Review reproduced two gaps: missing or synchronous later-stage callbacks were discovered only after earlier provider work, and final relevance withholding collapsed its specific bounded reason to `presentation_already_withheld`. All three async capabilities are now checked before any dispatch and on identity rechecks. Final withholding retains the existing guard's bounded reason (including question-not-answered and uncertain), while discarding the entire answer and retaining disabled authority flags.

Eight regression cases reproduce and cover these behaviors. **464 relevant offline tests passed**, including 84 coordinator tests. Packet, review, presentation and readiness evidence integrity remained valid with no errors; readiness stayed blocked. No frozen source, governance record, route, benchmark, credential, storage or production configuration changed. Authenticated scope/catalog integration and the previously listed release gates remain outstanding.
