# ADR-009: Constitution as Code

## Status

Accepted

## Context

SentinelAI's Constitution should be reproducible, reviewable, and traceable.

Runtime memory should not become the source of truth.

## Decision

SentinelAI's Constitution will be treated as code.

Markdown documents in docs/ are the source of truth.

The Constitution Builder compiles these documents into the sentinel_core_memory Qdrant collection.

## Consequences

- The Constitution is version controlled through Git.
- Core Memory is a compiled artifact.
- The Constitution can be rebuilt at any time.
- Changes to SentinelAI's identity are reviewable and traceable.
