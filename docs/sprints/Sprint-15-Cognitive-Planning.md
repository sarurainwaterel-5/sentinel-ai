# Sprint 15: Cognitive Planning

## Status

Completed

## Date Completed

2026-08-03

## Sprint Theme

From supported reasoning to structured action preparation.

---

## Objective

Design and implement SentinelAI's first cognitive planning faculty.

The faculty must transform evidence-supported reasoning into a
structured, inspectable, risk-aware plan without autonomously executing
actions.

---

## Mission Statement

> Teach Sentinel how to think ahead without allowing it to act ahead of
> human authority.

---

## Starting Point

At the beginning of Sprint 15, SentinelAI had a complete
evidence-grounded reasoning pipeline.

It could:

- retrieve knowledge;
- organize evidence;
- generate candidate inferences;
- calculate reasoning confidence;
- produce structured conclusions;
- communicate results;
- evaluate constitutional coherence;
- decline unsupported conclusions.

It could not yet transform a supported conclusion into a disciplined
course of action.

---

## Planning Definition

Sprint 15 defined planning as:

> The cognitive process of transforming a supported conclusion into an
> ordered, risk-aware sequence of recommended actions that advances a
> defined objective.

Planning was explicitly separated from:

- retrieval;
- reasoning;
- decision;
- execution;
- communication.

A plan is not a prediction.

A plan is a structured response to the best available understanding at a
specific point in time.

---

## Deliverables

### Public Planning Contracts

Created:

