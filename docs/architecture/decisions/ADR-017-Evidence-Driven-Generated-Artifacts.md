# docs/architecture/decisions/ADR-017-Evidence-Driven-Generated-Artifacts.md

# ADR-017
# Evidence-Driven Generated Artifacts

## Status

Accepted

---

# Context

SentinelAI increasingly produces architectural artifacts describing its
internal state.

Examples include:

- Canon Manifest
- Knowledge Graph
- Bridge Summary
- Identity Model

Maintaining these artifacts manually introduces the risk that published
documentation diverges from the actual architecture.

SentinelAI requires a deterministic method for ensuring that every
published description reflects observable system reality.

---

# Decision

Generated artifacts shall never be edited manually.

Instead:

1. Modify system reality.
2. Discover architectural observations.
3. Record observations.
4. Organize observations.
5. Validate every claim.
6. Render a new generated artifact.

Only generated artifacts may be published.

---

# Sentinel Pattern

Reality

↓

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

Generated Artifact

Each stage owns exactly one responsibility.

No stage may assume responsibilities belonging to another stage.

---

# Engineering Principles

## Reality Principle

Reality is the only editable source of truth.

---

## Identity Principle

SentinelAI's identity is discovered rather than authored.

---

## Validation Principle

Only validated truth may become identity.

---

## Separation Principle

Workspaces present understanding.

Engines produce understanding.

---

# Consequences

Positive

- Single source of truth
- Deterministic documentation
- Reduced configuration drift
- Strong architectural traceability
- Easier automated validation
- Improved explainability
- Repeatable subsystem architecture

Trade-offs

- Architectural changes require regeneration
- Generated artifacts cannot be manually patched
- Slightly longer engineering workflow
- Increased discipline around source ownership

---

# Rationale

Generated documentation should never become another editable source of
truth.

Instead, reality itself remains authoritative.

Every generated artifact becomes an evidence-backed reflection of the
current system rather than an independently maintained document.

This approach ensures that SentinelAI describes only what can be observed,
verified, and proven.

---

# Closing Principle

Architecture produces understanding.

Understanding produces identity.

Identity must always remain grounded in reality.
