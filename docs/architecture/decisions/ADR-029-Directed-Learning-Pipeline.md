# ADR-029: Directed Learning Pipeline

## Status

Accepted

---

## Context

Prior to Sprint 12, SentinelAI possessed the ability to ingest,
store, and retrieve knowledge.

However, the frontend and backend operated as largely independent
systems.

Knowledge ingestion existed as an API capability rather than a
coherent teaching workflow.

The frontend lacked operational context, while the backend lacked
complete domain metadata within vector memory.

Sprint 12 establishes the first complete teaching pipeline connecting
human intent to persistent cognitive memory.

---

## Decision

SentinelAI adopts a Directed Learning Pipeline.

Human teaching follows the sequence:

Human
→ Workspace Selection
→ Teaching Intent
→ Knowledge Upload
→ Fingerprinting
→ Duplicate Detection
→ Text Extraction
→ Chunking
→ Embedding
→ Persistent Memory
→ Learning Confirmation

The frontend expresses teaching intent.

The backend performs cognitive ingestion.

Knowledge ownership remains a backend responsibility.

---

## Architectural Principles

### 1. Human Intent Precedes Processing

Selecting knowledge is independent from ingesting knowledge.

The frontend never performs ingestion logic.

---

### 2. Context Precedes Learning

Every teaching mission occurs within an explicit workspace.

Knowledge must always possess operational context.

---

### 3. Metadata Is Constitutional

Every stored knowledge artifact carries:

- module
- topic
- collection
- organization_id
- description

Both SQL storage and vector memory preserve identical identity.

---

### 4. Frontend Speaks Human

The frontend presents:

Current Workspace

The backend internally translates workspace into canonical domain
metadata.

Adapters isolate language differences.

---

### 5. Learning Is Directed

Knowledge is never added without intentional human instruction.

Sentinel learns because it is taught.

---

## Capability Earned

Sprint 12 earns the capability:

Directed Learning

Sentinel now accepts intentional human teaching while preserving
organizational context across structured memory and semantic memory.

---

## Consequences

Positive

- Unified teaching workflow
- Domain-aware knowledge ingestion
- Consistent metadata across SQL and Qdrant
- Clear separation of frontend and backend responsibilities
- Foundation for domain-aware Recall and Reason

Trade-offs

- Adapter temporarily translates frontend "domain"
  into backend "module"

Future architectural work may rename backend terminology once
migration becomes appropriate.

---

## Related ADRs

ADR-027 — Platform Integration

ADR-028 — Frontend Architectural Language
