# Sprint 20.2 — Evidence-Grounded Proposition Reasoning

## Status

**Complete**

## Sprint Intent

Extend SentinelAI's evidence-grounded reasoning architecture beyond isolated
premise extraction.

Sprint 20.1 established the ability to derive explicit, inspectable premises
from evidence.

Sprint 20.2 establishes the next cognitive layer:

> Sentinel must be able to determine how evidence-grounded premises relate
> to one another and preserve the lineage required to synthesize higher-order
> propositions.

The purpose of this sprint is not to produce final conclusions.

It is to create the structural reasoning layer between evidence-grounded
premises and downstream inference.

---

## Architectural Context

Before this sprint, the active reasoning path was primarily:

```text
Evidence
    ↓
Inference
    ↓
Confidence
    ↓
Structured Conclusion

Premise extraction had been introduced as an explicit cognitive capability,
but premise relationships and proposition synthesis were not yet integrated
into the reasoning architecture.

This created an architectural gap.

Sentinel could identify evidence-grounded propositions, but the system did not
yet possess an explicit representation of:

how premises support one another;
how premises conflict;
how premises complement one another;
when premises are independent;
when a relationship remains unresolved;
which premises participate in a synthesized proposition;
which evidence remains upstream of that proposition.

Sprint 20.2 closes that gap.

The expanded cognitive path is:

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

This pipeline remains evidence-grounded and inspectable.

Core Principle

A synthesized proposition must never become detached from the evidence that
produced it.

The lineage is therefore:

Evidence
    ↓
Premise
    ↓
Premise Relationship
    ↓
Synthesized Proposition

A synthesized proposition is not a final conclusion.

It is a higher-order reasoning artifact derived from multiple
evidence-grounded premises whose semantic relationship has been explicitly
assessed.

Work Completed
1. Premise Relationship Model

Added explicit domain models for relationships between premises.

Canonical relationship kinds now include:

SUPPORTS
CONFLICTS
COMPLEMENTS
INDEPENDENT
UNRESOLVED

These relationships are directional and preserve the identities of both the
source and target premises.

A relationship records how two propositions relate without itself inventing
a new proposition.

2. Relationship Model Validation

Relationship models now enforce structural validity.

The model prevents malformed reasoning artifacts from silently entering the
cognitive pipeline.

Validation includes relationship integrity and guards against invalid premise
references or semantically incoherent relationship structures.

This continues SentinelAI's broader architectural principle:

Cognitive artifacts are contracts, not arbitrary dictionaries.

3. Semantic Relationship Policy

Added a semantic relationship policy responsible for translating semantic
assessment into canonical Sentinel relationship categories.

This separates:

semantic interpretation
        ↓
relationship policy
        ↓
canonical relationship model

The distinction prevents semantic evaluation logic from becoming coupled
directly to persistent reasoning contracts.

4. Semantic Premise Relationship Evaluation

Added semantic relationship evaluation as a dedicated cognition service.

Its responsibility is to assess the meaningful relationship between two
premises without creating a final conclusion.

This preserves separation of concerns between:

premise extraction;
relationship assessment;
proposition synthesis;
inference;
confidence;
conclusion.
5. Premise Relationship Assessor

Added PremiseRelationshipAssessor.

The assessor coordinates relationship evaluation between source and target
premises and produces canonical PremiseRelationship artifacts.

The reasoning engine can now examine multiple premises pairwise rather than
assuming that evidence-grounded premises exist independently.

6. Synthesized Proposition Model

Added a first-class SynthesizedProposition reasoning artifact.

A synthesized proposition preserves:

its own proposition identity;
the derived statement;
participating premise IDs;
upstream evidence IDs;
upstream domain IDs;
relationship metadata.

This allows higher-order reasoning to remain traceable all the way back to the
evidence layer.

7. Proposition Synthesizer

Added PropositionSynthesizer.

The synthesizer:

receives evidence-grounded premises;
receives explicit premise relationships;
ignores relationships that are independent or unresolved;
identifies participating premises;
delegates semantic statement generation;
preserves evidence and domain provenance;
emits a SynthesizedProposition.

The synthesizer does not produce a final answer or conclusion.

Reasoning Engine Integration

ReasoningEngine.reason() was expanded to expose the new reasoning artifacts.

The pipeline now performs:

Evidence Analysis
      ↓
Premise Extraction
      ↓
Pairwise Relationship Assessment
      ↓
Proposition Synthesis
      ↓
Inference
      ↓
Confidence
      ↓
Structured Conclusion

ReasoningResult can now expose:

premises
premise_relationships
synthesized_propositions
inferences
conclusion
reasoning_trace

This makes the intermediate cognition available for inspection rather than
hiding it behind the final answer.

Insufficient-Evidence Behavior

An important requirement was preserved during integration.

A failure to produce a downstream inference does not discard earlier
reasoning artifacts.

When inference cannot proceed, Sentinel may still return:

Evidence
Premises
Premise Relationships
Synthesized Propositions

with:

status = "insufficient_evidence"

This is intentional.

A reasoning system should be able to explain how far its cognition progressed
before reaching an epistemic boundary.

Uncertainty Semantics Preserved

Existing uncertainty semantics remain intact.

The architecture continues to distinguish:

Limitations

Constraints on the conclusion that can currently be formed.

Missing Information

Evidence that is absent and would materially improve the judgment.

Confidence Uncertainty

Reasons confidence remains bounded even when a conclusion can be produced.

The new premise and proposition layers do not collapse these concepts.

Compatibility Decision

PropositionSynthesizer requires a semantic proposition generator.

A production SemanticPropositionGenerator has not yet been implemented.

For that reason, the default ReasoningEngine currently treats proposition
synthesis as an optional production dependency.

self.propositions = None

When a proposition synthesizer is explicitly supplied, the full proposition
pipeline executes.

When one is not supplied, the engine remains operational and returns an empty
synthesized_propositions collection.

This preserves compatibility with existing reasoning behavior while avoiding
the introduction of a fake or placeholder production semantic generator.

Deferred Work
Semantic Proposition Generator

The next implementation step is a production-grade
SemanticPropositionGenerator.

Its responsibility will be narrowly defined:

Given multiple evidence-grounded premises and their validated semantic
relationships, generate a concise higher-order proposition without
introducing unsupported claims.

It must preserve the following constraints:

no unsupported semantic expansion;
no final conclusion generation;
no evidence fabrication;
no loss of provenance;
no replacement of the inference layer;
deterministic contracts around its inputs and outputs;
inspectable behavior suitable for evaluation.

Once implemented, PropositionSynthesizer can become a default production
dependency of ReasoningEngine.

Files Added
Reasoning Services
app/services/cognition/reasoning/premise_relationship_assessor.py
app/services/cognition/reasoning/proposition_synthesizer.py
app/services/cognition/reasoning/semantic_relationship_evaluator.py
app/services/cognition/reasoning/semantic_relationship_policy.py
Tests
tests/services/cognition/reasoning/test_premise_relationship_assessor.py
tests/services/cognition/reasoning/test_premise_relationship_models.py
tests/services/cognition/reasoning/test_proposition_synthesis_models.py
tests/services/cognition/reasoning/test_proposition_synthesizer.py
tests/services/cognition/reasoning/test_reasoning_engine.py
tests/services/cognition/reasoning/test_semantic_relationship_evaluator.py
tests/services/cognition/reasoning/test_semantic_relationship_policy.py
Files Modified
app/services/cognition/reasoning/models.py
app/services/cognition/reasoning/reasoning_engine.py
Verification

The reasoning test suite was executed with:

PYTHONPATH=. pytest -q \
  tests/services/cognition/reasoning

Final result:

31 passed

The completed suite verifies:

premise relationship contracts;
relationship model validation;
semantic relationship policy behavior;
semantic relationship evaluation;
premise relationship assessment;
synthesized proposition contracts;
proposition provenance;
proposition synthesis behavior;
reasoning-engine pipeline exposure;
insufficient-evidence behavior;
uncertainty semantic separation;
compatibility with existing reasoning behavior.
Architectural Result

Sentinel's reasoning architecture has moved from reasoning over evidence as an
undifferentiated collection toward reasoning over explicit cognitive objects.

The distinction is important.

Before:

Evidence → Inference

Now:

Evidence
    ↓
Premise
    ↓
Relationship
    ↓
Proposition
    ↓
Inference

Each stage has a different responsibility.

Each stage can be inspected.

Each stage preserves provenance.

Each stage can be independently tested.

This increases Sentinel's ability to reason without turning the reasoning
engine into an opaque monolith.

Sprint Boundary

Sprint 20.2 ends with:

explicit premise relationship contracts;
semantic relationship classification;
pairwise relationship assessment;
evidence-grounded proposition contracts;
proposition synthesis with provenance;
reasoning-engine exposure of premise reasoning artifacts;
preserved insufficient-evidence semantics;
preserved uncertainty semantics;
31 passing reasoning tests.

Production semantic proposition generation is intentionally deferred.

That work begins beyond this sprint boundary.

Sprint Outcome

Sprint 20.2 — Complete

Sentinel can now represent not only what the evidence says, but how
evidence-grounded propositions relate.

The next cognitive threshold is teaching Sentinel to generate higher-order
semantic propositions from those relationships without exceeding the evidence.
