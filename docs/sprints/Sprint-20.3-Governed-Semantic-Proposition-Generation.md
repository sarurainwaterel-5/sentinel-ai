# Sprint 20.3 — Governed Semantic Proposition Generation

## Status

Planned. ADR-037 remains Proposed until implementation review.

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
adapters and explicit error behavior.

### 20.3-E — Production semantic generator

Implement a production adapter that returns only untrusted candidates. Its
prompt or model configuration is not a substitute for grounding validation.

### 20.3-F — ReasoningEngine dependency injection

Inject governed synthesis without direct provider construction. Preserve the
existing evidence-based inference path and expose safe high-level trace and
result information without private chain-of-thought.

### 20.3-G — Adversarial/evaluation suite

Test unsupported facts, certainty inflation, causal overreach, negation
reversal, conflict suppression, fabricated precision, invalid premise and
relationship references, provenance laundering, and provider failure.

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
