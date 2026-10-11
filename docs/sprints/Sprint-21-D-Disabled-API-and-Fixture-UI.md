# Sprint 21-D — Disabled API and inspectable fixture UI

## Boundary

GET `/cognition/answer/readiness` always reports disabled, false grounding and
closed proposition-to-inference, with explicit benchmark/answer release blockers.
POST `/cognition/answer` validates the strict request and returns an inspectable
GovernedAnswer with HTTP 503, null answer_text and no claims/evidence. It cannot
construct or call retrieval, generation, assessment, inference or the offline
coordinator. Environment/client enable switches cannot unlock it. Organization
scope other than the single local default is rejected with 403; malformed requests
use 422. Server-generated request/snapshot IDs do not certify cognition.

The routes are registered in the existing application. Authentication remains the
existing single-administrator Caddy proxy protecting all `/api/*` paths. The API
container remains unexposed by the persistent local compose configuration. No new
credentials, tenant authorization model or proxy exceptions are introduced. An
isolated unauthenticated test app verifies only disabled routes and has no storage
or provider composition; it is not a production deployment. Future release must
retain authenticated server-side scope resolution before any retrieval.

The frontend API client preserves expected structured 503 responses, rejects
unexpected success/unknown status/validation states, and checks captured request
scope. No caller automatically falls back to Recall or Reason. Reason shows a
readiness notice only; its existing submit behavior is unchanged. Readiness checks
abort on navigation, time out after ten seconds and allow explicit retry.

## Fixture inspector

GovernedAnswerPanel accepts explicitly unit_test, non-empirical fixture reports.
It is not mounted as a production answer entry point. It shows attributed preview,
claim validation, keyboard-accessible claim-to-source citations, source locator
and exact quote, conflicts and uncertainty separately. Production release remains
disabled and constitutional status is unassessed. Unsupported/unknown/mismatched
fixtures withhold their preview. React renders document/model text as escaped
text. Instance-specific citation targets prevent multiple reports from pointing
at each other's sources. The UI does not independently certify backend hashes or
semantic truth; its display of a scripted verdict is not release evidence.

## Verification story

Temporary localhost harness: availability notice → Vite proxy → isolated disabled
FastAPI router → readiness/structured 503 → client validation → disabled UI.
A separately generated synthetic 21-C fixture exercised the inspector. No private
PDFs, credentials, live model calls, database queries or deployment were needed.
Browser checks passed readiness, actual HTTP 503, null public answer/empty claims,
keyboard citations, source inspection, 1200/800/500px layouts and no page errors.
The temporary servers were stopped and preview files removed after verification.
The installed service at port 8080 was not rebuilt or restarted.

Backend isolated tests use asynchronous ASGITransport. The synchronous TestClient
harness stalled in this environment and was interrupted; async HTTP assertions
passed instead. Existing reasoning/benchmark enforcement tests remain offline;
they are not live semantic benchmark execution.

## Next gate

21-E requires an acceptance packet and separately authorized empirical 20.3-G
results/configuration plus explicit answer-presentation review. Missing acceptance
must keep production disabled. No ADR change, inference promotion, benchmark
execution, production credential introduction or deployment is authorized here.

## Validation results

- Reasoning plus disabled-route regression: 296 passed, with one existing offline
  Qdrant compatibility warning. Isolated async API assertions: 8 passed.
- Full frontend regression: 83 passed; final affected tests repeated after UI
  changes. Lint and production build passed.
- Browser harness: readiness disabled, POST 503 preserved, keyboard source target
  and quote inspection passed, no page errors or horizontal overflow at
  1200/800/500px. Fixture rendering is non-empirical; no live model was called.
- No change to ADR-037, benchmark artifacts, inference code or release thresholds.
