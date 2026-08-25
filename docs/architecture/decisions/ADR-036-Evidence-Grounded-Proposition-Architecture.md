# ADR-036 — Evidence-Grounded Proposition Architecture

## Status

Accepted

## Date


The architecture therefore requires an explicit evidence-grounded
proposition layer.

Decision

SentinelAI SHALL represent atomic evidence-grounded propositions as
Premises before higher-order proposition synthesis occurs.

The accepted architectural direction is:

Retrieval
   ↓
Evidence Analysis
   ↓
Premise Extraction
   ↓
Atomic Premises
   ↓
Premise Relationship Assessment
   ↓
Proposition Synthesis
   ↓
Candidate Inference
   ↓
Confidence Assessment
   ↓
Supported Conclusion
   ↓
Constitutional Coherence

Not every stage must be implemented simultaneously.

The architectural boundaries SHALL nevertheless remain explicit as the
reasoning faculty evolves.

Decision Principles
1. Evidence Is Not a Proposition

Retrieved evidence represents source material available to reasoning.

A Premise represents an explicit proposition derived from usable
evidence.

The architecture SHALL NOT assume:

Retrieved Chunk
      =
Reasoning Proposition
2. Every Evidence-Grounded Premise Requires Provenance

An evidence-grounded Premise SHALL preserve explicit lineage to the
evidence from which it was derived.

A Premise without evidence lineage SHALL NOT be represented as an
evidence-grounded proposition.

3. Retrieval Does Not Grant Reasoning Authority

Information does not become a Premise merely because retrieval returned
it.

Unknown or unusable evidence SHALL NOT be silently promoted into the
proposition layer.

4. Extraction Is Not Synthesis

Premise extraction may perform deterministic normalization and exact
proposition consolidation.

It SHALL NOT:

manufacture conclusions,
infer unstated claims,
resolve contradictions,
perform semantic composition,
or strengthen a proposition beyond its evidence.
5. Repeated Evidence Is Not Repeated Proposition Identity

Multiple evidence items may support the same proposition.

When exact-equivalent propositions are consolidated, all relevant
evidence lineage SHALL remain preserved.

The architecture SHALL distinguish:

Number of propositions
        from
Number of supporting evidence items
6. Semantic Relationship Requires an Explicit Cognitive Stage

Non-identical propositions SHALL NOT be merged merely because they
appear similar.

Relationships such as support, conflict, complementarity, independence,
or unresolved relation require explicit assessment.

This responsibility belongs to a dedicated relationship layer.

7. Relationship Assessment Is Not Proposition Synthesis

Determining that two Premises are related does not authorize the
relationship assessor to manufacture a higher-order conclusion.

For example:

P1:
Retrieval preserves source provenance.

P2:
Reasoning conclusions preserve evidence references.

A relationship assessor may determine that these Premises complement
one another.

It SHALL NOT automatically manufacture:

Therefore SentinelAI provides fully auditable reasoning.

That transformation belongs to proposition synthesis and must preserve
its own evidence and reasoning lineage.

8. Proposition Synthesis Must Remain Evidence-Grounded

Future synthesized propositions SHALL remain traceable through their
supporting Premises to underlying evidence.

The intended lineage is:

Source
  ↓
Evidence
  ↓
Premise
  ↓
Relationship
  ↓
Synthesized Proposition
  ↓
Inference
  ↓
Conclusion

No synthesis stage may sever provenance.

9. Unresolved Relationships Are Valid

SentinelAI SHALL be permitted to represent uncertainty about the
relationship between propositions.

The architecture SHALL prefer an explicit unresolved state over a
fabricated relationship.

Epistemic restraint is a valid reasoning result.

Premise Identity

A Premise represents one atomic proposition.

Its identity is conceptually distinct from its evidence support.

Therefore:

Premise identity
      ≠
Evidence identity

A single Premise may have multiple evidence identifiers.

