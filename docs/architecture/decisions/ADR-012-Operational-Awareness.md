# ADR-012
# Operational Awareness

**Status:** Accepted

**Date:** 2026-07-05

**Authors:** Rain & SentinelAI Architecture Team

**Supersedes:** None

**Related ADRs:**

- ADR-008 Constitutional Memory
- ADR-009 Constitution as Code
- ADR-010 Reasoning Orchestration
- ADR-011 Cognitive Engine

---

# ADR-012
# Operational Awareness

## Status

Accepted

---

## Context

SentinelAI operates as a Cognitive Operating System composed of multiple
independent services.

Examples include:

- Bridge
- PostgreSQL
- Qdrant
- Cognitive Engine
- Constitution
- Memory Services
- Knowledge APIs
- Embedding Services

During development it became apparent that individual services could become
unavailable while the application itself remained online.

Traditional software often exposes these failures through technical exceptions
or server errors.

Examples:

- Connection refused
- HTTP 500
- Database unavailable

These messages provide little operational meaning to users.

A Cognitive Operating System should first understand its own operational state
before attempting to assist others.

---

## Decision

SentinelAI shall continuously observe its own operational health.

Rather than exposing infrastructure failures directly to users,
SentinelAI will translate technical failures into operational awareness.

Examples:

Instead of

HTTP 500

SentinelAI communicates

Knowledge services are currently unavailable.

Instead of

Connection refused

SentinelAI communicates

PostgreSQL is offline.

Suggested action:
Start infrastructure services.

Operational meaning takes priority over implementation details.

Detailed diagnostics remain available through engineering logs.

---

## Operational Readiness

SentinelAI maintains readiness indicators for critical services.

Examples include:

- Frontend
- Backend API
- PostgreSQL
- Qdrant
- Constitution
- Core Memory
- Cognitive Engine
- Embedding Service

The Bridge presents these indicators before any operational work begins.

---

## Bridge Philosophy

The Bridge represents SentinelAI's situational awareness.

It continuously answers:

"What is the current state of the system?"

rather than

"What errors occurred?"

---

## Consequences

### Positive

• Immediate visibility into platform health

• Faster troubleshooting

• Human-centered operational reporting

• Increased confidence before beginning work

• Improved onboarding for new contributors

• Production-ready operational behavior

---

### Tradeoffs

Additional health endpoints must be maintained.

Infrastructure monitoring becomes part of the platform architecture.

---

## Future Work

Operational Awareness will expand to include:

- Docker service discovery
- Kubernetes health
- GPU readiness
- Disk utilization
- Memory pressure
- Queue health
- External integrations
- AI model availability
- Performance telemetry
- Predictive health analysis

---

## Guiding Principle

SentinelAI observes itself before observing the world.

Operational awareness precedes operational intelligence.
