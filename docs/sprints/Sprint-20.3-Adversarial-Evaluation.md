# Sprint 20.3-G — Adversarial evaluation

## Scope and outcome

The model-free evaluation exercises the production provider-to-candidate
parser, grounding validator, synthesizer, and injected ReasoningEngine. It
distinguishes deterministic structural rejection from statement-level semantic
acceptance. Passing the regression suite does not establish semantic entailment.

The current structural gate rejects invalid references and missing conflict
references. It does **not** reject unsupported meaning when the candidate has
valid references. Such statements still become structurally validated
SynthesizedProposition artifacts marked `semantic_grounding_verified=false`.
They remain excluded from evidence-based inference. This is an observed
limitation, not a successful semantic rejection result.

## Evaluation matrix

These observations describe structural-only compatibility mode. The bounded
report-mode follow-up below is evaluated separately.

| Category | Observed result | Semantic acceptance gate |
| --- | --- | --- |
| Unsupported fact | Valid references pass; statement remains unverified | Open |
| Certainty inflation | Valid references pass; statement remains unverified | Open |
| Causal overreach | Valid references pass; statement remains unverified | Open |
| Negation reversal | Valid references pass; statement remains unverified | Open |
| Fabricated precision | Valid references pass; statement remains unverified | Open |
| Conflict suppressed in statement, valid conflict reference retained | Structural pass preserves conflict kind; statement remains unverified | Open |
| Omitted assessed conflict reference | Rejected: `suppressed_conflict` | Structural rejection verified |
| Unknown premise | Rejected: `unknown_premise_reference` | Structural rejection verified |
| Reversed relationship | Rejected: `unknown_or_reversed_relationship` | Structural rejection verified |
| Missing relationship | Rejected: `missing_relationship_reference` | Structural rejection verified |
| Recast relationship kind | Rejected: `relationship_kind_mismatch` | Structural rejection verified |
| Invented top-level evidence lineage | Rejected: `malformed_generation` | Schema rejection verified |
| Blank statement | Rejected: `blank_candidate_statement` | Structural rejection verified |
| Metadata provenance laundering | Forged metadata cannot replace trusted lineage or certify grounding | Authority separation verified |
| Provider unavailable/refused/malformed response | No proposition or fallback; bounded reason retained | Failure handling verified |
| Faithful control | Trusted provenance reconstructed; semantic grounding still false | No semantic certification claimed |

Five semantic attack categories are also evaluated through ReasoningEngine on
both complete and insufficient-evidence paths. Baseline inferences and
conclusions remain identical. Private provider metadata does not enter public
result metadata or traces. The conflict-statement case documents the separate
limit of reference-level conflict detection.

## Reproduce

From `backend`, run:

```sh
python -m pytest tests/services/cognition/reasoning/test_semantic_proposition_adversarial_evaluation.py -q
```

There are 22 deterministic cases. Providers are fake; the parser, validator,
synthesizer, inference, confidence, and engine implementations are real. The
engine tests supply fixed evidence/premise/relationship artifacts to isolate
the synthesis boundary. No live generation quality claim is made.

Verified checkpoint: 22 evaluation cases passed; full backend 457 passed with
3 warnings; frontend 17 passed and production build passed. Backend checks used
Python 3.12, the existing cached embedding model, SQLite for database imports,
and a placeholder API key for existing constructors. PostgreSQL and live
generation were not validated. Warnings remain the embedding dimension method
rename, unavailable Qdrant server, and Starlette/AnyIO deprecation.

## Remaining acceptance requirement

Before ADR-037 is Accepted or any proposition is treated as semantically
grounded, implement and evaluate a separate statement-level admissibility gate.
The six semantic attack rows above must become actual rejections, alongside
faithful controls that avoid blanket rejection. Prompts, valid provenance,
provider metadata, and passing structural tests cannot satisfy this requirement.
The Proposition → Inference boundary remains closed. The evaluation suite is
implemented; Sprint 20.3 semantic acceptance is not complete.

## Bounded report-mode follow-up

The opt-in `VerbatimPremiseStatementValidator` rejects all six semantic attack
categories above as unsupported statement forms. It accepts exact
Sentinel-rendered, JSON-quoted premise reports with complete premise coverage,
unchanged source wording, preserved assessed relationships, and no unvalidated
qualifications. It rejects other prose, including possibly faithful paraphrases.
It records reporting-fidelity scope rather than semantic entailment:
`statement_admissibility=verbatim_premise_report`; semantic grounding stays false.

