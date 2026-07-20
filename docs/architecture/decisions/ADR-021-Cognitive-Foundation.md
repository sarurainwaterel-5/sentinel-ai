# ADR-021 — Cognitive Foundation

## Status

Accepted

---

## Context

SentinelAI had established a coherent architectural foundation through
its Identity, Bridge, Canon, and Operational Domain subsystems.

However, the platform lacked a canonical representation of cognition.

Documents could be indexed and retrieved, but SentinelAI had no
structured representation of what it had learned or how understanding
was organized.

The project therefore required a domain-independent cognitive
architecture capable of representing observations, evidence, concepts,
principles, relationships, understanding, and learning without coupling
those ideas to any specific implementation or domain.

The architecture also needed to preserve the constitutional principles
defined in the Sentinel Manifesto, Sentinel Triangle, and Sentinel
Language.

---

## Decision

SentinelAI adopts a canonical Cognitive Foundation.

The Cognitive Foundation consists of five architectural layers.

```

Language

↓

Models

↓

Builder

↓

Validator

↓

Renderer

```

Each layer owns a single responsibility.

The architecture intentionally separates construction,
verification, and communication.

Learning, reasoning, extraction, and reflection are deferred to future
subsystems.

---

## Cognitive Language

The Sentinel Language defines the canonical vocabulary used throughout
the Cognitive Foundation.

The following concepts are constitutional.

- Observation
- Evidence
- Concept
- Principle
- Relationship
- Understanding
- Learning Event

These terms shall not be redefined by individual subsystems.

---

## Cognitive Models

The Cognitive Foundation introduces the following domain-independent
models.

- Observation
- Evidence
- Concept
- Principle
- Relationship
- Understanding
- LearningEvent
- CognitiveRegistry

The Cognitive Registry represents SentinelAI's assembled cognitive
state.

It is the canonical representation of what Sentinel currently
understands.

---

## Builder Responsibilities

The Builder assembles cognitive objects into a coherent registry.

Builder responsibilities include:

- assembling cognitive objects
- preserving supplied cognitive state
- constructing the Cognitive Registry

The Builder shall never:

- validate
- repair
- deduplicate
- reason
- classify
- persist

---

## Validator Responsibilities

The Validator verifies structural coherence.

The Validator reports.

The Validator never repairs.

Validation currently focuses on:

- defined identifiers
- unique identifiers

Future validation will include:

- relationship integrity
- evidence traceability
- principle support
- understanding integrity
- learning event consistency

---

## Renderer Responsibilities

The Renderer communicates validated cognitive state.

The Renderer exposes Sentinel's current understanding without modifying
or interpreting it.

Invalid cognitive registries shall not be rendered.

---

## Architectural Principles

The Cognitive Foundation adopts the following architectural principles.

Reality remains the only editable source of truth.

The Cognitive Registry becomes the canonical representation of
SentinelAI's understanding.

Builders construct.

Validators verify.

Renderers communicate.

Learning changes understanding.

Understanding remains accountable to evidence.

---

## Consequences

SentinelAI now possesses a stable cognitive architecture independent of
document ingestion or language models.

Future capabilities—including learning, extraction, reasoning,
reflection, knowledge graphs, and autonomous agents—shall build upon
the Cognitive Foundation rather than introducing parallel cognitive
representations.

This preserves architectural coherence while allowing intelligence to
grow incrementally.

---

## Capability Earned

Sprint 8.3 established SentinelAI's cognitive architecture.

SentinelAI now possesses a canonical language, cognitive models,
registry, validator, and renderer capable of representing structured
understanding.

The platform now possesses the architectural capacity to learn.

Actual learning is introduced in subsequent architectural decisions.

---

## Related Documents

- MANIFESTO.md
- SENTINEL_TRIANGLE.md
- SENTINEL_LANGUAGE.md
- ADR-018 — Operational Domain Foundation
- ADR-019 — Operational Domain Workspace
- ADR-020 — Domain Constitutions Govern Intelligence
