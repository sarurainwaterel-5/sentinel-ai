# ADR-034 — Governed Persistent Reflection History

## Status

Accepted

## Date

2026-08-19

## Context

SentinelAI already possesses a Reflection architecture capable of examining accumulated Learning Events and producing bounded reflective cognition.

That capability alone is not sufficient for longitudinal intelligence.

If a Reflection exists only for the lifetime of a request or process, Sentinel cannot reliably examine:

- previous reflective conclusions,
- earlier confidence levels,
- prior constitutional judgments,
- historical insufficiency,
- conflicted cognitive outcomes,
- or changes in Reflection across time.

Reflection therefore requires durable historical preservation.

However, persistence introduces architectural risk.

If persistence is embedded inside cognitive faculties, storage concerns may acquire accidental cognitive authority.

If only successful or admissible Reflections are preserved, Sentinel develops survivorship bias.

If historical records can be updated or overwritten, later cognition can silently rewrite the evidence required to explain its own development.

SentinelAI therefore requires a governed, append-only, persistent Reflection history.

---

## Decision

SentinelAI SHALL preserve each completed governed Reflection as an immutable historical record.

Historical recording SHALL occur only after reflective cognition and constitutional evaluation have completed their independent judgments.

The accepted sequence is:

```text
Authoritative Learning Events
        ↓
Reflection Engine
        ↓
Reflection Confidence
        ↓
Constitutional Coherence
        ↓
GovernedReflectionResult
        ↓
ReflectionRecordFactory
        ↓
ReflectionRecord
        ↓
PersistentReflectionHistoryRepository
        ↓
Durable Storage

Persistence records cognitive outcomes.

Persistence does not determine cognitive outcomes.

Decision Principles
1. Reflection History Is Append-Only

A historical Reflection represents what Sentinel concluded at a specific moment.

Later cognition may:

examine it,
challenge it,
supersede it,
identify weakness,
identify conflict,
or produce a revised Reflection.

Later cognition SHALL NOT silently modify the earlier record.

Present understanding may change without falsifying intellectual history.

2. All Reflection Outcomes Are Historical Evidence

Reflection history SHALL preserve outcomes regardless of apparent success.

This includes:

COMPLETE
INSUFFICIENT_EVIDENCE
LIMITED
CONFLICTED
CONSTITUTIONALLY_INADMISSIBLE

A weak or rejected Reflection remains evidence of Sentinel's historical cognitive state.

This prevents survivorship bias.

3. Confidence and Constitutional Judgment Remain Independent

Reflection confidence and constitutional admissibility are separate authorities.

A historical record may therefore preserve combinations such as:

confidence = low
admissible = true

or:

confidence = high
admissible = false

Persistence SHALL preserve these judgments exactly as produced.

Persistence SHALL NOT merge, reinterpret, or recalculate them.

4. Historical Memory Grants No Execution Authority

Persisted cognition is evidence.

It is not permission to act.

The following principle remains invariant:

Constitutional admissibility does not grant execution authority.

Recommendations preserved in historical Reflection remain subject to their existing human-approval and execution boundaries.

ReflectionRecord

ReflectionRecord is the canonical historical representation of one governed Reflection.

It preserves:

reflection_id
mission_id
session_id
organization_id
reflected_at
learning_event_ids
pattern_ids
insight_ids
recommendation_ids
Reflection status
Reflection confidence score
Reflection confidence level
constitutional coherence
constitutional score
admissibility
longitudinal Understanding provenance
reflective trends

The record is a representation of completed cognition.

It is not a new cognitive judgment.

ReflectionRecordFactory

Transformation from governed cognition to historical representation belongs to ReflectionRecordFactory.

The factory may:

extract identifiers,
preserve provenance,
preserve confidence,
preserve constitutional judgment,
preserve mission context,
preserve longitudinal metadata.

The factory SHALL NOT:

perform Reflection,
recalculate confidence,
evaluate constitutional coherence,
alter admissibility,
persist records,
repair cognition,
execute Recommendations.

Its responsibility is faithful representation transfer.

Repository Boundary

Reflection persistence SHALL occur through a repository boundary.

Repository implementations are responsible for:

append-only storage,
identity preservation,
retrieval,
mission-scoped history,
organization-scoped history,
chronological retrieval,
defensive historical snapshots.

Repositories SHALL NOT expose authority to:

update,
overwrite,
rewrite,
repair,
delete,
or execute historical cognition.

Storage does not become cognition merely because it stores cognition.

Persistent Repository

Production Reflection history uses SentinelAI's SQLAlchemy persistence architecture.

The production adapter is:

PersistentReflectionHistoryRepository

It receives a request-scoped SQLAlchemy Session and persists historical records into:

reflection_history

A persisted Reflection SHALL remain recoverable through:

Session A
    ↓
save ReflectionRecord
    ↓
database
    ↓
Session A closes


Session B
    ↓
new repository
    ↓
recover same ReflectionRecord

This establishes runtime-independent historical memory.

Schema Management

Persistent cognitive memory must be reproducible from source control.

The Reflection history schema SHALL therefore be managed through Alembic.

Accepted migration lineage:

28753b490a74
        ↓
01620884d63e
        ↓
HEAD

Revision:

01620884d63e — create reflection history table

The migration must support:

empty database
    ↓
upgrade head
    ↓
reflection_history exists
    ↓
downgrade base
    ↓
reflection_history removed
    ↓
upgrade head
    ↓
reflection_history recreated
Application Integration Boundary

Automatic historical recording belongs to ReflectionApplicationService.

This boundary was selected because it already coordinates the application workflow without owning reflective cognition.

The accepted sequence is:

ReflectionApplicationService
        │
        ├── resolve authoritative Learning Events
        │
        ├── request governed Reflection
        │
        ├── create ReflectionRecord
        │
        ├── persist ReflectionRecord
        │
        ├── format governed Reflection
        │
        └── return public response

Historical persistence SHALL NOT be embedded in:

ReflectionEngine
ReflectionCoherenceEvaluator
HTTP route logic

This preserves separation between cognition, governance, infrastructure, and transport.

HTTP Boundary

The Reflection HTTP route owns transport only.

The route may:

accept ReflectionAPIRequest,
obtain a request-scoped database Session,
compose application dependencies,
delegate to ReflectionApplicationService,
return ReflectionAPIResponse.

The route SHALL NOT own:

Reflection logic,
confidence calculation,
constitutional evaluation,
historical transformation,
persistence semantics,
execution.
Learning History vs Reflection History

SentinelAI distinguishes two forms of cognitive history.

Learning History
    "How did understanding change?"


Reflection History
    "What did Sentinel conclude when examining that change?"

Neither replaces the other.

Together they support longitudinal cognitive accountability.

Longitudinal Implications

Persistent Reflection history enables future faculties to examine:

changes in reflective confidence,
changes in discovered Patterns,
changes in Insights,
changes in Recommendations,
repeated insufficiency,
constitutional disagreement,
changes in reflective trend,
Reflection upon prior Reflection.

Previous Reflection records SHALL be treated as historical evidence, not unquestionable truth.

Rejected Alternatives
Store Only Successful Reflection

Rejected.

This would introduce survivorship bias and remove evidence needed to understand cognitive failure, uncertainty, and revision.

Rewrite Earlier Reflection

Rejected.

Mutating prior Reflection would destroy intellectual provenance.

New cognition must supersede prior cognition through new records, not modification.

Persist Inside ReflectionEngine

Rejected.

ReflectionEngine owns reflective cognition.

Persistence is infrastructure.

Combining them would violate SentinelAI's separation-of-responsibility doctrine.

Persist Directly in the HTTP Route

Rejected.

HTTP is transport.

Persistence must remain available to future non-HTTP interfaces such as:

CLI missions,
workers,
internal orchestration,
background cognition,
future Teach workflows.
Allow an LLM to Define Historical Truth

Rejected.

An LLM may later contribute semantic interpretation under explicit governance.

It SHALL NOT define which historical cognitive records exist or rewrite their provenance.

Historical identity remains deterministic system responsibility.

Consequences
Positive

This decision gives SentinelAI:

durable reflective memory,
longitudinal cognitive accountability,
preserved uncertainty,
preserved failed Reflection,
preserved constitutional disagreement,
reproducible persistence schema,
cross-session historical recovery,
a foundation for Reflection upon Reflection.
Costs

This decision introduces:

additional domain models,
repository complexity,
schema migration responsibility,
historical identity management,
provenance requirements,
additional integration testing.

These costs are accepted because durable intellectual history is required for longitudinal cognition.

Validation

Sprint 18 validated this architecture with:

318 backend tests passed
2 non-blocking warnings

Reflection HTTP boundary:

6 passed

Live production-path persistence verification:

POST /reflection
        ↓
governed Reflection
        ↓
ReflectionRecord creation
        ↓
PostgreSQL persistence
        ↓
request completed
        ↓
new database Session
        ↓
FOUND 1 REFLECTION RECORD

This confirmed that Reflection survives the original request and remains recoverable in a later runtime context.

Related Architecture

This decision extends:

ADR-023 — Learning Recorder and Cognitive Memory
ADR-024 — Reflection Architecture
ADR-025 — Constitutional Subsystem Pattern
ADR-031 — Unified Memory Architecture
ADR-032 — Structured Intelligence Contracts

It does not replace them.

Architectural Invariants

The following invariants are now permanent unless formally amended:

Historical Reflection is append-only.
Weak and rejected Reflection is preserved.
Persistence occurs after cognition and constitutional evaluation.
Persistence does not create cognitive authority.
Confidence and constitutional admissibility remain separate.
Historical memory grants no execution authority.
Reflection history must remain recoverable across runtime boundaries.
Historical schemas must be reproducible from source-controlled migrations.
New cognition supersedes old cognition through new records, never silent rewriting.
Prior Reflection is evidence for future Reflection, not unquestionable truth.
Capability Earned

SentinelAI can now preserve governed Reflection as durable historical evidence without allowing persistence to acquire cognitive, constitutional, or execution authority.

This enables Sentinel to eventually answer not only:

What have I learned?

but also:

What did I previously conclude about what I had learned, and how has that reflective judgment changed over time?