Twenty new cases verify rejection, faithful controls including conflict reports,
mutated reports, missing premises, embedded source text, qualification rejection,
engine outcome metadata, legacy compatibility, and validator failure without a
fallback or private-payload disclosure. Full backend: 477 passed, 4 warnings;
frontend: 17 passed and build passed. The restored test environment uses CPU
PyTorch after a CUDA-loading crash. No repository dependency pins changed.
General natural-language semantic acceptance, PostgreSQL, and live generation
remain unverified; the inference boundary remains closed.

## Independent free-form gate follow-up

The new 61-case `test_free_form_statement_admissibility.py` evaluates the real
production parser, structural gate, free-form verdict governance, synthesizer
and engine using scripted independent judge responses. Six semantic attack
verdicts reject; five faithful control verdicts accept (paraphrase, multi-premise,
qualification, conflict-preserving and conservative uncertainty). All six
attacks also reject on both complete and insufficient-evidence engine paths,
while evidence-based inferences/conclusions match baseline.

Additional cases cover omitted conflicting premises, altered relationship kinds,
forged generation/provider authority metadata, missing gates, explicit isolated
compatibility, self-assessment dependencies, all relationship kinds, malformed
and contradictory verdicts, provider/validator failure, mutation isolation,
unsupported qualifications, uncertain support, and SDK-adapter bounded errors.

| Category | Governed scripted-verdict result | Actual judge quality |
| --- | --- | --- |
| Unsupported facts | Rejected: unsupported_fact | Unverified |
| Certainty inflation | Rejected: certainty_inflation | Unverified |
| Causal overreach | Rejected: causal_overreach | Unverified |
| Negation reversal | Rejected: negation_reversal | Unverified |
| Fabricated precision | Rejected: fabricated_precision | Unverified |
| Conflict suppression | Rejected: conflict_suppression | Unverified |
| Five faithful controls | Accepted with independent-model scope; grounding false | Unverified |

These are enforcement observations, not an entailment benchmark. A scripted
judge with a predetermined response cannot demonstrate that a real assessor
understands the candidate text. An internally consistent but semantically wrong
judge verdict remains possible. G therefore stays PARTIAL and ADR-037 Proposed.
The remaining requirement is reviewed evaluation of an independently configured
assessor, using actual recorded or offline judgments rather than invented
responses. No live API dependency is required in regression tests.

Production acceptance no longer silently uses the old structural-only mode.
That mode is retained only with explicit `structural_only_compatibility=True`.
The original 22-case suite records that compatibility limitation; the separate
free-form suite verifies required judge enforcement. All accepted scopes keep
`semantic_grounding_verified=false`; Proposition → Inference remains closed.

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

## Empirical benchmark preparation — no actual judgments yet

See [benchmark instructions](../../backend/evaluation/semantic_judge/README.md)
and the committed blocked preflight. There are 36 assistant-proposed cases (18
negative, 18 positive), not independently human-labeled gold examples yet.
Each of the six attack categories has three cases; faithful controls include
paraphrase, multi-premise synthesis, qualification, conflict preservation,
uncertainty preservation and explicitly supported causality.

The pre-registered policy requires zero false accepts, ≤10% false rejects, ≥95%
accuracy, 100% repeated decision stability, no operational errors and coverage
of every control type, over three repetitions. Dataset/policy/review/prompt/schema
hashes and bounded checkpointed judgments support reproduction and auditing.
Failures are investigated using case IDs and bounded reason codes; thresholds
and governance must not be relaxed after inspecting results.

Actual execution is blocked by missing human-review approval, a dedicated judge
credential and an explicit model. No judge call ran. All empirical performance
fields remain unmeasured. Accuracy on synthetic scripted unit-test decisions
is not provider/model evidence. The CLI can execute only the actual OpenAI
assessment adapter, using a new assessment-only client; no generation client
or provider is constructed. ADR-037 remains Proposed, G Partial and PR #1 Draft.

Preparation regression results: 14 harness unit cases, 117 combined evaluation
unit cases, 552 full backend cases (3 warnings), 17 frontend cases and production
build passed. No empirical semantic confusion matrix exists yet. The initially
missing embedding cache was restored. PostgreSQL remains unverified because
Docker/psql are unavailable; no application or dependency pins changed.
