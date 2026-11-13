# Sprint 21 runtime composition: implementation worklist

Independent source audit, 2026-11-12. This is an implementation recommendation,
not an acceptance record. ADR-037 remains Proposed; governed answering and the
proposition-to-inference boundary remain closed. No live migration, model call,
permission assignment, or production enablement was performed for this audit.

## Concrete missing boundaries

| Boundary | Current implementation | Work needed before a runtime acceptance candidate exists |
|---|---|---|
| Deployed request → current denial diagnostic | `app/main.py` registers `routes/governed_answers.py`; that route returns literal disabled responses with static blockers. `inspect_release_gate` is consumed by the separate unregistered isolated app. | Introduce a versioned current-readiness adapter on a separate review surface first. Bind the selected-model report through `evaluation/semantic_judge/astra_report.py`; keep the frozen route and historical inventory unchanged until a reviewed replacement contract exists. Missing, malformed, stale or unreadable evidence must still deny before retrieval/provider construction. |
| Authenticated operator → PostgreSQL grants | `isolated_sqlite_identity.py` verifies actual disposable credentials and grants. The proposed PostgreSQL `principals` table has ID/epoch/disabled fields, but no credential-verifier integration. | Specify the local authenticated proxy identity handoff and its trust boundary; implement an explicit PostgreSQL authority reader bound to principal ID, permission epoch and exact four-field scope. An organization parameter or matching vector payload cannot create a grant. Do not copy SQLite test passwords or infer grants from the legacy catalog. |
| Application lifecycle → authoritative catalog/outbox | `postgres_rehearsal.py` writes its own synthetic transactions. Application upload writes vectors before the legacy document row; archive/restore updates vectors separately from SQL. | Introduce an additive, reviewed application migration and transaction-owning writer. Inventory every create/retry/reindex/archive/restore/delete/scope-change/repair entry point; route each supported operation through expected-generation SQL transitions and an outbox. Unsupported writers must be explicitly denied for governed material. Preserve durable tombstones and immutable content versions. |
| Authoritative versions → actual Qdrant state | The proposal records manifests; legacy points lack governed content/lifecycle bindings. Reconciliation agreement is only migration-review readiness. | Implement a distinct governed index representation carrying document ID, exact scope, content/lifecycle epochs, manifest digest and locator. The reconciler must read back the complete ordered point set before acknowledging a current outbox operation. Late completions cannot make a newer or tombstoned version eligible. Never relabel legacy `status=indexed` as this proof. |
| Scoped retrieval → source bytes | Current retrieval uses the existing application index. SQL byte inspection is separate and explicitly not governed evidence. | Add a runtime reader that verifies each returned locator against the authoritative immutable version and manifest, including exact bytes/digests/lengths and scope. Exclude pending, archived, tombstoned, malformed and mismatched material. Recheck principal/catalog versions around every await and before exposing results. Document the publication barrier rather than claiming serial rechecks provide a transaction across external services. |
| Runtime context → selected provider roles | `OpenAIGovernedTransport` offers bounded untrusted structured Responses results. Offline coordinators explicitly require `execution_source=unit_test` and scripted fixtures. | Implement a new runtime/rehearsal coordinator with truthful provenance and separate interfaces for retrieval, generation, statement validation, relevance and presentation. Do not wrap the real transport in a `unit_test` label or loosen the frozen coordinator guard. Preserve one outer deadline, bounded budgets, cancellation and no retry/fallback/repair. Rejection must discard partial claims and citations. |
| Accepted candidate → rendered review output | The current frontend contract accepts only disabled envelopes; `governedAnswerApi.js` deliberately rejects unexpected successful responses. | Build a separately labeled inspection surface before changing that public contract. Bind exact question, full supplied context, candidate, citations, scopes, model/configuration, source/version digests and rendered output. Only then can the human inspect an actual runtime candidate. Stored-only media, sampled video text and OCR warnings must retain their extraction limitations in citations. |

## Two design decisions that block a direct reuse of the SQL rehearsal

The standalone PostgreSQL schema limits source bytes to **1 MiB**, chunk locators
to **0..31**, and each chunk to **64 KiB**. These are intentional rehearsal bounds,
not a storage plan for the actual corpus. The current intake accepts much larger
sources, and media extraction permits up to 8 MiB of extracted UTF-8 text. Applying
this DDL unchanged would reject legitimate large sources and manifests.

Before preparing an application migration, choose and document either immutable
content-addressed source storage with transactional references, or explicit SQL
byte budgets suitable for the reviewed corpus. Keep ordered manifest verification
bounded and paginated without silently truncating it. Define how retained PDF,
image, video and unsupported stored-only originals relate to versions and
extraction-policy identities. A source that has no searchable text must remain
ineligible for governed retrieval.

The measured Astra benchmark uses
`OpenAIReasoningAdmissibilityProvider` and `chat.completions.parse`. The selected
runtime transport uses `responses.parse`, including for the statement role.
Prompt/schema reuse and a shared model alias do not establish that the measured
wire path covers that runtime configuration. Either compose the exact measured
adapter with an appropriate bounded asynchronous boundary, or separately measure
the runtime statement path under a versioned protocol and submit its applicability
for review. Do not edit the frozen benchmark or claim the existing 108 calls
measured generation, relevance, retrieval, citations or the Responses path.

