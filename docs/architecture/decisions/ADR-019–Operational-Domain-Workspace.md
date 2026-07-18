# ADR-019 – Operational Domain Workspace

## Status

Accepted

---

## Context

Sprint 8.0 established the backend Operational Domain architecture.

Operators required a way to observe validated domains without duplicating
business logic inside the frontend.

The workspace needed to remain a presentation layer while preserving backend
ownership of domain reasoning.

---

## Decision

The frontend shall consume the rendered Domain Model exclusively through
read-only REST services.

React components shall display:

- summary
- validation
- evidence counts
- operational status

No frontend component may compute domain validity.

No frontend component may infer operational state.

All validation remains owned by the backend.

---

## Consequences

Positive

- Single source of truth
- Consistent validation
- Reduced frontend complexity
- Clean architectural separation
- Extensible workspace model

Negative

- Frontend depends on backend availability.
- CORS configuration becomes infrastructure responsibility.

---

## Sentinel Pattern

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

REST API

↓

Frontend Service

↓

Workspace

↓

Operator

---

## Principle

Operational Domains specialize SentinelAI's operation without changing
SentinelAI's identity.

The frontend observes validated reality.

It never defines reality.

---

## Outcome

Operational Domains became SentinelAI's first operational workspace generated
entirely from validated architectural knowledge.

The Sentinel Pattern remains intact.

