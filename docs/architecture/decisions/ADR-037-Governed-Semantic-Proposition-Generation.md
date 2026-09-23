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