This distinction enables future confidence systems to evaluate
corroboration without inflating proposition counts.

Provenance Model

The proposition architecture SHALL preserve sufficient lineage to
support inspection of:

Conclusion
   ↓
Inference
   ↓
Synthesized Proposition
   ↓
Premise
   ↓
EvidenceItem
   ↓
EvidenceSource

This lineage is part of SentinelAI's observable cognition architecture.

Relationship to Confidence

Proposition count alone SHALL NOT determine confidence.

Repeated evidence for one proposition may improve evidentiary support,
but confidence systems must remain capable of distinguishing:

repeated chunks,
repeated evidence from one document,
independent corroborating documents,
multiple distinct propositions,
conflicting propositions,
and unresolved relationships.

Premise architecture provides the structure necessary for those future
distinctions.

Relationship to Constitutional Coherence

Evidence-grounded proposition synthesis does not replace constitutional
governance.

A proposition may be strongly supported by evidence and still conflict
with SentinelAI's governing principles.

The accepted separation remains:

Evidence Support
      ≠
Constitutional Coherence
Rejected Alternatives
Direct Chunk-to-Inference Reasoning

Rejected as the long-term architecture because inference remains too
closely coupled to retrieval representation.

LLM-Only Premise Generation

Rejected as the foundational extraction mechanism because proposition
identity and provenance require deterministic, inspectable boundaries.

LLM-assisted semantic reasoning may be introduced later behind explicit
contracts.

Fuzzy Premise Deduplication During Extraction

Rejected because semantic similarity does not prove proposition
equivalence.

Relationship Assessment Inside Retrieval

Rejected because retrieval finds candidate evidence and must not acquire
reasoning authority.

Relationship Assessment Inside the Frontend

Rejected because presentation has no authoritative cognitive role.

Consequences
Positive

This decision provides:

explicit proposition-level reasoning,
stronger evidence provenance,
safer future synthesis,
clearer contradiction analysis,
clearer corroboration semantics,
improved confidence architecture,
inspectable proposition lineage,
and reduced dependence on chunk-shaped inference.
Costs

The decision introduces:

additional reasoning models,
additional cognitive stages,
proposition relationship contracts,
more provenance bookkeeping,
additional semantic tests,
and future synthesis complexity.

These costs are accepted.

The complexity represents real cognitive distinctions that should be
modeled explicitly rather than hidden inside an inference step.

Architectural Invariants

The following invariants govern SentinelAI proposition reasoning:

Evidence is not automatically a Premise.

Every evidence-grounded Premise has provenance.

Unknown evidence cannot silently become a Premise.

Exact proposition duplication does not create independent propositions.

Semantic similarity does not prove proposition equivalence.

Relationship assessment does not manufacture conclusions.

Synthesis does not sever evidence lineage.

Unresolved relationships are valid.
Relationship to ADR-035

ADR-035 established that SentinelAI's reasoning interface must preserve
the semantic distinctions produced by cognition.

ADR-036 extends that principle into the reasoning faculty itself.

ADR-035 governs how cognition is exposed.

ADR-036 governs how evidence becomes proposition-level cognition.

Together they establish:

Evidence
   ↓
Inspectable Proposition Formation
   ↓
Inspectable Reasoning
   ↓
Inspectable Presentation
Future Application

This architecture establishes the foundation for:

Premise Relationship Assessment,
proposition clustering,
evidence-grounded proposition synthesis,
contradiction-aware reasoning,
corroboration-aware confidence,
proposition-level reasoning traces,
and richer inspectable Reason cockpit behavior.

Future implementations may use deterministic algorithms, embeddings,
language models, or hybrid methods.

Regardless of implementation mechanism, the architectural contracts in
this ADR SHALL remain authoritative.

Closing Principle

SentinelAI should not merely retrieve evidence and speak from it.

It should transform evidence into explicit, traceable propositions,
reason over their relationships, and preserve the path back to what was
actually known.
