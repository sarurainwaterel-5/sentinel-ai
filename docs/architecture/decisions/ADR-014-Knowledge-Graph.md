# ADR-014 – Introduce the Canon Knowledge Graph

**Status:** Accepted

---

# Context

The Living Canon introduced during Sprint 7.5 gave SentinelAI a permanent body of organized knowledge.

Documents could be discovered, classified, and summarized.

However, the Canon still represented knowledge as isolated documents.

Although humans naturally understand relationships between architecture decisions, sprint history, philosophy, design, and implementation, SentinelAI had no internal representation of those connections.

Without explicit relationships, future reasoning would rely entirely on retrieval rather than understanding.

---

# Decision

SentinelAI will represent Canon knowledge as a graph.

Each document becomes a node.

Supporting entities such as layers and document classifications also become nodes.

Relationships are represented through explicit edges connecting those entities.

The initial implementation intentionally uses deterministic relationships generated from known metadata.

Examples include:

- belongs_to
- classified_as

Future iterations will introduce semantic relationships discovered automatically through document analysis.

---

# Rationale

Graph structures more closely represent how engineering knowledge is organized than traditional document collections.

They allow SentinelAI to:

- Navigate relationships
- Traverse connected knowledge
- Explain why documents are related
- Support future reasoning engines
- Visualize knowledge structure within the Bridge

Rather than replacing vector search, the graph complements it.

Vector search answers:

*"What is similar?"*

The Knowledge Graph answers:

*"How is this connected?"*

Together they provide a stronger foundation for intelligent reasoning.

---

# Consequences

## Positive

- Establishes explicit knowledge relationships.
- Enables graph traversal.
- Supports future visualization.
- Creates a foundation for graph-based reasoning.
- Improves explainability.

---

## Trade-offs

Maintaining a graph introduces additional architectural complexity.

Relationship generation must remain deterministic and understandable before more advanced semantic techniques are introduced.

This additional complexity is considered worthwhile because it creates a long-term foundation for cognitive reasoning.

---

# Future Direction

Future versions of the Knowledge Graph will introduce:

- Reference discovery
- Semantic relationship detection
- Concept extraction
- Knowledge clusters
- Reasoning paths
- Graph visualization within the Bridge
- Hybrid graph and vector retrieval

The Canon Knowledge Graph represents the first step toward SentinelAI understanding not only what it knows, but how its knowledge is connected.

---

# Decision Summary

The Canon will evolve from an organized collection of documents into a connected representation of engineering knowledge.

This decision establishes the architectural foundation for future graph reasoning and cognitive capabilities.
