ADR-026
Title

Cognitive Orchestration Pipeline

Status

Accepted

Date

2026-07-29

Context

Prior to Sprint 14, SentinelAI consisted of several independent cognitive components:

Constitutional identity
Retrieval service
Reasoning engine
Confidence assessment
LLM formatter
Coherence engine

Although each subsystem functioned independently, there was no single component responsible for coordinating the complete reasoning workflow.

Additionally, earlier implementations allowed reasoning, communication, and orchestration responsibilities to become intertwined, increasing coupling and making future evolution more difficult.

A unified orchestration model was required.

Decision

SentinelAI adopts a dedicated Reasoning Orchestrator responsible solely for coordinating the cognitive workflow.

The orchestrator owns sequencing but owns no business logic.

The complete workflow becomes:

Request
    ↓
Constitutional Identity
    ↓
Knowledge Retrieval
    ↓
Evidence Organization
    ↓
Deterministic Reasoning
    ↓
Confidence Assessment
    ↓
Communication Formatting
    ↓
Constitutional Coherence
    ↓
Reasoning Response

Component Responsibilities
Constitutional Reasoning Service

Responsible for:

identity context
constitutional articles
governance guidance

Never performs retrieval or inference.

Retrieval Service

Responsible for:

document retrieval
hybrid search
filtering
ranking

Never generates conclusions.

Reasoning Engine

Responsible for:

evidence organization
inference generation
confidence calculation
reasoning trace

Never communicates directly with users.

LLM Formatter

Responsible for:

translating structured reasoning into natural language
preserving reasoning fidelity
explaining evidence
explaining confidence

Never modifies reasoning.

Coherence Engine

Responsible for:

constitutional validation
conflict detection
coherence scoring

Never changes reasoning conclusions.

Reasoning Orchestrator

Responsible for:

workflow sequencing
component coordination
response assembly

Owns no reasoning logic.

Design Principles
Separation of Concerns

Each subsystem performs exactly one cognitive responsibility.

Deterministic Reasoning

Reasoning is generated from structured evidence.

Language generation does not determine conclusions.

Evidence Before Conclusions

No conclusion may exist without supporting evidence.

Confidence Before Communication

Confidence is computed before any natural-language explanation.

Communication reflects confidence rather than creating it.

Constitutional Governance

All reasoning is evaluated against SentinelAI's constitutional framework before being returned.

Graceful Failure

If sufficient evidence cannot be established:

no conclusion is generated
uncertainty is communicated
confidence remains low
hallucination is prevented
Consequences
Positive
Strong separation of responsibilities
Independent subsystem evolution
Easier testing
Easier debugging
Lower coupling
Improved maintainability
Reduced hallucination risk
Explicit uncertainty handling
Trade-offs

The orchestration pipeline introduces additional component boundaries and object transformations.

This slightly increases implementation complexity but significantly improves long-term maintainability and architectural clarity.

Validation

Sprint 14 validated both primary execution paths.

Supported Evidence

Verified:

retrieval
inference
confidence
communication
coherence
API serialization

Result:

Successful structured reasoning response.

Insufficient Evidence

Verified:

absence of conclusion
low confidence
structured uncertainty
graceful response generation

Result:

No unsupported conclusions produced.

Alternatives Considered
LLM-Centric Reasoning

Rejected.

Reasoning generated directly by the language model makes confidence difficult to calibrate and reduces determinism.

Retrieval-Only Pipeline

Rejected.

Retrieval without structured inference cannot distinguish between available information and supported conclusions.

Monolithic Cognitive Service

Rejected.

Combining retrieval, inference, formatting, and orchestration into a single component increases coupling and reduces maintainability.

Future Implications

This decision establishes the architectural foundation for:

Multi-agent cognition
Planning systems
Hypothesis evaluation
Long-term memory
Autonomous workflows
Trading intelligence
Incident response reasoning
Cross-domain cognitive orchestration

All future cognitive capabilities should integrate through the Reasoning Orchestrator while preserving the separation of responsibilities defined in this ADR.

ADR-026 establishes how SentinelAI thinks. From here on, every advanced capability—planning, agents, or trading cognition—can plug into this orchestration model instead of inventing its own reasoning flow.
