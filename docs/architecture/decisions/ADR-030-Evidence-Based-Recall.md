# ADR-030: Evidence-Based Recall

## Status

Accepted

---

## Context

Sprint 12 introduced Directed Learning, enabling SentinelAI to
accept intentional human teaching and preserve structured and
semantic memory.

Although knowledge could be stored, SentinelAI lacked a dedicated
Recall capability capable of reconstructing evidence from the
currently active operational workspace.

Retrieval existed independently of operational context.

Sprint 13 establishes Recall as a constitutional cognitive
capability.

---

## Decision

SentinelAI adopts Evidence-Based Recall.

Recall reconstructs knowledge from the active workspace using
semantic retrieval, evidence assembly, and grounded reasoning.

Recall never generates unsupported knowledge.

Every response originates from retrieved evidence.

---

## Recall Pipeline

Human Question

↓

Current Workspace

↓

Domain-Aware Retrieval

↓

Evidence Assembly

↓

Context Construction

↓

Language Generation

↓

Evidence Attribution

↓

Human Response

---

## Architectural Principles

### 1. Recall Reconstructs Memory

Recall reproduces learned knowledge.

It never invents knowledge.

---

### 2. Workspace Precedes Recall

Every recall operation executes inside the currently selected
workspace.

Operational context determines retrieval boundaries.

---

### 3. Evidence Precedes Explanation

Sentinel retrieves supporting evidence before generating any
response.

Explanation is always grounded in retrieved knowledge.

---

### 4. Recall Preserves Traceability

Every answer returns supporting evidence.

Evidence remains visible to the human operator.

---

### 5. Retrieval and Reasoning Remain Separate

Retrieval discovers evidence.

Reasoning interprets evidence.

Neither subsystem assumes responsibility for the other.

---

## Capability Earned

Evidence-Based Recall

SentinelAI can now reconstruct previously learned knowledge from
the appropriate operational workspace while preserving evidence
traceability.

---

## Consequences

Positive

- Domain-aware retrieval
- Evidence-grounded responses
- Operational workspace awareness
- Source attribution
- Foundation for analytical reasoning

Trade-offs

- Retrieval depends upon metadata quality.
- Workspace selection influences recall results.
- Future multi-domain recall requires explicit orchestration.

---

## Related ADRs

ADR-027 — Platform Integration

ADR-028 — Frontend Architectural Language

ADR-029 — Directed Learning Pipeline
