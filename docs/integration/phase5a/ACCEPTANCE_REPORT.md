# Phase 5A — governed SRE / Companion acceptance checkpoint

Date: 2026-11-17 (America/Chicago).

**Decision: full Phase 5A acceptance is withheld.** The supplied directive stops at Guarantee A item 5, “No implicit administrator”. Remaining criteria were requested. This checkpoint validates the visible requirements and records observed workflow limitations; it does not assume or approve missing requirements.

## Baseline evidence

The clean starting checkout on `codex/sprint-21-b-contracts` was `fb275edc581504f45d0f85922f1e41fefcea105e`. Annotated tag `sentinel-phase4-validated` (tag object `6967960ef08232bf33d1c80baf03cb5975c3f22b`) peels to exactly that commit. The tag is preserved.

The existing `.local-validation/integration-regression.log` records **2711 passed, zero failures, zero skipped**, with eight warnings. Its SHA-256 is `fb1f116f0d2a00d7d3f8726f48c0eb38a0b2ec492215da2e6755c97720c11523`. `.local-validation/compose.yaml` specifies `postgres:16` and `qdrant/qdrant:v1.18.0`; SHA-256 `aca1eb52d094b722bf54a12a338fb83a7d865c86cc8bd44762b88c23819ec6f7`. These corroborate the supplied historical Phase 4 baseline. They are not a fresh integration-service rehearsal or a cryptographically bound execution receipt. No database/container/service was started, stopped or modified for this checkpoint. No credentials or environment files were read.

## Visible guarantees and results

| Guarantee | Assessment |
| --- | --- |
| Protected SRE data operations require authenticated principals | Exact issued handles, trusted catalog identity and current catalog rechecks enforced. Pure validation/health functions process supplied values and do not independently grant data access. |
| Tenant, application and evidence-scope separation | Explicit exact-match grants; no wildcard or administrator fallback. Companion adds endpoint-specific action grants and owner-scoped SQL keys. |
| Authorization before investigation publication | SRE checkpoint immediately before return; Companion API additionally rechecks investigate grant before returning. |
| Revoked/stale sessions denied | Existing epoch/disabled/scope/issuer tests plus added mid-retrieval revocation and unchanged-history/audit assertions. |
| No implicit administrator | No bypass or default supervisor grant found. Unknown principals and missing action grants are denied. This interprets only the visible fragment; the remainder may impose additional constraints. |
| Evidence and recommendations remain governed | Atomic snapshots, structural verification, source hashes, explicit uncertainty and withheld causal root cause. Generated model prose remains withheld. |
| Operational execution remains outside these pipelines | No remediation, deployment or broker execution path added; existing deny controls and closed release boundary preserved. |

Catalog validity checks are point-in-time. They do not prove linearizable publication against a concurrent external catalog mutation; the existing authentication contract explicitly reserves stronger publication barriers for SQL locking/composition.

## Minimal correction

Malformed Companion audit/record JSON and missing fields escaped as raw exceptions because transaction rollback rethrew all exception types. Five new regressions reproduced failures before correction. The transaction now preserves existing `SREError` and normalizes unexpected ordinary exceptions after rollback to bounded `SREError('CONVERSATION_OPERATION_FAILED')`. The API's existing generic error handler handles that failure. This changes error normalization only; grants, scopes, ownership, audit semantics, schema, operational execution and approval rules are unchanged.

The reviewed Companion store source hash is refreshed in the existing capability registry, and the registry's own hash pin is refreshed. No capability implementation or authorization status is promoted.

## Workflow and isolation limitations

1. **Recommendation → Audit → Human Approval is incomplete.** Investigations return a report digest and prior evidence audit head, but append no investigation/recommendation audit event or approval record. Existing tests expressly preserve read-only investigation semantics. Report discussion cannot approve execution. Full end-to-end workflow acceptance is withheld pending the remaining requirements and an explicit design for this missing state.
2. **HTTP disconnect cancellation is not propagated.** Python entrypoints check supplied cancellation/deadline callbacks; browser abort only suppresses stale UI and a submitted server turn may finish. This is documented existing behavior, not verified request-disconnect cancellation.
3. **Shared database corruption has shared availability impact.** Companion integrity checks cover all conversations and the global audit chain. An unrelated owner's corrupt row can block the shared store. Confidentiality fails closed, but tenant-level availability isolation is not established.
4. Live-model semantic quality, production transport/readiness and general architectural acceptance are outside the demonstrated offline results.

No authorization boundary was modified, production deployed, external service changed, operational remediation performed, tag moved, repository pushed or merge made.

## Verification evidence

The new authorization suite covers seven denied HTTP action grants, four capability-publication revocations, and turn-retrieval revocation with unchanged history/audit: **12 passed, zero failures/skips**. The failure-isolation suite covers malformed conversation/audit JSON, missing fields, write rollback, preserved domain errors and generic API responses: five pre-fix failures; final results are recorded in VERIFICATION_RESULTS.json.

**Final fresh relevant suite: 173 passed, zero failures, zero skipped (34.87 seconds).** All 19 source pins verify. This includes the 17 new cases; overlapping 12/17-case focused runs are not added to 173. An exploratory pre-correction run recorded the five corruption failures and one temporarily stale source pin; final verification supersedes that run. The full backend and live PostgreSQL/Qdrant suite were not rerun in this checkpoint. Relevant SRE/Companion regression results and source/log hashes are recorded in `VERIFICATION_RESULTS.json` and the private `outputs/phase5a-verification-20261117/` evidence directory. Counts from overlapping runs are not summed. Frontend source is unchanged. Historical Phase 4 integration success is kept separate from fresh offline validation.

## Next step

Obtain the missing portion of the Phase 5A directive, map each remaining guarantee to evidence/tests, and resolve the audit/approval acceptance gap without silently changing the existing read-only investigation contract. Production/service/remediation changes and authorization-boundary changes still require explicit owner approval.
