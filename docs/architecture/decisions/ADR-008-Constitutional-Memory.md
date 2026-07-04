# ADR-008: Constitutional Memory

## Status

Accepted

## Context

SentinelAI needs a protected identity layer that guides product, design, engineering, and reasoning decisions.

Normal uploaded knowledge should not be able to override SentinelAI's governing principles.

## Decision

SentinelAI will maintain a protected constitutional memory layer.

This layer contains:

- Vision
- Manifesto
- SentinelAI Principles
- Builder's Oath
- Engineering Principles
- Cognitive Design Principles
- Language Guide
- Architecture Decision Records

Constitutional Memory has higher precedence than normal domain knowledge.

## Consequences

- SentinelAI can reason from its own principles.
- Product and architecture recommendations become more consistent.
- Constitutional Memory must be rebuilt intentionally when source documents change.
