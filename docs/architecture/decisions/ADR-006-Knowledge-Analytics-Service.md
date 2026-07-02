# ADR-006: Introduce KnowledgeAnalyticsService

## Status
Accepted

## Date
2026-07-02

## Context

The Knowledge Dashboard requires aggregated statistics about the
knowledge base. Originally these responsibilities were beginning to
accumulate inside the KnowledgeManagementService.

This violated the Single Responsibility Principle and blurred the
distinction between lifecycle operations and analytics.

## Decision

Introduce a dedicated KnowledgeAnalyticsService responsible for:

- Dashboard statistics
- Knowledge metrics
- Recent document summaries
- Domain, topic, and collection analytics
- Future coverage analysis

KnowledgeManagementService will remain responsible only for lifecycle
operations such as:

- Upload
- Archive
- Restore
- Delete
- Re-index
- Versioning

## Consequences

### Positive

- Clear separation of concerns
- Easier maintenance
- Easier testing
- Cleaner service boundaries
- Microservice-ready architecture
- Dashboard logic isolated from lifecycle logic

### Future

This service will evolve to include:

- Knowledge coverage scoring
- AI classification metrics
- Usage analytics
- Organizational intelligence reporting
