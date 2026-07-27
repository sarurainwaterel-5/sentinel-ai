# ADR-031 — Unified Memory Architecture

**Status:** Accepted

**Date:** 2026-07-27

**Sprint:** 13.1 — Unified Memory

---

# Context

SentinelAI stores knowledge across two complementary systems:

- PostgreSQL
- Qdrant

As Sentinel evolved, earlier document uploads were indexed before several metadata fields existed.

This resulted in a split between:

- canonical document identity stored in PostgreSQL
- semantic vector memory stored in Qdrant

The platform required a permanent architecture for maintaining synchronization between both systems while preserving historical knowledge.

---

# Decision

SentinelAI adopts a **Unified Memory Architecture**.

The architecture defines PostgreSQL as the canonical source of truth for document identity and metadata.

Qdrant is defined as a derived semantic memory optimized for retrieval and reasoning.

Vector memory must always be reconstructable from canonical document records.

---

# Memory Architecture

```
                Sentinel Memory

                PostgreSQL
          (Canonical Knowledge)

                     │
                     │
                     ▼

            Migration / Validation

                     │
                     ▼

                 Qdrant
          (Semantic Vector Memory)

                     │
                     ▼

            Retrieval / Recall
                     │
                     ▼

                 Reasoning
```

---

# Canonical Source

Every document record stored in PostgreSQL defines:

- document_id
- filename
- file_hash
- module
- topic
- collection
- description
- organization_id
- embedding_model
- status
- uploaded_at

These values represent Sentinel's authoritative knowledge identity.

No vector payload may contradict canonical metadata.

---

# Semantic Memory

Qdrant stores:

- embeddings
- chunk text
- chunk index
- semantic metadata

Vector memory exists solely to accelerate retrieval.

It is considered reproducible infrastructure.

Loss of vectors must never imply loss of knowledge.

---

# Identity Hierarchy

Memory reconciliation follows this order:

1. document_id
2. file_hash
3. unique filename (legacy compatibility only)

Filename reconciliation is permitted only when the filename uniquely identifies a single canonical document.

---

# Migration Philosophy

Metadata migrations are:

- idempotent
- additive
- non-destructive

A migration must:

- preserve existing text
- preserve chunk indices
- preserve embeddings
- update only missing or stale metadata

Correct payloads are skipped.

Repeated execution must produce no further changes.

---

# Vector Reconstruction

When vector memory is missing but canonical documents remain:

```
Existing PDF
        │
        ▼

Extract Text
        │
        ▼

Chunk
        │
        ▼

Embed
        │
        ▼

Store Vectors

```

Vector reconstruction must:

- reuse the existing document_id
- reuse the existing file_hash
- preserve canonical metadata
- never create duplicate document records

---

# Large Document Handling

Large documents may exceed transport limits during vector storage.

To support production-scale knowledge bases:

- vectors are written in bounded batches
- batch size is configurable
- reconstruction is resumable
- payload size limits never affect document identity

---

# Memory Lifecycle

SentinelAI defines the following lifecycle:

```
Teach
   │
   ▼

Store
   │
   ▼

Retrieve
   │
   ▼

Reason
   │
   ▼

Migrate
   │
   ▼

Repair
   │
   ▼

Verify
   │
   ▼

Govern
```

Every stage preserves canonical identity.

---

# Integrity Verification

Memory health is measured through reconciliation.

A healthy memory satisfies:

- every document exists in PostgreSQL
- every document has semantic vectors
- vector payload metadata matches canonical metadata
- migrations report zero required updates
- reconstruction reports zero missing vectors

---

# Operational Principles

SentinelAI follows these principles:

1. PostgreSQL is authoritative.

2. Qdrant is reproducible.

3. Migrations repair memory without destroying history.

4. Reconstruction restores semantic memory from canonical knowledge.

5. Metadata synchronization is continuously verifiable.

6. Memory operations must remain safe to execute repeatedly.

---

# Consequences

Benefits:

- deterministic memory
- recoverable semantic storage
- production-safe migrations
- platform-wide consistency
- simplified future upgrades

Tradeoffs:

- additional migration tooling
- periodic integrity verification
- maintenance of reconstruction services

These tradeoffs are accepted because they significantly improve long-term platform reliability.

---

# Outcome

Sprint 13.1 established SentinelAI's first permanent Memory Operations framework.

Capabilities introduced:

- Metadata Migration
- Vector Reconstruction
- Memory Verification
- Idempotent Migration Services
- Batch Vector Storage
- Unified Memory

SentinelAI now operates with a fully unified knowledge architecture in which canonical document identity and semantic memory remain synchronized and recoverable.
