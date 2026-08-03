# SentinelAI Cognitive Planning Subsystem

## Architectural Foundation

This subsystem is implemented according to the:

- `docs/architecture/cognitive/COGNITIVE_ARCHITECTURE_DOCTRINE.md`
- `docs/architecture/cognitive/COGNITIVE_SUBSYSTEM_TEMPLATE.md`
- `docs/architecture/decisions/ADR-027-COGNITIVE-PLANNING-FACULTY.md`

Developers should review these documents before modifying the planning
subsystem.

---

## Purpose

The cognitive planning subsystem transforms an evidence-supported
reasoning conclusion into a structured, inspectable, risk-aware plan.

Planning answers:

> Given what the evidence supports, what proposed course of action best
> advances the objective?

Planning does not execute actions.

Planning does not replace reasoning.

Planning does not independently retrieve facts.

Planning does not silently invent assumptions.

---

## Cognitive Boundary

The planning subsystem begins after reasoning has produced an
authoritative `ReasoningResult`.

```text
Knowledge Retrieval
        ↓
Evidence-Grounded Reasoning
        ↓
PlanningContext
        ↓
Cognitive Planning
        ↓
PlanningResult

The subsystem consumes:

PlanningContext
├── objective
├── ReasoningResult
├── constraints
├── supplied assumptions
└── workflow metadata

The subsystem produces:

PlanningResult
├── objective
├── reasoning basis
├── selected strategy
├── ordered steps
├── dependencies
├── assumptions
├── constraints
├── risks
├── success criteria
├── complexity
├── planning confidence
├── planning trace
└── status
Architectural Principle

Planning recommends. Humans authorize.

Every proposed planning step remains non-executing and approval-gated.

The planning subsystem contains no tool invocation, autonomous action,
or hidden execution state.

Subsystem Structure
planning/
├── README.md
├── __init__.py
├── models.py
├── strategy_engine.py
├── step_decomposer.py
├── risk_analyzer.py
├── planning_confidence_engine.py
├── planning_engine.py
├── planning_formatter.py
└── planning_orchestrator.py
Cognitive Pipeline
PlanningContext
        ↓
StrategyEngine
        ↓
StepDecomposer
        ↓
RiskAnalyzer
        ↓
PlanningConfidenceEngine
        ↓
PlanningEngine
        ↓
PlanningFormatter
        ↓
PlanningOrchestrator
        ↓
PlanningResponse

Each component owns one responsibility.

Component Responsibilities
models.py

Defines the authoritative internal planning language.

Key contracts include:

PlanningContext
PlanningObjective
PlanningReasoningBasis
PlanningStrategy
PlanningStep
PlanningDependency
PlanningAssumption
PlanningRisk
PlanningRiskAnalysis
PlanningConfidence
PlanningResult

The model layer also validates the planning graph.

It ensures:

step identifiers are unique;
dependency identifiers are unique;
risk identifiers are unique;
references point to real objects;
step sequences begin at one;
step sequences remain contiguous.
strategy_engine.py

Generates, evaluates, ranks, and selects bounded strategy candidates.

Current domain-neutral candidates include:

direct sequential strategy;
phased verification-led strategy;
clarification-first strategy.

The engine preserves rejected alternatives and returns no strategy when
reasoning is insufficient.

It does not generate steps.

step_decomposer.py

Transforms one selected strategy into ordered, inspectable planning
steps.

Every step contains:

a stable identifier;
a contiguous sequence number;
title and description;
rationale;
completion criteria;
human-approval requirement.

It does not select strategy, analyze risk, or execute work.

risk_analyzer.py

Examines the proposed strategy and steps for structural planning
exposure.

It produces:

dependencies;
explicit assumptions;
risks;
mitigations;
contingencies;
unresolved conditions;
a user-safe analysis trace.

It does not calculate planning confidence.

planning_confidence_engine.py

Calculates explainable confidence in the viability and completeness of
the proposed plan.

Planning confidence considers:

reasoning strength;
strategy suitability;
step completeness;
dependency readiness;
assumption burden;
risk exposure;
unresolved conditions;
human-approval coverage.

Planning confidence is distinct from reasoning confidence.

Reasoning confidence measures support for a conclusion.

Planning confidence measures viability of a proposed course of action.

planning_engine.py

Coordinates the specialist planning engines.

Strategy selection
        ↓
Step decomposition
        ↓
Risk analysis
        ↓
Planning confidence
        ↓
PlanningResult

The engine owns coordination, not specialist logic.

It handles both:

supported planning;
insufficient-reasoning planning.
planning_formatter.py

Translates an authoritative PlanningResult into professional,
human-readable communication.

The formatter may improve clarity.

It may not:

change strategy;
add or reorder steps;
invent risks;
change confidence;
alter success criteria;
imply execution occurred.

Blocked or insufficient planning uses a deterministic fallback and does
not require an LLM call.

planning_orchestrator.py

Coordinates the complete public planning workflow.

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

The orchestrator owns sequencing and public-response mapping.

It contains no planning business logic.

Public API

The planning route is:

POST /cognition/plan

The route accepts a PlanningRequest and returns a PlanningResponse.

The public response separates:

readable communication;
authoritative planning;
reasoning provenance;
constitutional coherence;
source provenance;
workflow metadata.
Planning Statuses
complete

A supported strategy, ordered steps, risk analysis, and planning
confidence were produced.

insufficient_reasoning

Planning could not begin because no supported reasoning conclusion was
available.

blocked

A plan could not be completed or its viability fell below the required
structural threshold.

requires_clarification

The reasoning supports a direction, but significant planning uncertainty
must be resolved before detailed implementation should proceed.

Explainability

Every plan should support backward traceability:

Why does this step exist?
        ↓
Because of this strategy
        ↓
Selected from this reasoning basis
        ↓
Supported by this evidence

Planning traces expose high-level stages without revealing private
chain-of-thought.

Determinism

The specialist planning pipeline is deterministic.

Given identical structured inputs, the engines should produce identical:

strategy candidates;
strategy ranking;
step decomposition;
risk analysis;
planning confidence;
authoritative planning result.

Natural-language presentation may vary because it occurs after cognition
is complete.

Human Authority

Sprint 15 introduces planning only.

It does not introduce autonomous execution.

Every planning step defaults to requiring human approval.

Future execution capabilities must remain separate from planning and
must consume an explicitly approved plan through their own contracts.

Validation

Sprint 15 validated:

public planning schema imports;
internal planning model construction;
planning graph validation;
strategy ranking;
insufficient-reasoning strategy behavior;
step decomposition;
insufficient-reasoning step behavior;
risk-analysis references;
planning-confidence calculation;
insufficient-plan confidence behavior;
supported PlanningEngine behavior;
insufficient-reasoning PlanningEngine behavior;
supported formatter behavior;
deterministic formatter fallback;
orchestrator imports;
route registration in OpenAPI.
Extension Points

Future versions may add:

domain-specific strategy policies;
richer objective interpretation;
explicit public assumptions;
dependency graph ordering;
strategy comparison details;
domain-specific risk libraries;
dynamic success criteria;
planning evaluation benchmarks;
decision-layer review;
human approval workflows;
revision and replanning;
execution handoff contracts.

These extensions must preserve the Cognitive Architecture Doctrine.

Permanent Boundary

The planner may recommend action, but it may never claim that action
occurred.

Planning and execution remain separate cognitive and operational
faculties.
MD


## 2. Cognitive subsystem construction template

```bash
mkdir -p docs/architecture/cognitive

