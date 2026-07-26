# ADR-028: Platform Integration and Architectural Language

## Status

Accepted

---

## Context

SentinelAI has completed a substantial constitutional cognitive
foundation.

The backend now includes established capabilities for:

- identity
- domains
- knowledge ingestion
- recall
- reflection
- reasoning
- deliberation
- governance
- operational awareness

The frontend already presents these capabilities as distinct
workspaces.

However, several workspaces remain disconnected from their backend
capabilities, and some user workflows are not yet operational.

The next development phase must connect SentinelAI's interface to its
existing cognitive architecture without introducing a separate or
incoherent frontend vocabulary.

The frontend must mirror the backend's architectural responsibilities,
constitutional language, and domain boundaries.

---

## Decision

SentinelAI shall begin a Platform Integration phase.

The objective of this phase is to connect the existing frontend
workspaces to the backend capabilities they represent.

Integration shall preserve one coherent architectural language across:

- backend modules
- API contracts
- frontend workspaces
- user actions
- status messages
- documentation

The frontend shall not create competing names for concepts already
defined by the backend.

Where a backend capability has canonical language, the frontend shall
use that language unless a human-centered presentation requires a
clearer label.

Any clearer presentation label must remain traceable to the canonical
backend concept.

---

## Architectural Principle

The frontend is the visible expression of the backend architecture.

The backend defines constitutional meaning.

The frontend communicates that meaning to the human.

The frontend may simplify presentation.

The frontend shall not alter responsibility.

---

## Integration Scope

The initial Platform Integration phase shall connect the following
capabilities:

### Teach

- document selection
- document upload
- domain assignment
- topic assignment
- optional description
- automatic classification suggestion
- human confirmation or override
- ingestion progress
- completion and error feedback
- mission history

### Domains

- available domain discovery
- domain status
- evidence-source counts
- active workspace selection
- domain-specific navigation
- domain-aware teaching actions

### Recall

- question submission
- selected-domain retrieval
- cross-domain retrieval when explicitly requested
- evidence display
- source attribution
- retrieval status

### Reason

- question submission
- reasoning input assembly
- validated reasoning output
- conclusion status
- uncertainty
- evidence traceability

### Intelligence

- knowledge patterns
- relationships
- domain-level summaries
- cross-domain discoveries
- knowledge analytics

### Governance

- constitutional health
- validator outcomes
- knowledge warnings
- architectural consistency
- human-agency safeguards

### Systems

- service health
- storage health
- vector-database health
- background-processing health
- model and collection status

---

## Domain Context

SentinelAI shall support an explicit active-domain context.

The active domain shall influence:

- teaching
- retrieval
- reasoning
- intelligence
- workspace navigation

The user may select:

- one specific domain
- all domains

Cross-domain operation must be explicit.

SentinelAI shall not silently mix unrelated domains when a specific
domain has been selected.

---

## Classification Authority

SentinelAI may suggest a domain and topic based on document content.

The human retains authority to:

- accept the suggestion
- override the suggestion
- assign the document manually
- place the document in General when uncertain

The final stored classification must distinguish between:

- automatic assignment
- human confirmation
- human override
- manual assignment

Classification may be automated.

Knowledge placement remains human-governed.

---

## Architectural Language Mapping

Every frontend workspace shall map to an existing backend
responsibility.

| Frontend Workspace | Backend Responsibility |
|---|---|
| Bridge | Operational awareness |
| Identity | Constitutional self-knowledge |
| Domains | Domain registry and domain state |
| Teach | Knowledge ingestion |
| Recall | Retrieval |
| Reason | Constitutional reasoning |
| Intelligence | Knowledge analytics and relationship discovery |
| Governance | Constitutional integrity |
| Systems | Platform and service operations |

This mapping shall remain explicit in architecture documentation and
implementation.

---

## Interface Language Rules

Frontend labels shall preserve the meaning of backend concepts.

Examples:

- `Teach` may present knowledge ingestion in human-centered language.
- `Recall` may present retrieval as asking what Sentinel remembers.
- `Reason` may present the Reasoning subsystem as evidence-based
  analysis.
- `Governance` may present constitutional validators and integrity
  checks as system health.
- `Systems` may present infrastructure and runtime state as platform
  operations.

Presentation language may be approachable.

Architectural meaning must remain unchanged.

---

## Responsibility Boundaries

### Frontend

The frontend may:

- collect user intent
- display system state
- communicate progress
- request backend operations
- present validated outputs
- preserve active domain context

The frontend shall never:

- perform classification as the source of truth
- invent knowledge metadata
- perform retrieval independently
- perform reasoning independently
- bypass validation
- convert recommendations into decisions

### Backend

The backend shall:

- receive explicit user intent
- apply constitutional services
- persist canonical metadata
- validate internal structures
- return traceable results
- preserve human authority

---

## API Contract Principle

API contracts shall use canonical backend field names.

Frontend adapters may translate those names into human-centered labels
for display.

The translation layer shall be explicit.

The frontend shall not require backend models to adopt presentation-only
terminology.

---

## Integration Sequence

The Platform Integration phase shall proceed in this order:

1. Establish shared domain context.
2. Connect the Teach upload workflow.
3. Persist document metadata and classification provenance.
4. Add ingestion progress and result feedback.
5. Connect domain-aware Recall.
6. Connect Reason to validated reasoning outputs.
7. Connect Intelligence analytics.
8. Connect Governance health and validator reports.
9. Connect Systems operational telemetry.
10. Exercise the complete workflow with a real Trading corpus.

---

## First End-to-End Mission

The first complete integration mission shall be:

```text
User selects Trading
        ↓
User uploads a document
        ↓
Sentinel suggests domain and topic
        ↓
Human confirms or overrides
        ↓
Backend ingests and indexes the document
        ↓
Trading evidence count increases
        ↓
Recall retrieves the document
        ↓
Reason uses the document as evidence
        ↓
Deliberation may reference the resulting conclusions
