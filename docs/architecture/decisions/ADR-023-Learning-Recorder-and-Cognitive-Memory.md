# ADR-023 — Learning Recorder and Cognitive Memory

## Status

Accepted

---

## Context

Sprint 8.3B established SentinelAI's Learning Pipeline.

SentinelAI became capable of transforming observations into structured
understanding through a disciplined cognitive process.

However, understanding alone represents only current cognitive state.

The platform required a mechanism capable of preserving how
understanding evolved across time.

Without historical continuity, SentinelAI could not explain the origin
of its understanding or support future reflection.

---

## Decision

SentinelAI adopts a Learning Recorder.

The Learning Recorder records completed cognitive learning cycles.

Learning does not create understanding.

Learning records the evolution of understanding.

Each Learning Event preserves the complete intellectual history of one
learning cycle.

Learning Records become the foundation of SentinelAI's cognitive memory.

---

## Responsibilities

The Learning Recorder shall:

- record completed learning cycles
- preserve cognitive history
- preserve evidence traceability
- preserve affected domains
- preserve timestamps
- summarize cognitive change

The Learning Recorder shall not:

- discover cognition
- build understanding
- validate cognition
- render cognition
- reason
- reflect

---

## Learning Event

A Learning Event records the completion of one learning cycle.

Each event preserves:

- observations
- evidence
- concepts
- principles
- relationships
- understandings
- affected domains
- timestamps
- summary

Learning Events remain immutable historical records.

Future learning does not modify previous events.

New understanding produces new Learning Events.

---

## Cognitive Memory

Learning Events collectively form SentinelAI's Cognitive Memory.

Memory preserves the evolution of understanding across time.

Memory answers:

"How did SentinelAI arrive at its current understanding?"

Memory preserves intellectual continuity.

Memory enables future reflection.

---

## Architectural Principles

The Learning Recorder adopts the following constitutional principles.

Understanding exists in the present.

Learning exists across time.

Memory preserves learning.

Learning records understanding.

Reflection examines learning.

Wisdom refines understanding.

Every learning event shall remain traceable to evidence.

Learning history shall remain immutable.

---

## Separation of Responsibilities

Cognition produces understanding.

Learning records understanding.

Memory preserves understanding.

Reflection examines understanding.

Each subsystem owns one responsibility.

No subsystem shall assume the responsibilities of another.

---

## Consequences

SentinelAI now possesses historical continuity.

Future Reflection systems may analyze Learning History without modifying
the underlying cognitive record.

Reasoning engines may explain conclusions by referencing historical
Learning Events.

Explainability becomes an inherent architectural property rather than an
additional feature.

---

## Capability Earned

Sprint 8.3C establishes SentinelAI's Cognitive Memory.

The platform can now preserve the evolution of understanding through
immutable Learning Events.

SentinelAI now possesses both current understanding and historical
learning.

This establishes the architectural foundation required for Reflection.

---

## Related Documents

- THEORY_OF_UNDERSTANDING.md
- MANIFESTO.md
- SENTINEL_TRIANGLE.md
- ADR-021 — Cognitive Foundation
- ADR-022 — Learning Pipeline
- Sprint 8.3B — First Cognitive Learning Cycle
- Sprint 8.3C — Learning Recorder & Theory of Understanding
