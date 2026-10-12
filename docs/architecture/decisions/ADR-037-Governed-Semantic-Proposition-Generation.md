# ADR-037 — Governed Semantic Proposition Generation

## Status

Proposed. Accept only after Sprint 20.3 implementation review and verification.

## Context

ADR-036 and Sprint 20.2 introduced evidence-grounded premises, directional
relationships, and synthesized propositions. The existing synthesizer accepts a
semantic statement directly from an injected generator. Attaching premise and
evidence identifiers to that statement cannot establish that its meaning is
supported. A generated statement could acquire apparently valid provenance
while asserting an unsupported fact: provenance laundering.

## Decision

> Semantic generation proposes meaning; Sentinel determines whether that
> meaning is admissible as an evidence-grounded proposition.

The governed path is:

```text
Evidence → Premise → Relationship → Candidate Proposition
         → Grounding Validation → Synthesized Proposition
         → [future inference boundary]
```

`SemanticPropositionGenerator` returns an untrusted `CandidateProposition`,
never a `SynthesizedProposition`. Generation and acceptance are separate
cognitive responsibilities. `PropositionSynthesizer` coordinates generation,
validation, and promotion; it is not the semantic model. The generator does
not become the synthesizer.

The candidate may reference premises and relationships, but those references
are claims to check, not authority. Relationships have no synthetic IDs: a
candidate refers to each relationship structurally by source premise ID,
target premise ID, and canonical kind. Sentinel resolves references against
the assessed relationships and reconstructs trusted premise, evidence, domain,
and relationship provenance from validated inputs. A candidate cannot replace
the assessed relationship basis or confidence.

Grounding validation fails closed on missing or contradictory references,
unsupported additions, certainty inflation, causal overreach, negation
reversal, fabricated precision, or conflict suppression. It must evaluate the
candidate statement as well as its provenance. A validated reference list
alone is insufficient. `INDEPENDENT` and `UNRESOLVED` relationships do not
qualify for synthesis. `CONFLICTS` cannot silently become `SUPPORTS`.

During Sprint 20.3-C, a structural pass can be represented as a
`SynthesizedProposition` with an explicit `semantic_grounding_verified=false`
marker. This marker identifies the limit of that artifact: its provenance is
validated, but its arbitrary natural-language statement is not certified as
entailed. It must not be supplied to inference as grounded input. Acceptance
for semantic use requires the separate statement-level gate before the future
Proposition → Inference boundary is opened.

Provider implementations sit behind a provider-neutral generation boundary.
Provider or model errors yield no proposition; they never trigger fabricated
fallback content. `ReasoningEngine` accepts dependencies without constructing
a provider-specific model directly. Governance must rely on explicit
contracts and validation, not on prompt instructions alone.

Results and traces may expose high-level generation, rejection reasons, and
accepted artifacts for inspection. They must not expose private chain-of-thought.

## Compatibility and boundaries

Sprint 20.3 does not make `InferenceEngine` consume propositions. Existing
evidence-based inference continues unchanged. Proposition → Inference is a
future architectural decision. This ADR extends ADR-036's provenance
requirement with structural validation during Sprint 20.3-C and requires
statement-level validation before semantic grounding can be claimed.

## Consequences

The additional validation stage may reject plausible but unprovable semantic
synthesis. That is the intended safe outcome. A production generator must be
evaluated with adversarial cases; successful generation alone is not evidence
of grounded acceptance.

## Sprint 20.3-G evaluation finding

The deterministic adversarial suite confirms structural rejection and
evidence-inference isolation, but also demonstrates that unsupported facts,
certainty inflation, causal overreach, negation reversal, fabricated precision,
and statement-level conflict suppression can pass when their references are
valid. These artifacts remain explicitly semantically unverified. This is an
open acceptance requirement, not evidence that statement-level validation is
implemented. See the [evaluation matrix](../../sprints/Sprint-20.3-Adversarial-Evaluation.md).
This ADR remains Proposed pending that gate and implementation review.

The follow-up `VerbatimPremiseStatementValidator` provides an opt-in bounded
gate for exact Sentinel-rendered reports of trusted premises and relationships.
It rejects all other statement forms and unvalidated qualifications without
claiming general natural-language entailment. Its accepted scope is recorded
separately from `semantic_grounding_verified`, which remains false. Existing
structural-only mode is unchanged. This does not resolve the general semantic
acceptance requirement above or open the Proposition → Inference boundary.

## Independent free-form gate implementation review

`FreeFormStatementAdmissibilityValidator` now assesses free-form candidates via
a distinct `SemanticAdmissibilityProvider`, independent from generation and
structural provenance reconstruction. The request contains source statements,
assessed directional relationship kinds/bases, the candidate statement and its
qualifications; generator/provider metadata and evidence lineage are excluded.
The separately injected SDK adapter lives outside cognition. No credentials or
model are automatically selected. Reusing the generation provider object or its
client for assessment is rejected; deployment owners must additionally ensure
the assessor is independently configured rather than a wrapper around the
generator's own approval. Object separation cannot prove model independence.

The untrusted judge response must satisfy a strict bounded schema, explicitly
assessing unsupported facts, certainty inflation, causality, negation, precision,
conflict, qualifications and insufficient support. Missing/malformed or
contradictory verdicts, provider failures and validator exceptions reject without
fallback. Only a consistent admissible verdict can pass. Prompts instruct the
judge to preserve SUPPORTS/COMPLEMENTS/CONFLICTS semantics and reject uncertainty;
those instructions alone are not empirical evidence of semantic accuracy.

Synthesis now requires statement validation by default. The old structural-only
path requires `structural_only_compatibility=True`, cannot be combined with a
statement validator, and is labeled in inspectable outcomes and engine metadata.
The exact-report validator remains a distinct specialized fidelity gate.

The free-form scope is `independent_model_semantic_admissibility`, not proof of
entailment or source truth. `semantic_grounding_verified` remains false: a
governed probabilistic judgment with unmeasured semantic accuracy does not
justify general entailment certification. Proposition → Inference stays closed.
Future inference work MUST NOT treat these artifacts as semantically grounded
without a separate accepted architecture establishing that capability.

This implementation review leaves the ADR **Proposed**. Scripted independent
judge responses verify six attack rejections, faithful-control acceptance and
fail-closed integration, but do not evaluate an actual judge's decisions on those
texts. G's semantic acceptance requirement remains open until an independently
configured assessor is evaluated against reviewed attack/control fixtures. That
evaluation can use recorded independent assessments or an offline assessor;
regression tests need not call a live API. No further inference architecture is
required to perform it, and this finding does not weaken the decision above.

### Empirical evaluation preparation checkpoint

A [pre-registered benchmark and runner](../../../backend/evaluation/semantic_judge/README.md)
are prepared. The 36 labels remain assistant proposals pending independent human
review. Actual execution is blocked by missing review approval and dedicated
judge credential/model configuration. No actual judgment or accuracy measurement
has occurred. This preparation leaves this ADR Proposed and its semantic
acceptance requirement open; it does not change any architectural decision.
