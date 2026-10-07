# Sprint 20.3 — Governed Semantic Proposition Generation

## Status

A–F implemented and regression verified. G's adversarial suite is implemented;
the independent statement-level gate is implemented, but semantic assessor
accuracy remains unverified and acceptance remains open. ADR-037 remains
Proposed. Sprint semantic acceptance is not complete.

A bounded opt-in statement gate now accepts only exact Sentinel-rendered
verbatim premise reports. This closes rejection for unsupported statement forms
in that mode; arbitrary natural-language semantic grounding remains open.

## Sprint Intent

Build on ADR-036 and completed Sprint 20.2. Introduce semantic proposition
generation without granting a model authority to certify its own grounding.

> Semantic generation proposes meaning; Sentinel determines whether that
> meaning is admissible as an evidence-grounded proposition.

```text
Evidence → Premise → Relationship → Candidate Proposition
         → Grounding Validation → Synthesized Proposition
         → [future inference boundary]
```

The candidate is untrusted. Provenance references are validated and trusted
lineage is reconstructed by Sentinel. Attaching correct evidence IDs to an
unsupported statement is provenance laundering and must fail closed.

## Implementation sequence

### 20.3-A — Domain contracts

Keep `CandidateProposition` distinct from `SynthesizedProposition`. Replace
invented `relationship_ids` with `CandidateRelationshipReference` containing
source premise ID, target premise ID, and canonical relationship kind. Reject
malformed references. Do not let generator metadata redefine trusted basis,
confidence, or provenance.

### 20.3-B — Deterministic grounding validator

Validate premise and directional relationship membership and reconstruct
provenance from trusted inputs. Reject missing, conflicting, or inadmissible
references with inspectable bounded reasons. This deterministic gate does not
certify that an arbitrary natural-language statement is entailed by premises.
Semantic admissibility and statement-level validation remain required before
a synthesized proposition can be treated as semantically grounded or used
at the future inference boundary.

### 20.3-C — PropositionSynthesizer governance integration

Generate candidates, validate them, and construct accepted propositions from
trusted inputs only. Exclude `INDEPENDENT` and `UNRESOLVED`; preserve
`CONFLICTS` without recasting them as support. No rejection or provider
failure may produce a fallback proposition. A structural pass may produce a
proposition with Sentinel-owned provenance, but must explicitly report that
semantic grounding has not been verified. The synthesizer exposes bounded
rejection reasons. Statement-level semantic admissibility remains an open
gate and cannot be inferred from valid references alone.

### 20.3-D — Semantic generation provider boundary

Keep generation behind a provider-neutral interface with isolated provider
adapters and explicit error behavior. The narrow
`SemanticGenerationProvider` contract accepts Sentinel premise and relationship
artifacts and returns untrusted text plus observational metadata. Its bounded
failure reasons are unavailable, refused, and malformed response. It does not
parse a `CandidateProposition`; that translation belongs to the future
production `SemanticPropositionGenerator` in 20.3-E. No provider adapter or
model configuration is selected by this milestone.

### 20.3-E — Production semantic generator

Implement a production adapter that returns only untrusted candidates. Its
prompt or model configuration is not a substitute for grounding validation.

`ProviderSemanticPropositionGenerator` accepts an injected
`SemanticGenerationProvider` and parses one strict `CandidateProposition` JSON
object. It performs no response repair, markdown extraction, fallback, or
grounding decision. Providers receive deep copies of the trusted artifacts so
provider mutation cannot replace the lineage later validated by Sentinel.
Schema/JSON errors remain `malformed_generation`; provider failures retain
their bounded reasons, and an invalid provider response type yields
`provider_malformed_response`. Provider metadata is copied into the candidate's
untrusted `generator_metadata.provider_metadata` namespace. No vendor adapter,
model, credentials, or engine wiring is selected here.

Verification: 22 new generator cases and 71 targeted generator/provider/
governance cases passed. The initial embedding-dependency collection gap was
resolved by installing sentence-transformers and caching the existing
all-MiniLM-L6-v2 model in the execution environment. All 420 backend tests
passed before F implementation. No repository dependency pins were changed.

### 20.3-F — ReasoningEngine dependency injection

Inject governed synthesis without direct provider construction. Preserve the
existing evidence-based inference path and expose safe high-level trace and
result information without private chain-of-thought.

`ReasoningEngine(proposition_synthesizer=...)` now accepts governed synthesis
as an optional constructor dependency. The default remains disabled and does
not construct a model or provider. The engine consumes the inspectable synthesis
outcome, records bounded rejection reasons in result metadata, and reports
structural acceptance separately from semantic grounding in high-level traces.
Outcome metadata is retained for both complete and insufficient-evidence
results. Inference still receives only the original EvidenceBundle.

