# ADR-010: Reasoning Orchestration

## Status

Accepted

## Context

SentinelAI reasoning will involve multiple layers:

- Identity
- Knowledge
- Mission context
- Coherence
- Prompt assembly
- Model response
- Reflection

Allowing each feature to reason independently would create inconsistency and duplicated logic.

## Decision

SentinelAI will use a dedicated Reasoning Orchestrator to coordinate reasoning workflows.

The orchestrator owns workflow, not business logic.

It delegates to specialized services.

## Consequences

- Reasoning becomes consistent across workspaces.
- Future legal, trading, engineering, and business intelligence features can share the same reasoning pipeline.
- The system becomes easier to test, explain, and extend.
