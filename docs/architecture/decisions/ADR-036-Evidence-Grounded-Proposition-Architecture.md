# ADR-036 — Evidence-Grounded Proposition Architecture

## Status

Accepted

## Context

SentinelAI's reasoning architecture originally operated primarily as:

```text
Evidence
    ↓
Inference
    ↓
Confidence
    ↓
Structured Conclusion

Sprint 20.1 introduced evidence-grounded premise extraction, giving Sentinel
an explicit representation of what individual pieces of evidence support.

That created a new architectural requirement.

Once premises exist as first-class cognitive artifacts, Sentinel must also be
able to represent how those premises relate before downstream inference occurs.

Without an explicit relationship and proposition layer, the reasoning engine
would still collapse multiple evidence-grounded claims directly into
inference.

That would create several problems:

relationships between premises would remain implicit;
support and conflict could not be inspected independently;
higher-order reasoning would lack a durable intermediate representation;
provenance could become difficult to preserve;
proposition generation and final inference could become conflated;
reasoning behavior would become harder to test in isolation.

Sentinel therefore requires an explicit cognitive layer between premises and
inference.

Decision

SentinelAI will use an evidence-grounded proposition architecture in which
reasoning progresses through explicit cognitive artifacts:

Evidence
    ↓
Premises
    ↓
Premise Relationships
    ↓
Synthesized Propositions
    ↓
Inference
    ↓
Confidence
    ↓
Structured Conclusion

Premise relationships and synthesized propositions are first-class reasoning
contracts.

They are not hidden implementation details.

Premise Relationships

Sentinel will represent relationships between premises using the canonical
relationship kinds:

SUPPORTS
CONFLICTS
COMPLEMENTS
INDEPENDENT
UNRESOLVED

A premise relationship is directional.

It identifies:

the source premise;
the target premise;
the relationship kind;
the basis for the relationship;
the confidence of the assessment.

A relationship assessment describes how two premises relate.

It does not create a new proposition.

Relationship Assessment

Premise relationships will be assessed by a dedicated reasoning service.

The architecture separates:

Semantic Evaluation
        ↓
Relationship Policy
        ↓
Canonical PremiseRelationship

This separation prevents semantic interpretation from becoming tightly coupled
to the domain model.

The semantic evaluator determines what relationship appears to exist.

The policy maps that semantic assessment into Sentinel's canonical reasoning
contract.

The PremiseRelationshipAssessor coordinates those responsibilities.

Pairwise Assessment

The reasoning engine will assess premises pairwise.

For a collection of premises:

P1
P2
P3

the engine may evaluate:

P1 → P2
P1 → P3
P2 → P3

This avoids hardcoding reasoning to exactly two premises and allows the
architecture to scale toward larger evidence sets.

Relationship assessment must remain bounded by available evidence and premise
content.

Synthesized Propositions

Sentinel will represent higher-order semantic synthesis using a dedicated
SynthesizedProposition model.

A synthesized proposition must preserve:

proposition identity;
proposition statement;
participating premise IDs;
upstream evidence IDs;
upstream domain IDs;
relevant relationship metadata.

The required provenance chain is:

Evidence
    ↓
Premise
    ↓
Premise Relationship
    ↓
Synthesized Proposition

A synthesized proposition must never become detached from the evidence that
ultimately produced it.

Separation From Inference

A synthesized proposition is not a final conclusion.

It is an intermediate cognitive artifact.

Its purpose is to express a higher-order statement that is supported by the
semantic relationship between multiple evidence-grounded premises.

The inference layer remains responsible for determining what conclusions can
reasonably be drawn from the available evidence and reasoning artifacts.

This preserves the separation:

Proposition Synthesis
        ≠
Inference
        ≠
Conclusion
Proposition Synthesis

PropositionSynthesizer is responsible for constructing synthesized
propositions.

It receives:

Premises
+
Premise Relationships

and may produce:

Synthesized Propositions

The synthesizer must not synthesize across relationships classified as:

INDEPENDENT
UNRESOLVED

Only meaningful semantic relationships may participate in higher-order
proposition construction.

The synthesizer must preserve complete evidence and domain provenance.

Semantic Proposition Generation

Generating the semantic statement of a synthesized proposition is a distinct
responsibility.

PropositionSynthesizer therefore accepts a semantic generator dependency.

The semantic generator is responsible only for generating the higher-order
statement from validated premises and relationships.

It must not:

invent unsupported claims;
produce final conclusions;
fabricate evidence;
erase provenance;
replace the inference engine;
exceed the semantic content of its inputs.
Default Engine Compatibility

A production semantic proposition generator does not yet exist.

Therefore ReasoningEngine will not instantiate
PropositionSynthesizer by default until a production-grade semantic
generator is available.

The current default behavior is:

self.propositions = None

When a proposition synthesizer is explicitly supplied, proposition synthesis
executes.

When no proposition synthesizer is supplied, the engine remains operational
and exposes:

synthesized_propositions = []

This is an intentional compatibility decision.

Sentinel will not introduce a placeholder or fake semantic generator merely to
complete the pipeline mechanically.

Reasoning Result Contract

ReasoningResult will expose intermediate reasoning artifacts including:

premises
premise_relationships
synthesized_propositions
inferences
conclusion
reasoning_trace

These artifacts are observable because Sentinel's cognition is intended to be
inspectable.

The system should expose how far reasoning progressed, not only the final
answer.

Insufficient-Evidence Semantics

Failure to produce an inference must not discard earlier reasoning artifacts.

If Sentinel successfully produces:

Evidence
Premises
Premise Relationships
Synthesized Propositions

but cannot produce a supported inference, the engine may return:

status = "insufficient_evidence"

while preserving all prior artifacts.

This allows the system to represent an epistemic boundary accurately.

Uncertainty Semantics

This architecture must preserve the existing distinction between:

Limitations

Constraints on what the current conclusion can support.

Missing Information

Evidence that is absent and would materially improve the judgment.

Confidence Uncertainty

Reasons confidence remains bounded.

Premise relationship assessment and proposition synthesis must not collapse
these concepts.

Consequences
Positive

The reasoning architecture becomes more inspectable.

Semantic relationships become explicit rather than implicit.

Higher-order reasoning gains a durable intermediate representation.

Evidence provenance is preserved through proposition synthesis.

Relationship assessment can be tested independently from proposition
generation.

Proposition synthesis can be tested independently from inference.

The reasoning engine becomes more structurally aligned with how Sentinel is
intended to reason.

Negative

The reasoning pipeline becomes more complex.

Additional domain models and services are required.

Pairwise relationship assessment may become computationally expensive as the
number of premises grows.

A production semantic proposition generator is still required before the full
pipeline can run automatically in the default engine.

Accepted Tradeoff

The additional complexity is intentional.

SentinelAI prioritizes inspectable, evidence-grounded cognition over a simpler
but opaque reasoning path.

Alternatives Considered
Direct Evidence-to-Inference

Rejected.

This approach leaves premise relationships implicit and provides no durable
representation of higher-order reasoning.

Merge Proposition Synthesis Into Inference

Rejected.

This would collapse two distinct cognitive responsibilities and make
provenance and testing less precise.

Generate Propositions Directly With an LLM

Rejected as the architectural contract.

An LLM may eventually implement the semantic generator, but proposition
generation must remain behind a governed interface with explicit inputs,
outputs, provenance, and validation.

Create a Placeholder Production Generator

Rejected.

A fake or weak default implementation would create the appearance of a
complete cognitive pipeline without providing trustworthy semantic behavior.

The dependency therefore remains optional until a production implementation
exists.

Implementation

The architecture is implemented through:

app/services/cognition/reasoning/models.py
app/services/cognition/reasoning/premise_relationship_assessor.py
app/services/cognition/reasoning/semantic_relationship_evaluator.py
app/services/cognition/reasoning/semantic_relationship_policy.py
app/services/cognition/reasoning/proposition_synthesizer.py
app/services/cognition/reasoning/reasoning_engine.py

Supporting tests include:

tests/services/cognition/reasoning/test_premise_relationship_models.py
tests/services/cognition/reasoning/test_premise_relationship_assessor.py
tests/services/cognition/reasoning/test_semantic_relationship_evaluator.py
tests/services/cognition/reasoning/test_semantic_relationship_policy.py
tests/services/cognition/reasoning/test_proposition_synthesis_models.py
tests/services/cognition/reasoning/test_proposition_synthesizer.py
tests/services/cognition/reasoning/test_reasoning_engine.py
Verification

At the completion of Sprint 20.2:

PYTHONPATH=. pytest -q \
  tests/services/cognition/reasoning

produced:

31 passed
Deferred Decision

A future architectural decision may define the production implementation of:

SemanticPropositionGenerator

That decision should address:

semantic generation mechanism;
grounding constraints;
deterministic validation;
model-provider boundaries;
hallucination resistance;
proposition evaluation;
failure behavior;
observability;
performance;
production dependency injection.

Until then, proposition generation remains an optional capability.

Final Principle

Sentinel must not jump directly from facts to conclusions when the reasoning
between them can be represented explicitly.

The architecture therefore preserves the chain:

Evidence
    ↓
Premise
    ↓
Relationship
    ↓
Proposition
    ↓
Inference
    ↓
Conclusion

Each transition is a cognitive responsibility.

Each artifact is inspectable.

Each claim remains grounded in provenance.