Verification: 15 new injection cases cover accepted candidates, malformed
generation, invalid references, bounded provider failures, unexpected errors,
private-payload exclusion, and default operation without credentials. Both
complete and insufficient-evidence paths preserve baseline inference and
conclusion behavior. All 435 backend tests passed after F; all 17 frontend
tests and the production build passed. Checks ran on Python 3.12 with SQLite
for database imports and a placeholder API key for existing constructors;
no live model generation was tested and PostgreSQL was not validated.
Semantic grounding remains false. Statement-level semantic acceptance and
ADR-037 implementation review remain outstanding.

### 20.3-G — Adversarial/evaluation suite

Test unsupported facts, certainty inflation, causal overreach, negation
reversal, conflict suppression, fabricated precision, invalid premise and
relationship references, provenance laundering, and provider failure.

The 22-case suite in `test_semantic_proposition_adversarial_evaluation.py`
exercises all listed categories through the production parser and governed
synthesis pipeline, including evidence-inference isolation on both engine
result paths. Structural attacks fail closed. Semantic attacks with valid
references currently pass the structural gate but remain explicitly unverified;
the suite records that limitation rather than claiming semantic rejection.
See [the evaluation matrix](Sprint-20.3-Adversarial-Evaluation.md).

The exact remaining acceptance work is a separate statement-level admissibility
gate with actual rejection of unsupported facts, certainty inflation, causal
overreach, negation reversal, fabricated precision, and statement-level conflict
suppression. Faithful controls must also be evaluated. ADR-037 remains Proposed
and propositions remain excluded from inference until those gates are satisfied.

### Bounded statement admissibility follow-up

`VerbatimPremiseStatementValidator` renders a JSON-quoted report of all supplied
participating premises and eligible assessed relationships. An exact statement
match, complete premise coverage, and no unvalidated qualifications are required.
Unsupported facts, inflated certainty, causal additions, negation reversal,
fabricated precision, and conflict suppression are rejected by the allowed-form
rule rather than an inferred understanding of arbitrary prose. Faithful exact
reports, including conflict reports, are positive controls. Paraphrases are
rejected even when they might be faithful.

Enable this gate explicitly through
`PropositionSynthesizer(semantic_generator=..., statement_validator=VerbatimPremiseStatementValidator())`.
Structural-only compatibility mode now requires the explicit
`structural_only_compatibility=True` option; omitting a validator otherwise
rejects with `statement_validator_required`. Gate rejection
or validator failure produces no fallback proposition. Accepted report metadata
records the bounded scope `statement_admissibility=verbatim_premise_report`;
`semantic_grounding_verified` remains false. Engine result metadata exposes the
scope and admissibility result without private validation payloads. Inference
continues to consume evidence only. This verifies reporting fidelity, not the
truth of sources or general semantic entailment; ADR-037 remains Proposed.

Verification: 20 new bounded-gate cases passed; 57 combined gate, evaluation,
and injection cases passed; full backend 477 passed with 4 warnings. Frontend
17 passed and production build passed. The restored Python 3.12 test environment
uses a CPU PyTorch build after the CUDA build crashed during collection; no
repository dependency pins changed. PostgreSQL and live generation remain
unverified. Warnings cover the embedding dimension rename, unavailable Qdrant,
Starlette/httpx deprecation, and the AnyIO portal alias.

## Definition of done

1. An explicit `SemanticPropositionGenerator` contract exists.
2. `CandidateProposition` remains distinct from `SynthesizedProposition`.
3. Candidates undergo inspectable grounding validation.
4. Invalid candidates fail closed.
5. Sentinel reconstructs trusted provenance.
6. Provider implementations remain isolated.
7. `PropositionSynthesizer` uses the governed pipeline.
8. `ReasoningEngine` supports dependency injection without provider coupling.
9. Existing inference remains backward compatible.
10. Proposition generation is observable through safe traces and results.
11. Adversarial provenance-laundering tests pass.
12. Full backend regression passes.
13. Frontend regression and build pass where available.
14. ADR-037 becomes Accepted only after implementation review.

## Non-goals

Proposition-driven inference; multi-hop inference; autonomous reasoning loops;
proposition persistence or memory; cross-session contradiction resolution;
CoherenceEngine redesign; autonomous agents; tool execution.

## Verification

Run targeted tests after each milestone, full backend regression at meaningful
checkpoints, and frontend tests/build for final review. Commit coherent green
milestones without weakening existing tests.

## Independent free-form statement gate follow-up

