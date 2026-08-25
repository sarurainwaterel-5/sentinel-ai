# Sprint 20.1 — Evidence-Grounded Premise Extraction

## Status

**Complete**

## Validation

Final acceptance gates:

```text
Focused premise extraction tests: 3 passed
Reasoning regression suite:        5 passed
Premise model duplication:         RESOLVED
Evidence provenance invariant:     VERIFIED
Unknown evidence exclusion:        VERIFIED
Exact proposition consolidation:   VERIFIED

Sprint 20.1 was accepted only after evidence could be transformed into
explicit propositions without losing provenance or silently promoting
unusable evidence into reasoning premises.

No acceptance criterion depended solely on successful retrieval.

Mission

Sprint 20.1 introduced an explicit proposition layer between evidence
analysis and downstream inference.

Prior to this sprint, SentinelAI's reasoning architecture organized
retrieved evidence and formed candidate inferences, but inference
statements remained substantially shaped by retrieved source chunks.

The objective of this sprint was to establish a bounded transformation:

Retrieved Evidence
        ↓
Evidence Analysis
        ↓
Premise Extraction
        ↓
Atomic Evidence-Grounded Propositions

A retrieved chunk is evidence material.

A Premise is an explicit proposition derived from usable evidence.

Those concepts SHALL NOT be treated as interchangeable.

Commander's Intent

Reason should reason over propositions grounded in evidence rather than
treat retrieved chunks themselves as the final units of cognition.

The proposition layer must increase reasoning capability without
weakening epistemic restraint.

Premise extraction therefore SHALL preserve:

evidence lineage,
source provenance,
deterministic normalization,
bounded transformation,
and explicit exclusion of unusable evidence.

Premise extraction SHALL NOT become conclusion generation.

Problem

The existing reasoning pipeline contained an architectural compression:

Evidence
   ↓
Inference

Although evidence remained inspectable, the transition from retrieved
material to reasoning propositions was not represented as its own
cognitive boundary.

This allowed candidate inference language to remain too closely coupled
to individual retrieved chunks.

The resulting behavior could resemble sophisticated chunk selection
rather than proposition-based reasoning.

Architectural Change

Sprint 20.1 introduced PremiseExtractor.

The new conceptual pipeline is:

Retrieval
   ↓
EvidenceSource
   ↓
EvidenceItem
   ↓
PremiseExtractor
   ↓
Premise
   ↓
Future Relationship Assessment
   ↓
Future Proposition Synthesis
   ↓
Inference

The extractor establishes atomic propositions.

It does not yet determine relationships among propositions or synthesize
higher-order claims.

Premise Contract

A reasoning Premise represents one normalized proposition grounded in
usable evidence.

Each Premise contains:

premise_id
statement
evidence_ids
domain_ids
metadata

The critical invariant is:

Premise
   ↓
MUST possess evidence lineage

An evidence-derived Premise without evidence provenance is invalid.

Evidence Eligibility

Not every retrieved item earns proposition status.

The extractor accepts usable evidence from the eligible evidence
collections and excludes unknown evidence.

The accepted boundary is:

Usable Evidence
      ↓
May become Premise


Unknown / Unusable Evidence
      ↓
MUST NOT become Premise

Retrieval therefore remains distinct from epistemic promotion.

Being retrieved does not make information a reasoning premise.

Deterministic Normalization

Premise extraction performs bounded normalization of evidence
statements.

Normalization may:

trim surrounding whitespace,
normalize repeated whitespace,
establish deterministic comparison keys.

Normalization SHALL NOT:

invent semantic content,
paraphrase into stronger claims,
infer unstated relationships,
resolve contradictions,
or manufacture conclusions.

This preserves the distinction between normalization and reasoning.

Exact Proposition Consolidation

Sprint 20.1 established the first proposition consolidation behavior.

When multiple evidence items express the same normalized proposition,
SentinelAI creates one Premise while preserving the combined evidence
lineage.

The accepted relationship is:

Evidence A ──┐
             │
             ├── Same normalized proposition
             │
Evidence B ──┘
             ↓
         One Premise
             ↓
   evidence_ids = [A, B]

Repeated evidence may strengthen the provenance of a proposition.

Repeated evidence SHALL NOT masquerade as multiple independent
propositions.

Provenance Preservation

Consolidation does not discard source lineage.

The resulting Premise preserves available provenance including:

evidence identifiers,
source document identifiers,
source chunk positions,
evidence dispositions,
and domain identifiers.

This allows future reasoning stages to distinguish proposition identity
from evidentiary support.

Unknown Evidence

Unknown evidence is deliberately excluded from premise extraction.

This establishes the invariant:

Unknown evidence
      ≠
Reasoning premise

An evidence item that cannot provide usable evidentiary content must not
silently acquire reasoning authority merely because retrieval returned
it.

Model Integrity Correction

Sprint 20.1 also identified duplicate service-layer Premise model
definitions.

The duplicate definitions were not contract-equivalent.

One definition required non-empty evidence lineage.

The later duplicate allowed an empty evidence_ids collection and,
because of Python name rebinding, became the effective runtime model.

The duplicate was removed.

The stronger evidence-lineage contract was retained.

The resulting invariant is:

Evidence-Grounded Premise
          ↓
evidence_ids MUST be non-empty

The separate core reasoning Premise remains a distinct architectural
model serving the broader core reasoning registry.

Architectural Boundaries

Premise extraction SHALL:

transform usable evidence into atomic propositions,
preserve evidence lineage,
preserve relevant source metadata,
normalize proposition representation deterministically,
consolidate exact-equivalent propositions,
and reject unusable evidence from proposition promotion.

Premise extraction SHALL NOT:

determine truth,
generate conclusions,
calculate confidence,
resolve contradictions,
infer semantic equivalence from merely similar wording,
synthesize multiple propositions into higher-order claims,
or perform constitutional governance.
Why Semantic Similarity Was Deferred

Sprint 20.1 deliberately does not merge propositions merely because
their wording appears semantically similar.

For example:

Premise A:
Sentinel preserves evidence provenance.

Premise B:
Sentinel maintains traceability between conclusions and sources.

These propositions may be related.

They are not deterministically identical.

Automatically collapsing them during extraction would grant semantic
reasoning authority to the extraction layer.

That responsibility is deferred to explicit relationship assessment and
proposition synthesis.

Testing Architecture

Focused tests protect three extraction behaviors.

Traceable Premise Extraction

Usable evidence produces Premises with explicit evidence lineage.

Unknown Evidence Exclusion

Unknown evidence does not produce Premises.

Exact Proposition Consolidation

Exact-equivalent normalized propositions produce one Premise with
combined evidence provenance.

The broader reasoning regression suite remained green after the
stronger Premise model contract was restored.

Established Laws

Sprint 20.1 establishes four reasoning laws.

Law 1 — Evidence Grounding

Usable evidence may become a traceable Premise.

Law 2 — Epistemic Eligibility

Unknown or unusable evidence may not become a Premise.

Law 3 — Proposition Identity

Equivalent normalized evidence statements represent one proposition,
not multiple independent propositions.

Law 4 — Provenance

Every evidence-grounded Premise must retain non-empty evidence lineage.

Cognitive Evolution

Before Sprint 20.1:

Retrieved Chunks
      ↓
Evidence Analysis
      ↓
Candidate Inference
      ↓
Conclusion

After Sprint 20.1:

Retrieved Chunks
      ↓
Evidence Analysis
      ↓
Premise Extraction
      ↓
Atomic Evidence-Grounded Propositions
      ↓
[Relationship Assessment]
      ↓
[Proposition Synthesis]
      ↓
Inference
      ↓
Conclusion

The bracketed stages remain future work.

Sprint 20.1 establishes the boundary they will consume.

What We Learned

Evidence and propositions are related but distinct cognitive objects.

A source passage may contain material relevant to reasoning.

A Premise represents the bounded proposition Sentinel is permitted to
carry forward from that material.

Making this transformation explicit improves:

inspectability,
provenance,
reasoning composition,
future contradiction analysis,
future corroboration analysis,
and confidence semantics.

It also creates a natural location for future proposition-level
reasoning without contaminating retrieval or evidence analysis.

Sprint Outcome

Sprint 20.1 established SentinelAI's first explicit evidence-grounded
proposition layer.

Sentinel can now transform usable evidence into atomic Premises while
preserving provenance and rejecting unusable evidence.

Exact-equivalent propositions can be consolidated without losing their
independent evidence references.

The reasoning architecture is therefore no longer required to treat
retrieved chunks as its only meaningful units.

What Comes Next

Sprint 20.2 will introduce Premise Relationship Assessment.

Its purpose will be to determine bounded relationships among atomic
Premises without synthesizing new conclusions.

Candidate relationships include:

SUPPORTS
CONFLICTS
COMPLEMENTS
INDEPENDENT
UNRESOLVED

Relationship assessment will establish the proposition structure needed
for later evidence-grounded synthesis.

Closing Principle

Evidence provides the material for reasoning.

Premises provide the propositions.

Sentinel should know the difference.
