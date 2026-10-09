# SentinelAI local release assessment

Reviewed 2026-10-08. Scope: a persistent installation on Rain's local computer, with one administrator login. Public publication was deferred at Rain's request.

## Analysis

The repository has a working React dashboard and implemented knowledge ingestion, retrieval, reasoning, planning, verification, and persistent reflection. The former README still described Sprint 6.4 despite Sprint 20.3 implementation. The project should be assessed against its current source and sprint records.

The governed proposition pipeline distinguishes untrusted candidates from accepted artifacts, reconstructs provenance, isolates providers, and fails closed on malformed inputs and gate failures. Its independent model gate has regression coverage, but actual judge accuracy is unmeasured. General semantic grounding, proposition-driven inference, autonomous execution, and public multi-tenant operation cannot be claimed complete.

## Release changes

- Package the browser, API, database, vector store and cached CPU embedding model with Docker Compose.
- Publish only the password-protected browser/API proxy on loopback. The API, PostgreSQL and Qdrant have no host ports in the complete local installation.
- Generate private local credentials without committing them. Caddy uses a password hash; see its [official hashing documentation](https://caddyserver.com/docs/command-line#caddy-hash-password).
- Persist PostgreSQL, Qdrant, original uploads and cognitive history in volumes. Seed constitutional memory only when its collection is empty.
- Share process configuration across the API and Alembic while preserving explicitly supplied migration-test URLs.
- Make all frontend workspaces use the configured API origin.
- Load and share one embedding model per process, bound CPU thread use and batch constitutional-memory embeddings. Real-model bulk/single embedding parity and 384-dimensional output were verified.
- Start the API without provider credentials, and give a clear 503 setup response for unavailable model features.
- Stream uploaded PDFs to unique server paths, reject unsafe filenames and oversized/non-PDF files, and remove failed or duplicate uploads.
- Mark vectors archived/restored and exclude archived vectors from retrieval.
- Add the document catalog migration missing from the original empty revision; validate duplicate prevention and preservation of pre-existing compatible tables.
- Correct the constitution build-info repository path, repair lint configuration, update vulnerable frontend dependencies, add readiness checks for storage connectivity and required tables, and add CI.

## Approval checkpoint

Recovered the exact approved blob and Git tree from the earlier Work environment. Both object hashes and commit hash matched the original commit; no attestations or case rationales were invented or changed. Pushed commit `213fb04125b189adc2fc770f157e4e454b559644` and fetched to verify matching remote HEAD. The repository approval validator accepts all 36 human labels with zero review blockers.

No semantic benchmark calls have been made. ADR-037 remains Proposed. PR #1 is unchanged.

## Verified checks

- Backend: **584 tests passed**; one Starlette/httpx deprecation warning.
- Frontend: **30 tests passed**, lint passed, production build passed.
- Frontend dependency audit: **zero reported vulnerabilities** after compatible lockfile updates.
- Python dependency consistency: `pip check` passed.
- PostgreSQL: three migrations applied to a real PostgreSQL 16 instance; Alembic reached `031_document_catalog`.
- Compose and CI YAML parsed; shell scripts passed syntax checks; `git diff --check` passed.

Packaged HTTP workflow verification passed through the password-protected browser origin: unauthenticated access rejected, administrator access accepted, live database/vector readiness, PDF indexing, duplicate detection, semantic search, archive exclusion, restoration, dashboard, and rejection of unsafe filenames. Bridge, Canon and Domains returned HTTP 200. Missing provider credentials produced the expected explicit 503. The synthetic verification PDF was left archived. The initial in-app automation rejected localhost. Subsequent headless Chromium checks completed actual browser navigation, connection inspection, planning submission, verification submission, and document restoration/archive with no client errors; desktop and compact layouts were visually inspected.

## Remaining acceptance work

The existing local application credentials successfully exercised Planning and Verification through both HTTP and browser workflows. Separate judge credentials, an explicit judge model and benchmark execution authorization are still required for the 108-call semantic evaluation. Never substitute regression results for empirical accuracy, weaken thresholds, or open proposition-driven inference on this release's evidence.

Intelligence, Governance, and Systems now have connected operator workflows. Bridge health observes storage instead of returning a fixed success. Constitutional coherence now fails closed as explicitly unassessed instead of returning an unearned perfect score. A verified constitutional assessor and semantic acceptance remain outstanding; storage readiness does not certify them. See [workspace implementation](product/WORKSPACE_COMPLETION.md). Public hosting remains a separate rollout with TLS, full API authentication, deployment credentials, backup/restore validation, operational monitoring, and appropriate account isolation.


## Workspace verification

The complete local workflow passed: PDF ingestion → factual Learning Events →
organization-scoped deterministic Reflection → immutable rejected outcome retained
in PostgreSQL. Actual model-backed Planning and Verification returned structured
results with separate unassessed constitutional judgment. Browser forms rendered
those results, and Governance restored/re-archived a synthetic document. All
synthetic workspace test documents remain archived; their history is retained in
a separate verification organization. No existing user document was changed.