cat > docs/architecture/cognitive/COGNITIVE_SUBSYSTEM_TEMPLATE.md <<'MD'
# SentinelAI Cognitive Subsystem Construction Template

## Purpose

This document defines the standard construction lifecycle for every new
SentinelAI cognitive faculty.

It translates the Cognitive Architecture Doctrine into a repeatable
engineering process.

The doctrine explains why Sentinel cognition is structured this way.

This template explains how to build it consistently.

---

## Governing Principle

> Every new cognitive capability must first be expressed as a language
> and a structured contract before implementation begins.

A cognitive subsystem is not complete merely because its code works.

It must also be:

- understandable;
- inspectable;
- deterministic where appropriate;
- independently testable;
- constitutionally coherent;
- consistent with existing cognitive faculties.

---

# Phase 0 — Define the Language

Before creating files, define the cognitive faculty in plain language.

Answer:

1. What cognitive question does this faculty answer?
2. What structured input does it receive?
3. What authoritative output does it produce?
4. What responsibilities are explicitly excluded?
5. Where does it sit in the cognitive hierarchy?
6. Which existing faculty precedes it?
7. Which future faculty may consume its result?

Example:

```text
Reasoning asks:
What does the evidence support?

Planning asks:
Given what the evidence supports, what should happen next?

Decision asks:
Should the proposed plan be adopted?

Execution asks:
How is an approved decision carried out?

No implementation begins until the responsibility boundary is clear.

Phase 1 — Create the Package Structure

Use the canonical structure:

app/
├── schemas/
│   └── cognition/
│       └── <faculty>.py
│
└── services/
    └── cognition/
        └── <faculty>/
            ├── README.md
            ├── __init__.py
            ├── models.py
            ├── <specialist_1>.py
            ├── <specialist_2>.py
            ├── <faculty>_confidence_engine.py
            ├── <faculty>_engine.py
            ├── <faculty>_formatter.py
            └── <faculty>_orchestrator.py

Not every faculty requires the same number of specialists.

Every specialist must still own exactly one responsibility.

Phase 2 — Define Public Schemas

Create the public API contract before implementation.

The schema should separate:

request controls;
authoritative structured cognition;
communication;
confidence;
coherence;
source provenance;
workflow metadata.

Public schemas must not expose:

raw database objects;
Qdrant point models;
internal engine state;
hidden mutable state;
implementation-specific types.

Compile and import-test the schema before continuing.

Phase 3 — Define Internal Models

Internal models describe how the faculty represents cognition.

They may be richer than public API schemas.

Internal models should include:

structured input context;
intermediate cognitive objects;
confidence contracts;
final authoritative result;
status enumeration;
user-safe trace;
metadata;
cross-reference validation where applicable.

Internal cognition must not rely on anonymous dictionaries or tuples when
a stable domain contract is appropriate.

Compile and contract-test the models before continuing.

Phase 4 — Identify Specialist Engines

Break the faculty into independent cognitive responsibilities.

Examples:

Reasoning
├── EvidenceAnalyzer
├── InferenceEngine
└── ConfidenceEngine
Planning
├── StrategyEngine
├── StepDecomposer
├── RiskAnalyzer
└── PlanningConfidenceEngine

Each specialist must answer one question.

A specialist must not absorb responsibilities merely because related
information is available.

Phase 5 — Apply the Candidate Pattern

Whenever multiple valid outputs may exist, use the canonical cognitive
selection pattern:

Generate bounded candidates
        ↓
Evaluate against explicit criteria
        ↓
Rank deterministically
        ↓
Select the strongest supported result
        ↓
Preserve alternatives

Candidate selection must remain inspectable.

A missing supported candidate must produce an explicit empty or blocked
state rather than an invented result.

Phase 6 — Separate Confidence

Confidence must be produced by a dedicated assessment responsibility.

The confidence engine should:

consume structured contracts;
calculate bounded factors;
expose positive and negative contributions;
preserve uncertainty;
explain the final score;
avoid universal-certainty claims.

Confidence should not be copied directly from retrieval scores or
generated by an LLM.

Compile and test normal and insufficient-input branches.

Phase 7 — Build the Coordinator Engine

The faculty engine coordinates specialists.

It must not duplicate specialist logic.

Canonical pattern:

Structured context
        ↓
Specialist A
        ↓
Specialist B
        ↓
Confidence engine
        ↓
Authoritative result

The coordinator must handle unsupported or insufficient states explicitly.

Every coordinator requires tests for:

supported cognition;
insufficient input;
blocked cognition where applicable.
Phase 8 — Build the Formatter

Communication begins only after authoritative cognition is complete.

The formatter may:

improve clarity;
organize explanation;
adapt presentation.

The formatter may not:

change conclusions;
change strategies;
change confidence;
invent evidence;
invent assumptions;
remove limitations;
imply unperformed execution.

Incomplete cognition should use a deterministic fallback whenever an LLM
call is unnecessary.

Phase 9 — Build the Orchestrator

The orchestrator owns workflow and public-response assembly.

It may coordinate:

identity;
retrieval;
upstream cognition;
the current faculty;
formatter;
constitutional coherence;
response translation.

It must not perform the faculty’s cognitive work.

Canonical rule:

Orchestrators coordinate. Engines think. Formatters communicate.

Phase 10 — Expose the API

The API is created only after:

contracts exist;
specialist engines pass;
coordinator passes;
formatter passes;
orchestrator imports successfully.

The route should remain thin:

Request
    ↓
Orchestrator
    ↓
Response

Verify route registration through OpenAPI.

Phase 11 — Validate Incrementally

Every component follows:

Inspect sibling
    ↓
Understand contracts
    ↓
Implement one responsibility
    ↓
Compile
    ↓
Contract test
    ↓
Proceed

Required validation layers:

syntax compilation;
import test;
specialist contract test;
insufficient-input test;
coordinator integration test;
formatter supported test;
deterministic fallback test;
orchestrator import test;
API registration test;
end-to-end runtime test.

Compile success is not equivalent to runtime success.

Both normal and alternate branches must be exercised.

Phase 12 — Document the Subsystem

Every cognitive subsystem receives a README containing:

purpose;
cognitive question;
boundaries;
component responsibilities;
architecture diagram;
contracts;
statuses;
explainability model;
determinism expectations;
validation;
extension points.

Documentation is part of the deliverable.

Phase 13 — Review Architectural Decisions

Ask:

Did this subsystem introduce a durable architectural decision?

Write an ADR when the answer is yes.

An ADR should record:

context;
decision;
responsibilities;
alternatives considered;
consequences;
validation;
future implications;
doctrine compliance.

Do not create an ADR for routine implementation details.

Phase 14 — Doctrine Compliance Review

Before completion, verify:

 One responsibility per engine
 Structured contracts between components
 Deterministic cognition before communication
 Explicit insufficient-input behavior
 Candidate generation before selection where applicable
 Dedicated confidence assessment
 Formatter separated from cognition
 Orchestrator separated from cognition
 Human authority preserved
 No hidden execution
 User-safe traces only
 API created last
 Normal and alternate branches tested
 README completed
 ADR reviewed

Any violation must be resolved or explicitly approved through an ADR.

Phase 15 — Close the Sprint

A completed cognitive sprint ends with:

final compile sweep;
end-to-end validation;
subsystem README;
ADR where required;
sprint completion document;
clean milestone commit;
push to the remote repository.

The repository should be left in a clean, explainable state before the
next faculty begins.

Canonical Construction Sequence
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
Coordinator engine
    ↓
Formatter
    ↓
Orchestrator
    ↓
API
    ↓
Integration tests
    ↓
Documentation
    ↓
ADR review
    ↓
Commit
Permanent Objective

Every architectural decision should reduce the cost of adding future
cognitive capabilities.

The template exists so future faculties are composed from a proven
architectural grammar rather than invented from a blank page.
MD


## 3. ADR-027 — Cognitive Planning Faculty

```bash
mkdir -p docs/architecture/decisions

