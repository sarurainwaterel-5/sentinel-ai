# ADR-018 — Operational Domain Foundation

Status

Accepted

---

## Context

Following the completion of SentinelAI's Self subsystem, a mechanism was
required to represent discipline-specific operating contexts such as
Engineering, Trading, Security, and Law.

The architecture needed to support specialization without fragmenting
SentinelAI's identity.

---

## Decision

Operational Domains are introduced as a foundational architectural
subsystem.

Operational Domains specialize SentinelAI's operation while preserving a
single validated constitutional identity.

Domains represent operational context.

Domains are not alternate identities, personalities, or independent
assistants.

Operational Domains follow the Sentinel Pattern:

Discovery

↓

Registry

↓

Builder

↓

Validator

↓

Renderer

↓

Domain Model

---

## Responsibilities

Operational Domains:

- define operational context
- represent discipline identity
- organize validated operational information

Operational Domains do not:

- activate themselves
- reason
- modify identity
- duplicate knowledge
- interpret evidence

---

## Architectural Consequences

Positive

- Identity remains singular.
- Operational specialization becomes composable.
- Future User Domains inherit the same architecture.
- Future Enterprise Domains inherit the same architecture.
- Builder owns composition.
- Registry remains simple.

Trade-offs

Operational Domains intentionally begin with minimal behavior.

Activation, composition, and reasoning are deferred to future sprints.

---

## Architectural Principle

Operational Domains specialize SentinelAI's operation while preserving a
single validated constitutional identity.

Identity is permanent.

Operational context is selected.

---

## Related Documents

SENTINEL_TRIANGLE.md

LANGUAGE_GUIDE.md

SPRING-8.0-Operational-Domain-Foundation.md
