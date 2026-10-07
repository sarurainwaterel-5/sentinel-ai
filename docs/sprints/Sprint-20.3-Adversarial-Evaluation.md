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