## Next bounded implementation

Prepare a **separate, disposable PostgreSQL plus Qdrant composition rehearsal**,
using synthetic sources and the proposed revised storage contract. Keep it
unregistered from `app/main.py`. Use dedicated database/collection identity
allowlists and reject the installed application database/collection. Its first
milestone should stop before provider dispatch:

1. Authenticate a disposable principal and capture an exact scoped permission
   epoch.
2. Commit immutable source/chunks, expected-generation identity and outbox in one
   actual PostgreSQL transaction.
3. Apply that outbox item to a disposable Qdrant collection; read back and verify
   its full ordered manifest, then acknowledge only the matching current version.
4. Retrieve a locator under scope filtering, resolve it to SQL-held authoritative
   bytes, and recheck permission/catalog versions.
5. Return an inspection envelope with `production_enabled=false`,
   `release_authorized=false`, and proposition-to-inference closed. Its output
   must not use the governed public-answer response contract.

After that milestone passes, compose local HTTP provider mocks through the real
SDK transport, then separately authorize and record actual selected-role calls.
Mocks prove serialization and control flow, not semantic accuracy. A paid model
call does not by itself establish independent validation or human acceptance.

## Required failure observations for that rehearsal

| Injected event | Required observable result |
|---|---|
| Catalog/outbox final insert fails | Neither identity/version/revision nor outbox advances. |
| Index write succeeds, acknowledgement transaction fails | No governed eligibility; retry is idempotent and re-verifies current version. |
| Old create finishes after archive, restore, scope move or tombstone | Old acknowledgement is stale; prior points cannot become eligible. |
| Point omitted, duplicated, wrong-order, wrong-byte, wrong-scope or wrong epoch | Source/index verification denies; no partial evidence or candidate escapes. |
| Permission rotation/revocation occurs during retrieval or any provider await | Remaining work is cancelled or discarded; no candidate/citations are returned. |
| Generation, judge or relevance refuses, times out, exceeds budget or returns malformed data | Terminal bounded denial; no fallback or partial answer. |
| Request question/context/source changes between validation and presentation | Context binding fails and the candidate is withheld. |
| Gate evidence is missing or changed | Denial occurs before retrieval and before any provider call. |
| Clean bounded inspection succeeds | All exact versions and provenance are recorded, but release/production authority remains false. |

## Human-only acceptance still needed

These cannot be supplied by code or an agent: final empirical acceptance of the
exact benchmark evidence; applicability and provider-independence review; review
of the final migration target and scope/principal mapping; inspection of the exact
rendered runtime question/context/candidate/citations; and explicit bound
production authorization. Completion of an isolated rehearsal does not substitute
for those decisions or mark Sprint 21 complete.

## Evidence scope of this audit

This review inspected the source modules named above, the standalone SQL DDL,
the selected model configuration, the versioned Astra adapter/report diagnostic,
and the current frontend answer parser. It identified missing integration and
capacity contracts; it did not perform a new PostgreSQL/Qdrant composition run.
Earlier SQL, authentication, transport, reconciliation, OCR and benchmark results
retain their original limited evidence scopes. No new runtime acceptance claim
is made here.

## Subsequent implementation checkpoint

The new `postgres_qdrant_rehearsal.py` executed against dedicated disposable
PostgreSQL 16 and Qdrant 1.18 services: 14 rollback/readback/scoped-byte-resolution,
mutation, revocation and late-completion checks passed; all owned test resources
were removed. It uses two tiny synthetic chunks and fixed four-dimensional
vectors. It does not authenticate an application principal or migrate the corpus.

`live_provider_rehearsal.py` now supplies a separate 44-call maximum selected-role
review harness with frozen input/review pins, structural checks, complete context,
truthful transport provenance, and durable private checkpoints before clients and
each dispatch. Its escaped HTML helper presents exact candidate wording and all
supplied sources/premises/relationships. The actual 44-call run completed after explicit owner-approved role assignment;
see [the preserved result](Sprint-21-Provider-Result-2026-11-12.md). One control
relevance disagreement and two withheld generated candidates await review.

`GET /governance/release-inspection` is an additive read-only workspace route. It
consumes the current denial diagnostic and independently validates the saved Astra
report; every production/acceptance authority flag remains false. The frozen
answer route, main-module bytes and historical answer packet remain unchanged.
This diagnostic does not implement an answer publication path.

The source storage v2 proposal and isolated content-addressed source primitive
address the large-original-file design gap without changing the v1 rehearsal
schema. The isolated chunk-object store now supports bounded strict UTF-8 publication
and verified reads (48 focused source/chunk tests passed). Versioned SQL references,
paginated manifests, application writers and the publication barrier remain work.

## November 13 team follow-up

See [the team checkpoint](Sprint-21-Team-Checkpoint-2026-11-13.md) for isolated
versioned SQL manifests, SDK inspection composition, PostgreSQL grant observations,
writer inventory and exact remaining application integration. These additions do
not replace the application lifecycle/outbox/publication work or owner acceptance.