The provider-neutral `SemanticAdmissibilityProvider` accepts only semantic text
and assessed relationship data, never generator/provider metadata or provenance.
`FreeFormStatementAdmissibilityValidator` parses its untrusted strict JSON verdict
and reconciles an explicit admissible decision with all eight required checks
and bounded reason codes. Any defect, uncertain support, inconsistent verdict,
malformed response or provider error rejects. Structural and statement validator
exceptions now produce bounded rejection outcomes. Validators receive defensive
copies, so mutation cannot rewrite the candidate or trusted provenance.

Use `PropositionSynthesizer(semantic_generator=...,
statement_validator=FreeFormStatementAdmissibilityValidator(provider=...))`.
The SDK adapter `OpenAISemanticAdmissibilityProvider(client=..., model=...)`
lives outside cognition and requires separate explicit configuration. Reusing
generation's provider/client is rejected; wrappers and shared model behavior
still require independent deployment review. No live model call is needed for
regression tests, and no model/credentials are selected by ReasoningEngine.

Free-form scope is `independent_model_semantic_admissibility`. Exact reports
retain `verbatim_premise_report` scope. Structural-only compatibility is explicit
and labeled `structural_only_compatibility`; it has no statement decision. None
of these scopes changes `semantic_grounding_verified=false`. Inference still
receives EvidenceBundle only, and the Proposition → Inference boundary is closed.

### Final acceptance matrix for this follow-up

| Milestone | Status | Evidence / remaining requirement |
| --- | --- | --- |
| A | PASS | Untrusted candidate and distinct accepted artifact contracts |
| B | PASS | Deterministic membership and trusted provenance reconstruction |
| C | PASS | Mandatory default statement gate; explicit compatibility; fail-closed coordination |
| D | PASS | Provider-neutral generation contract |
| E | PASS | Strict production parser; no repair/fallback |
| F | PASS | Optional injection; evidence inference and conclusions unchanged |
| G | PARTIAL | Enforcement tests pass; actual independent assessor accuracy not evaluated |

| Definition of Done | Status | Evidence / remaining requirement |
| --- | --- | --- |
| 1. Generator contract | PASS | SemanticPropositionGenerator |
| 2. Distinct candidate | PASS | CandidateProposition / SynthesizedProposition |
| 3. Inspectable validation | PASS | Structural outcome plus bounded statement decision and scope |
| 4. Invalid candidates fail closed | PARTIAL | Schema/structural/judge/validator failures reject; actual semantic classification quality remains unverified |
| 5. Trusted provenance | PASS | Reconstructed exclusively from trusted inputs |
| 6. Provider isolation | PASS (Sprint scope) | New adapters outside cognition; pre-existing relationship evaluator/formatter SDK coupling unchanged |
| 7. Governed synthesis | PASS | Default requires both gates; compatibility explicitly identified |
| 8. Dependency injection | PASS | Engine constructs no generation/judge provider |
| 9. Inference compatibility | PASS | EvidenceBundle input and baseline conclusions preserved |
| 10. Safe observability | PARTIAL | Bounded judge reasons, no judge payload/chain-of-thought; free-form content safety depends on unverified semantic judgment |
| 11. Adversarial laundering | PARTIAL | Metadata cannot self-certify; scripted verdict enforcement passes, actual assessor decisions not benchmarked |
| 12. Full backend | PASS | Follow-up verification recorded below |
| 13. Frontend/build | PASS | Follow-up verification recorded below |
| 14. ADR accepted after review | OPEN | ADR-037 remains Proposed pending semantic evaluation |

The smallest remaining acceptance step is evaluation of the configured independent
assessor on all six attacks and the five faithful controls, with retained bounded
verdicts and reviewed expected labels. The current scripted fixtures test
governance, not natural-language classification. Do not mark G PASS or the PR
ready solely because those fixtures pass. No inference work is authorized.

## Follow-up verification (independent gate)

- New free-form gate tests: 61 passed.
- Gate + original adversarial + exact-report evaluation: 103 passed.
- Existing candidate/synthesizer/grounding/provider/generator/injection tests: 95 passed.
- Complete reasoning suite: 220 passed, 1 warning.
- Complete cognition suite: 538 passed, 3 warnings.
- Full backend: 538 passed, 4 warnings.
- Frontend: 17 passed; production build passed.
- `git diff --check`: passed.

Python 3.12, CPU PyTorch, cached existing embedding model, SQLite database imports
and a placeholder API key for existing constructors were used. No live
generation or judge call was made. Docker and psql executables are unavailable,
so PostgreSQL integration was not validated. Backend warnings remain the
embedding-dimension rename, unavailable Qdrant compatibility check,
Starlette/httpx deprecation and AnyIO BlockingPortal alias. npm additionally
warns about the execution environment's deprecated http-proxy configuration.
No dependency pins or inference implementation changed.
