# ADR-033 — Domain Knowledge Ingestion

Status

Accepted

Date

Sprint 13.2

---

## Context

Teach originally performed synchronous document ingestion.

Knowledge assets are now organized into operational domains.

Each document contributes to a specific operational workspace.

---

## Decision

Knowledge ingestion becomes domain-first.

Every uploaded document belongs to a single operational domain.

Examples

Engineering

Trading

Law

Incident Response

Finance

Identity

Future ingestion will execute as asynchronous knowledge missions.

---

## Consequences

Benefits

• Domain-aware retrieval

• Reduced retrieval noise

• Operational workspaces

• Future cross-domain reasoning

• Knowledge lifecycle management

Future Work

Teach Mission Queue

Mission Timeline

Knowledge Summary

Recent Missions

Background Processing

---

## Result

Sentinel evolves from document storage into operational knowledge acquisition.