cat > docs/architecture/decisions/ADR-027-COGNITIVE-PLANNING-FACULTY.md <<'MD'
# ADR-027: Cognitive Planning Faculty

## Status

Accepted

## Date

2026-08-03

## Decision Owners

SentinelAI Architecture

---

## Context

Sprint 14 established SentinelAI's evidence-grounded reasoning pipeline.

That pipeline determines:

> What does the available evidence support?

Reasoning alone does not determine a course of action.

SentinelAI required a separate capability that could transform a
supported conclusion into an ordered, risk-aware, inspectable plan.

A design decision was required regarding whether planning should:

1. be added directly to the reasoning engine;
2. be generated entirely by an LLM;
3. be implemented as a separate cognitive faculty;
4. be combined immediately with autonomous execution.

Combining planning with reasoning would give one subsystem multiple
cognitive responsibilities.

Generating plans entirely through an LLM would reduce determinism,
inspectability, and confidence calibration.

Combining planning with execution would allow recommendations and actions
to become dangerously conflated.

SentinelAI therefore required a distinct planning faculty.

---

## Decision

SentinelAI adopts Cognitive Planning as an independent faculty positioned
after Reasoning and before any future Decision or Execution capability.

```text
Knowledge Retrieval
        ↓
Evidence-Grounded Reasoning
        ↓
Cognitive Planning
        ↓
Future Decision
        ↓
Future Approved Execution

Planning transforms an authoritative ReasoningResult into a structured
PlanningResult.

Planning recommends a course of action.

Planning does not execute it.

Definition

Planning is defined as:

The cognitive process of transforming a supported conclusion into an
ordered, risk-aware sequence of recommended actions that advances a
defined objective.

A plan is not a prediction.

A plan is a structured response to the best available understanding at a
specific point in time.

Architectural Structure

The planning faculty uses specialist engines:

PlanningContext
        ↓
StrategyEngine
        ↓
StepDecomposer
        ↓
RiskAnalyzer
        ↓
PlanningConfidenceEngine
        ↓
PlanningEngine
        ↓
PlanningFormatter
        ↓
PlanningOrchestrator
        ↓
PlanningResponse

Each component owns one responsibility.

Component Responsibilities
StrategyEngine
generates bounded strategy candidates;
evaluates explicit planning pressures;
ranks candidates deterministically;
selects the strongest supported strategy;
preserves rejected alternatives.

It does not generate steps.

StepDecomposer
transforms one strategy into ordered steps;
preserves rationale;
defines completion criteria;
requires human approval.

It does not analyze risk or execute work.

RiskAnalyzer
exposes dependencies;
preserves assumptions;
identifies structural and reasoning-derived risks;
provides mitigations and contingencies;
exposes unresolved conditions.

It does not calculate planning confidence.

PlanningConfidenceEngine
evaluates plan viability and completeness;
produces bounded factors;
explains positive and negative contributions;
preserves uncertainty.

It does not change the plan.

PlanningEngine
coordinates specialist engines;
produces the authoritative PlanningResult;
handles insufficient reasoning and blocked planning.

It does not absorb specialist responsibilities.

PlanningFormatter
translates a completed plan into readable communication;
uses deterministic fallbacks when no supported plan exists.

It does not modify authoritative cognition.

PlanningOrchestrator
coordinates identity, retrieval, reasoning, planning, formatting,
coherence, and public response mapping.

It does not plan.

Structured Contracts

The faculty communicates through explicit models.

Primary internal contracts include:

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

Primary public contracts include:

PlanningRequest;
PlanningReasoningBasisSummary;
PlanningStepSummary;
PlanningDependencySummary;
PlanningRiskSummary;
PlanningConfidenceSummary;
PlanningSummary;
PlanningCommunicationSummary;
PlanningResponse.
Reasoning and Planning Boundary

Reasoning determines whether evidence supports a conclusion.

Planning determines how an objective may be advanced given that
conclusion.

Planning may not silently replace, reinterpret, or bypass reasoning.

The boundary is:

ReasoningResult
        ↓
PlanningContext
        ↓
PlanningResult

If reasoning produces no supported conclusion, planning returns:

PlanningStatus.INSUFFICIENT_REASONING

with:

no strategy;
no steps;
zero planning confidence;
explicit uncertainty.
Planning and Execution Boundary

Planning steps represent proposed actions only.

They do not represent:

started actions;
completed actions;
successful actions;
tool invocations;
autonomous operations.

Every Sprint 15 step defaults to human approval.

Future execution must remain a separate subsystem and must consume an
explicitly approved plan.

Candidate Strategy Pattern

Strategy selection follows the cognitive candidate pattern:

Generate candidates
        ↓
Evaluate
        ↓
Rank
        ↓
Select
        ↓
Preserve alternatives

Initial domain-neutral strategies are:

direct sequential;
phased verification-led;
clarification-first.

Future domain strategy libraries may extend candidate generation without
changing the public planning contract.

Confidence Separation

Planning confidence is independent from reasoning confidence.

Reasoning confidence evaluates:

How strongly does evidence support the conclusion?

Planning confidence evaluates:

How viable and complete is the proposed plan?

Planning confidence uses reasoning confidence as one factor, but does not
copy it as the final score.

Plan Graph Integrity

PlanningResult validates the structural planning graph.

The model rejects:

duplicate step IDs;
duplicate dependency IDs;
duplicate risk IDs;
unknown dependency references;
unknown risk references;
dependencies referencing unknown steps;
risks referencing unknown steps;
duplicate sequence numbers;
non-contiguous step sequences.

This prevents disconnected planning lists from being accepted as a valid
plan.

Public API

Planning is exposed through:

POST /cognition/plan

The API returns structured planning, communication, coherence, source
provenance, and workflow metadata.

No response field represents completed execution.

Alternatives Considered
Add Planning to ReasoningEngine

Rejected.

Reasoning and planning answer different cognitive questions. Combining
them would violate single responsibility and make independent testing
more difficult.

LLM-Only Planning

Rejected.

An LLM-only planner would make strategy selection, step generation, and
confidence less deterministic and less inspectable.

Monolithic Planning Service

Rejected.

Combining strategy selection, decomposition, risk, confidence, formatting,
and orchestration would increase coupling and reduce extensibility.

Planning With Immediate Autonomous Execution

Rejected.

Recommendation and execution require separate governance, approval, and
safety boundaries.

Positive Consequences
reasoning and planning remain independently testable;
plans remain explainable;
unsupported reasoning produces no fabricated plan;
risk and confidence remain separate;
future domain strategies can be added cleanly;
future Decision can consume PlanningResult;
future Execution can require explicit approval;
the Cognitive Construction Template is validated by a second faculty.
Trade-offs

The design introduces more files, contracts, and mapping boundaries than
a monolithic planner.

This increases initial implementation effort.

The additional structure is accepted because it improves:

maintainability;
debugging;
testing;
explainability;
governance;
long-term extensibility.
Validation

Sprint 15 validated:

supported strategy generation;
insufficient-reasoning strategy behavior;
deterministic strategy ranking;
ordered step decomposition;
insufficient-reasoning step behavior;
valid risk references;
risk mitigations and contingencies;
explainable planning confidence;
insufficient-plan confidence;
supported PlanningEngine behavior;
insufficient-reasoning PlanningEngine behavior;
supported formatter behavior;
deterministic formatter fallback;
orchestrator imports;
route registration in OpenAPI.
Future Implications

This decision establishes the foundation for:

decision evaluation;
approval workflows;
plan revision;
replanning after new evidence;
execution handoff;
SRE operational planning;
incident-response planning;
engineering implementation plans;
trading preparation;
domain-specific strategy libraries;
multi-agent plan review.

Future faculties must consume the planning contract rather than reaching
into planning implementation details.

Doctrine Compliance

This decision complies with the SentinelAI Cognitive Architecture
Doctrine.

Affected principles:

 One Responsibility Per Engine
 Structured Contracts
 Candidate Generation Before Selection
 Deterministic Cognition
 Explainable Outputs
 Confidence Separation
 Formatter Separation
 Orchestrator Coordination
 Human Authority
 No Hidden Execution
 User-Safe Traces
 API Last

Doctrine violations:

None.

Final Principle

Reasoning determines what the evidence supports.

Planning determines what should happen next.

Humans retain authority over whether the plan is adopted or executed.
MD


## 4. Sprint 15 completion document

```bash
mkdir -p docs/sprints

cat > docs/sprints/SPRINT-015-COGNITIVE-PLANNING.md <<'MD'
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

---

## Deliverables

### Public Planning Contracts

Created:

```text
app/schemas/cognition/planning.py

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

app/services/cognition/planning/models.py

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

StrategyEngine

Implemented deterministic strategy candidate generation.

The engine:

generates bounded candidates;
evaluates explicit pressures;
ranks candidates;
selects the strongest supported strategy;
preserves rejected alternatives;
refuses strategy creation when reasoning is insufficient.

Initial strategies:

direct sequential;
phased verification-led;
clarification-first.
StepDecomposer

Implemented deterministic strategy decomposition.

The decomposer produces:

ordered steps;
stable identifiers;
rationales;
completion criteria;
human-approval requirements.

Step sequences begin at one and remain contiguous.

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
PlanningFormatter

Implemented natural-language communication after cognition completes.

The formatter:

explains the authoritative plan;
preserves strategy and step order;
preserves risk and confidence;
never implies execution;
uses deterministic fallback communication for unsupported plans.
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

The orchestrator owns workflow and public mapping only.

Public Route

Created:

POST /cognition/plan

The route was registered successfully and appeared in OpenAPI.
