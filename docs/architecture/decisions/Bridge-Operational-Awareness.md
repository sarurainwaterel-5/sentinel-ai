# ADR-016 — The Bridge Operational Awareness Workspace

## Status

Accepted

---

## Context

As SentinelAI's capabilities expanded, engineering concepts such as Canon, Knowledge Graph, Resolver, and Manifest began appearing directly in the user interface.

Although technically accurate, these concepts exposed implementation details instead of helping operators understand SentinelAI.

A dedicated operational workspace was required.

---

## Decision

The Bridge shall become SentinelAI's operational awareness workspace.

Its purpose is to summarize SentinelAI's current state without performing reasoning, teaching, or modifying knowledge.

The Bridge presents:

- Core Principles
- Connections
- Reflection
- Operational Health

through a unified summary service.

---

## Consequences

Positive

- clearer separation of responsibilities
- simplified operator experience
- stronger architectural boundaries
- consistent product language

Tradeoffs

- engineering terminology remains internal
- translation layer must be maintained as SentinelAI evolves

---

## Design Principle

Engineering language belongs to builders.

Operator language belongs to operators.

The Bridge exists to translate between them while preserving architectural integrity.

---

## Related ADRs

ADR-013 Living Canon

ADR-014 Knowledge Graph

ADR-015 Bridge Summary Service
