# Sprint 22B implementation report

## Outcome and acceptance boundary

Sprint 22B adds a local, opt-in Companion compatibility layer, repository-grounded capability inspection and recommendation-only incident intelligence. It does not establish full live conversational acceptance. Conversation is a bounded deterministic record path with simple follow-up handling; live model inference, general natural-language reasoning quality and production integration remain unverified. No provider was called, no credential acquired, no installed service changed, no trading file modified and no push/merge/deployment performed.

## Verified baseline and discovery

Sentinel baseline: `3202bf7f2e02fe3b1e93f75ff5ec85873ab1219b`, initially clean; existing branch `codex/sprint-21-b-contracts`. Related Trading baseline: `4b11094033d8ab4a8c666a564851f50afc5a8ed3`; nine unrelated dirty files preserved by exact hash comparison. Prior 22A evidence recorded 2558 backend passes, 63 skips and 92 frontend passes. Current actual totals follow below.

Inspected 22A reports, registry/store, health engine, authentication/grants, 21-F asynchronous coordinator, provider-neutral contracts/transport, legacy retrieval/self-ontology, frontend Recall/Reason/layout and frozen release source manifest. The integration plan was written before code. Existing issued authentication, strict SRE evidence contracts, SQLite infrastructure and frontend layout were reused. Legacy source discovery imports main and legacy retrieval initializes external dependencies, so neither was invoked for repository inspection. No new dependency or autonomous runtime was installed.

## Implemented changes

- `backend/app/services/companion/`: versioned curated capability registry; bounded no-symlink hash/AST repository inspection; request-specific authorization; owner/scope conversation policy; private SQLite history, revision/idempotency controls, fixed retention, deletion and metadata audit chain; deterministic cited response renderer and future provider-neutral seam; opt-in authenticated FastAPI factory.
- `backend/app/services/sre/store.py`: additive atomic explicit incident/observation snapshot. Existing schema stays version 2. Health uses complete service evidence, not a selectively favorable subset.
- `backend/app/services/sre/investigation.py` and `investigation_verifier.py`: deterministic temporal/dependency correlation, supported competing hypotheses, independently defined structural verification, uncertainty, evidence inventory, cited findings and report hashes. Root cause always WITHHELD; no numerical confidence.
- `frontend/src/pages/Companion.jsx`, `services/companionApi.js`, styles and additive navigation: history/create/select/delete, tone, messages, sources, capability inspector, loading/errors/cancel and stale-response suppression. API configuration is explicitly opt-in; no browser credentials/history persistence. Existing infrastructure has no token stream, so final responses only.
- Focused conversation/self-knowledge/incident and frontend security/interaction tests; all eight requested documents plus integration plan.

Frozen `backend/app/main.py` and `frontend/src/pages/Reason.jsx` remain byte-identical to baseline. ADR-037 remains Proposed; proposition-to-inference boundary closed. Existing offline governed coordinator is not broadened to accept runtime prose. Logical roles are observer, investigator, verifier, architect, conversation renderer and authorization supervisor; no unrestricted agent framework.

## Verification

Final reviewed source results: **2648 backend tests passed, 63 skipped, 0 failed** (8 deprecation warnings; 155.45 seconds), **104 frontend tests passed across 14 files, 0 failed**, production frontend build passed locally to `/tmp/sentinel22b-final-build`, and targeted changed-file ESLint passed. The 90-case focused run is a subset of backend acceptance and is not added to these totals. The 63 skips are retained existing optional/integration boundaries, not successful live verification. Independent review confirmed all 19 source pins and found no remaining material authorization, ownership or citation defects after the two review fixes. Evidence is stored outside Git in `outputs/sprint22b-verification-20261116/`: offline runner, backend log/JUnit, frontend log, local build/lint logs and preservation hashes. The offline runner supplies synthetic configuration, disables dotenv/model downloads and denies internet socket connections. Tests exercise real private SQLite persistence/reopen and in-process ASGI authentication/requests; they do not use a live model or production service.

Earlier integration failures were corrected: single-use authentication session reuse, substring follow-up matching, and expected capability-count changes. Independent review also corrected cumulative request-body enforcement and repeated follow-up topic retention, with added regressions. Those failed runs remain in the private evidence directory. Interrupted runs are not accepted results, and overlapping focused tests are not added to full-suite totals.

## Limitations and deferred work

The opt-in API factory is not installed or mounted into the running application. A trusted local composition must supply its explicit catalog/session factory, exact scope, grants and private databases. A dedicated incident picker and conversational follow-up binding to reports remain for 22C; the investigation API already accepts explicit authorized selections. General model inference and fluency require an approved integration plus independent semantic evaluation. Provider objects are deliberately not invoked while generated prose remains withheld. Technical/friendly/direct tone configuration does not establish human-like identity or memory.

Cancellation and deadlines are cooperative stage boundaries. Browser abort withholds stale display but does not promise server rollback. Audit hashes do not resist a privileged filesystem owner or unanchored tail truncation. Expired conversations are withheld and purged on current-owner list/create; no background retention scheduler exists. Secret-pattern rejection is bounded, not perfect sensitive-prose classification. No persistent personal memory is written.

Recommended next sprint: 22C approved local composition, explicit incident picker/report-context integration, empirical model evaluation and governed acceptance; see SPRINT_22C_READINESS.md. No production or inference authorization is implied.

## Local commits

Baseline commit is recorded above. Implementation commit: `e265c9908c838cf9ef0f592c9cf133c453e3567a`. A subsequent documentation-only commit records this identifier; its final HEAD is recorded in the private verification receipt and final response. No push is authorized.
