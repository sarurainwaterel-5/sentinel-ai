# ADR-026 — Constitutional Reasoning Architecture

## Status

Accepted

---

## Context

SentinelAI now possesses:

- structured understanding
- preserved learning history
- cognitive memory
- disciplined reflection
- reflective patterns
- insights
- recommendations

These capabilities allow SentinelAI to understand what it knows, examine
how that understanding evolved, and identify patterns across learning.

However, SentinelAI still lacks a constitutional mechanism for deriving
justified conclusions from its current understanding.

Reflection identifies what learning history reveals.

Reasoning must determine what conclusion most responsibly follows from
the available understanding, evidence, principles, and reflection.

Without a dedicated Reasoning subsystem, conclusion formation risks
becoming implicit, inconsistent, or coupled directly to language-model
generation.

---

## Decision

SentinelAI adopts Reasoning as an independent constitutional subsystem.

Reasoning consumes validated cognitive and reflective state.

Reasoning produces justified conclusions.

Reasoning shall remain separate from:

- observation
- evidence discovery
- learning
- reflection
- human decision-making
- action

Reasoning supports judgment.

Reasoning does not replace judgment.

---

## Constitutional Definition

Reasoning is the disciplined process of deriving the most responsible
conclusion from available understanding while remaining accountable to
reality.

Reasoning determines what follows.

It does not invent what is known.

---

## Reasoning Inputs

The Reasoning subsystem may consume:

- Understandings
- Evidence
- Principles
- Relationships
- Learning Events
- Patterns
- Insights
- Recommendations
- Domain context
- User questions or reasoning goals

Every reasoning input shall remain traceable to its originating
cognitive or reflective object.

---

## Reasoning Outputs

The Reasoning subsystem produces structured reasoning artifacts.

Initial reasoning objects shall include:

- Premise
- Assumption
- Evidence Assessment
- Counterargument
- Conclusion
- Reasoning Report

A conclusion shall preserve:

- supporting premises
- supporting evidence
- applicable principles
- contradictory evidence
- assumptions
- uncertainty
- confidence
- affected domains

---

## Justified Conclusions

A conclusion is not a fact.

A conclusion is a disciplined judgment derived from available
understanding.

Every conclusion shall be:

- explainable
- evidence-traceable
- principle-governed
- uncertainty-aware
- revisable
- accountable to reality

Reasoning shall distinguish among:

- supported conclusions
- provisional conclusions
- unsupported conclusions
- inconclusive reasoning

---

## Architectural Lifecycle

Reasoning follows the Sentinel Constitutional Subsystem Pattern.

Language

↓

Models

↓

Builder

↓

Validator

↓

Renderer

↓

Engine

Each layer owns one responsibility.

---

## Layer Responsibilities

### Language

Defines the canonical vocabulary of reasoning.

### Models

Represent premises, assumptions, evidence assessments,
counterarguments, conclusions, and reasoning reports.

### Builder

Organizes reasoning objects into a coherent Reasoning Registry.

### Validator

Protects structural integrity and traceability.

### Renderer

Communicates justified conclusions without exposing implementation.

### Engine

Coordinates the complete reasoning process through orchestration.

---

## Separation of Responsibilities

Cognition represents understanding.

Learning records changes in understanding.

Memory preserves learning history.

Reflection examines learning history.

Reasoning derives justified conclusions.

Humans remain responsible for decisions and actions.

No subsystem shall assume the responsibilities of another.

---

## Reasoning Boundaries

Reasoning shall never:

- alter reality
- modify historical Learning Events
- rewrite evidence
- conceal contradictory evidence
- convert confidence into certainty
- fabricate missing understanding
- make autonomous human decisions
- present unsupported conclusions as established truth

When evidence is insufficient, Reasoning shall report that insufficiency.

---

## Accountability Chain

Every justified conclusion shall support a traceable accountability path.

Reality

↓

Observation

↓

Evidence

↓

Understanding

↓

Reflection

↓

Reasoning

↓

Justified Conclusion

↓

Human Judgment

This path provides explainability through architectural traceability
rather than exposure of private internal reasoning.

---

## Consequences

SentinelAI gains a dedicated architecture for disciplined conclusion
formation.

Language models and future reasoning technologies may assist individual
stages, but they shall populate the constitutional Reasoning
architecture rather than replace it.

Reasoning becomes implementation-independent.

Human judgment remains explicitly protected.

---

## Capability Earned

SentinelAI gains the architectural capacity to derive justified,
explainable, and revisable conclusions from earned understanding.

This capability advances SentinelAI from reflective learning toward
responsible decision support.

---

## Cognitive Coherence

The primary responsibility of Reasoning is preserving cognitive
coherence.

Reasoning evaluates whether accumulated understanding, principles,
evidence, learning history, and reflective insights remain
simultaneously consistent.

Reasoning derives conclusions that maximize coherence while remaining
accountable to reality.

When coherence cannot be achieved, Reasoning shall explicitly identify
the unresolved contradiction rather than conceal it.

## Related Documents

- MANIFESTO.md
- VISION.md
- THEORY_OF_UNDERSTANDING.md
- THEORY_OF_REFLECTION.md
- THEORY_OF_REASONING.md
- SENTINEL_SUBSYSTEM_PATTERN.md
- ADR-021 — Cognitive Foundation
- ADR-022 — Learning Pipeline
- ADR-023 — Learning Recorder and Cognitive Memory
- ADR-024 — Reflection Architecture
- ADR-025 — Constitutional Subsystem Pattern