```text
backend/app/schemas/cognition/planning.py

The public contract exposes:

planning requests;
reasoning provenance;
strategy;
ordered steps;
dependencies;
assumptions;
constraints;
risks;
success criteria;
complexity;
planning confidence;
communication;
constitutional coherence;
source provenance;
workflow metadata.
Internal Planning Models

Created:

backend/app/services/cognition/planning/models.py

The internal planning language includes:

PlanningContext;
PlanningObjective;
PlanningReasoningBasis;
PlanningStrategy;
PlanningStep;
PlanningDependency;
PlanningAssumption;
PlanningRisk;
PlanningRiskAnalysis;
PlanningConfidence;
PlanningResult.

The planning graph validates all cross-references and sequencing.

It rejects:

duplicate step identifiers;
duplicate dependency identifiers;
duplicate risk identifiers;
unknown dependency references;
unknown risk references;
dependencies that reference unknown steps;
risks that reference unknown steps;
duplicate sequence values;
non-contiguous step sequences.
StrategyEngine

Implemented deterministic strategy candidate generation.

The engine:

generates bounded candidates;
evaluates explicit planning pressures;
ranks candidates deterministically;
selects the strongest supported strategy;
preserves rejected alternatives;
refuses strategy creation when reasoning is insufficient.

Initial strategies:

direct sequential;
phased verification-led;
clarification-first.

The engine does not generate steps.

StepDecomposer

Implemented deterministic strategy decomposition.

The decomposer produces:

ordered steps;
stable identifiers;
explicit rationales;
observable completion criteria;
human-approval requirements.

Step sequences begin at one and remain contiguous.

The decomposer does not select strategy, analyze risk, or execute work.

RiskAnalyzer

Implemented independent structural risk analysis.

The analyzer identifies:

dependencies;
assumptions;
reasoning-derived risks;
constraint risks;
structural risks;
mitigations;
contingencies;
unresolved conditions.

Risk analysis deliberately does not calculate planning confidence.

PlanningConfidenceEngine

Implemented explainable planning-confidence assessment.

Factors include:

reasoning strength;
strategy suitability;
step completeness;
dependency readiness;
human-approval coverage;
assumption burden;
risk exposure;
unresolved conditions.

Planning confidence remains distinct from reasoning confidence.

Reasoning confidence evaluates:

How strongly does evidence support the conclusion?

Planning confidence evaluates:

How viable and complete is the proposed plan?

PlanningEngine

Implemented the planning coordinator.

The engine sequences:

StrategyEngine
        ↓
StepDecomposer
        ↓
RiskAnalyzer
        ↓
PlanningConfidenceEngine
        ↓
PlanningResult

The engine handles:

supported planning;
insufficient reasoning;
blocked planning;
clarification-first planning.

The coordinator owns workflow, not specialist cognition.

PlanningFormatter

Implemented natural-language communication after cognition completes.

The formatter:

explains the authoritative plan;
preserves the selected strategy;
preserves step order;
preserves risk and confidence;
never implies execution;
uses deterministic fallback communication for unsupported plans.

The formatter may improve clarity.

It may not change cognition.

PlanningOrchestrator

Implemented complete planning workflow orchestration.

PlanningRequest
        ↓
Constitutional identity
        ↓
Knowledge retrieval
        ↓
ReasoningEngine
        ↓
PlanningContext
        ↓
PlanningEngine
        ↓
PlanningFormatter
        ↓
CoherenceEngine
        ↓
PlanningResponse

The orchestrator owns workflow and public-response mapping only.

It does not perform planning business logic.

Public Route

Created:

POST /cognition/plan

The route was registered successfully and appeared in OpenAPI.

The route remains thin:

PlanningRequest
        ↓
PlanningOrchestrator
        ↓
PlanningResponse
Architecture Documentation

Sprint 15 produced or established:

docs/architecture/cognitive/
├── COGNITIVE_ARCHITECTURE_DOCTRINE.md
└── COGNITIVE_SUBSYSTEM_TEMPLATE.md

These documents define:

the permanent cognitive design laws;
the repeatable construction lifecycle for future faculties.

The doctrine explains why Sentinel cognition is structured this way.

The construction template explains how new faculties are built
consistently.

Architecture Decision

Created:

docs/architecture/decisions/
└── ADR-027-COGNITIVE-PLANNING-FACULTY.md

The ADR records why Planning exists as a separate faculty and why it must
remain separate from Reasoning and Execution.

Major Decisions
Planning Is a Separate Faculty

Reasoning and planning answer different questions.

Reasoning asks:

What does the evidence support?

Planning asks:

Given that conclusion, what should happen next?

They remain independently testable and communicate through explicit
contracts.

Planning Does Not Execute

Every step represents a proposal.

No planning object claims that an action:

started;
completed;
succeeded;
invoked a tool;
changed an external system.

Human approval remains required.

Risk and Confidence Are Separate

RiskAnalyzer exposes structural uncertainty.

PlanningConfidenceEngine evaluates viability.

Neither owns both responsibilities.

This preserves single responsibility and explainability.

Public and Internal Models Remain Separate

Internal cognition may evolve without forcing public API changes.

The orchestrator acts as the translation boundary between:

Internal PlanningResult
        ↓
Public PlanningResponse
Planning Must Preserve Reasoning Provenance

Every plan contains a planning-safe reasoning basis.

A plan can be traced backward:

Step
    ↓
Strategy
    ↓
Reasoning conclusion
    ↓
Evidence

Planning may not silently replace, reinterpret, or bypass reasoning.

Insufficient Reasoning Produces No Plan

When the reasoner has no supported conclusion, the planner returns:

no strategy;
no steps;
zero planning confidence;
explicit insufficient-reasoning status;
deterministic communication.

Sentinel does not fabricate a plan merely because an objective was
submitted.

Communication Begins After Cognition

Planning is completed before natural-language formatting begins.

The formatter communicates the plan.

It does not create the plan.

Runtime and Contract Validation

Validated successfully:

public planning schema imports;
internal model construction;
graph-reference validation;
strategy candidate generation;
deterministic strategy ranking;
strongest-strategy selection;
rejected-alternative preservation;
insufficient-reasoning strategy behavior;
step decomposition;
contiguous sequence validation;
insufficient-reasoning step behavior;
dependency generation;
assumption preservation;
risk-to-step references;
mitigations and contingencies;
unresolved-condition generation;
planning-confidence score bounds;
explainable confidence factors;
insufficient-plan confidence behavior;
supported PlanningEngine branch;
insufficient-reasoning PlanningEngine branch;
supported PlanningFormatter branch;
deterministic formatter fallback;
PlanningOrchestrator import;
route compilation;
route registration in OpenAPI.
Bugs and Corrections
Incorrect Repository Path

Planning files were initially created under:

app/services/cognition/planning/

at the repository root.

The actual application lives under:

backend/app/

The orphaned top-level directory was identified and removed before
implementation continued.

Lesson:

Verify the active application root before creating subsystem files.

RiskAnalyzer Responsibility Expansion

The initial design risked making RiskAnalyzer responsible for both:

risk identification;
planning-confidence calculation.

The coupling was identified before implementation.

A dedicated:

PlanningConfidenceEngine

was introduced.

Lesson:

Related responsibilities are not necessarily the same responsibility.

Formatter Contract Clarification

The public schema already contained:

PlanningCommunicationSummary

A duplicate internal communication model would have blurred the API
boundary.

The formatter instead introduced:

FormattedPlanningResponse

inside the formatter module.

Lesson:

Inspect existing contracts before introducing parallel
representations.

Insufficient-Reasoning Branches Were Treated as First-Class Paths

The planning subsystem was not considered complete after the supported
branch passed.

The insufficient-reasoning branch was implemented and tested across:

strategy selection;
step decomposition;
planning confidence;
planning coordination;
formatter fallback.

Lesson:

A cognitive subsystem is not complete until it handles both supported
and unsupported states coherently.

Architectural Pattern Validated

Sprint 15 successfully reused the Cognitive Construction Template:

Language
    ↓
Public schemas
    ↓
Internal models
    ↓
Specialist engines
    ↓
Confidence engine
    ↓
Coordinator
    ↓
Formatter
    ↓
Orchestrator
    ↓
API
    ↓
Tests
    ↓
Documentation

Reasoning discovered the pattern.

Planning proved it was repeatable.

Cognitive Design Pattern Reinforced

Every cognitive subsystem follows these principles:

One engine owns one cognitive responsibility.
Engines communicate through structured contracts.
Cognitive processing flows in one direction.
Candidates are generated before selection.
Evaluation is deterministic and inspectable.
Confidence belongs to a dedicated assessment engine.
Communication begins only after cognition completes.
Orchestrators coordinate.
Engines think.
Humans retain authority over execution.
Lessons Learned
Architecture Should Lead Implementation

Sprint 15 progressed faster because the design grammar already existed.

The implementation instantiated the pattern instead of inventing it.

Contracts Reduce Integration Cost

Each specialist plugged into the next because inputs and outputs were
defined before behavior.

The architecture was already present.

The implementation followed it.

Alternate Branches Must Be First-Class

Supported planning and insufficient-reasoning planning were both tested.

A system is not complete when only its happy path works.

Documentation Is Part of Architecture

The doctrine and construction template ensure the pattern survives beyond
the engineers who originally created it.

Documentation is not an afterthought.

It is part of the cognitive platform.

Planning Confidence Is Not Outcome Certainty

The score measures structural viability and completeness.

It does not guarantee successful execution.

The Repeatable Structure Reduces Future Cost

The architecture now gives future faculties a known construction path.

New capabilities no longer begin with:

How should this entire subsystem be designed?

They begin with:

Which specialist engines does this faculty require?

That is a sign of foundational maturity.

Sprint Outcome

Sprint 15 transformed SentinelAI from a system that can reason into a
system that can also prepare structured courses of action.

Sentinel can now:

retrieve evidence;
reason about what that evidence supports;
preserve the reasoning basis;
generate strategy candidates;
evaluate and rank strategies;
select a supported strategy;
decompose the strategy into ordered steps;
expose dependencies and assumptions;
identify risks and contingencies;
calculate planning confidence;
communicate the plan clearly;
evaluate constitutional coherence;
refuse to plan when reasoning is insufficient.

Sentinel still does not execute actions.

That boundary is intentional.

Cognitive Architecture After Sprint 15
Knowledge
    ↓
Retrieval
    ↓
Evidence
    ↓
Reasoning
    ↓
Planning

This establishes the foundation for future:

Planning
    ↓
Decision
    ↓
Approval
    ↓
Execution
    ↓
Observation
    ↓
Reflection
    ↓
Learning
Recommended Next Faculty

The natural next capability is not immediate autonomous execution.

The next design question is:

Should a proposed plan be adopted, deferred, rejected, or returned for
clarification?

That responsibility belongs to a future Decision faculty.

Decision should evaluate:

policy;
trade-offs;
risk tolerance;
constitutional constraints;
approval requirements;
timing;
plan viability.

Execution should remain later and separate.

Deferred Work

The previously preserved Teach Experience sprint remains separate.

It includes:

asynchronous ingestion for large PDFs;
live mission timeline;
upload, extraction, chunking, embedding, indexing, and completion
states;
knowledge summaries;
connected recent teaching missions;
UI polish that makes Teach feel active and operational.

This work was not folded into Sprint 15.

Doctrine Compliance

Sprint 15 complies with the SentinelAI Cognitive Architecture Doctrine.

 One Responsibility Per Engine
 Structured Contracts
 Candidate Generation Before Selection
 Deterministic Cognition
 Explainable Outputs
 Dedicated Confidence Engine
 Formatter Separation
 Orchestrator Coordination
 Human Authority
 No Hidden Execution
 User-Safe Traces
 API Created Last
 Supported Branch Tested
 Insufficient Branch Tested
 Documentation Completed
 ADR Completed

Doctrine violations:

None.

Sprint Completion Criteria

Sprint 15 is complete when:

all planning files compile;
supported planning works;
insufficient-reasoning planning works;
the route is registered;
documentation is committed;
the milestone is pushed.
Lead Engineer Reflection

Sprint 14 taught Sentinel how to reason.

Sprint 15 taught Sentinel how to think ahead.

The most significant achievement was not the production of a list of
steps.

It was the creation of a planning faculty that remains:

evidence-aware;
reasoning-grounded;
deterministic;
risk-aware;
confidence-calibrated;
inspectable;
approval-gated;
non-executing.

Planning also validated that SentinelAI's cognitive architecture is now
repeatable.

Future faculties no longer begin with a blank architectural page.

They begin with:

a doctrine;
a construction template;
stable contracts;
two working reference implementations.

That is the point at which architecture becomes a platform.

Sprint 15 is accepted as SentinelAI's Cognitive Planning milestone.


