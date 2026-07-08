# ADR-015 – Introduce the Relationship Discovery Engine

**Status:** Accepted

---

# Context

Sprint 7.6 introduced the Canon Knowledge Graph, providing a structural representation of SentinelAI's documentation.

The graph successfully organized documents into layers and classifications.

However, all relationships were generated from predefined metadata.

Although documents naturally referenced architecture decisions, sprint records, and related concepts, those connections were not represented within the graph.

Without interpreting document content, the graph remained primarily organizational rather than semantic.

---

# Decision

SentinelAI will introduce a Relationship Discovery Engine.

The engine is composed of two independent stages.

The Extractor performs observation by reading documents and extracting structured signals.

The Resolver performs interpretation by converting those signals into graph relationships through deterministic inference rules.

The resulting relationships become part of the Canon Knowledge Graph.

---

# Rationale

Separating observation from interpretation creates a more maintainable cognitive architecture.

The Extractor remains responsible for discovering facts.

The Resolver remains responsible for assigning meaning.

This mirrors the broader architectural philosophy of separating perception from reasoning.

Rather than relying exclusively on vector similarity or language models, SentinelAI first builds explicit, explainable knowledge relationships.

Future reasoning systems can therefore explain how conclusions were reached by traversing known graph relationships.

---

# Consequences

## Positive

- Knowledge relationships become explicit.
- Graph quality improves over time.
- Relationship inference remains deterministic and explainable.
- Graph traversal becomes possible.
- Future semantic reasoning builds upon an existing relationship model.

---

## Trade-offs

Relationship discovery introduces additional processing during graph construction.

Inference rules require ongoing maintenance as new document types and relationship categories are introduced.

These trade-offs are considered acceptable because they improve transparency and maintainability.

---

# Future Direction

Future iterations of the Relationship Discovery Engine will support:

- Semantic relationship inference
- Concept extraction
- Dependency discovery
- Cross-reference analysis
- Graph confidence scoring
- Hybrid graph and vector reasoning

Ultimately, the Relationship Discovery Engine enables SentinelAI to evolve from organizing documentation toward understanding the relationships that define its knowledge.

---

# Decision Summary

SentinelAI will infer graph relationships through a dedicated Relationship Discovery Engine that separates observation from interpretation.

This decision establishes the architectural foundation for explainable graph reasoning and future cognitive capabilities.
