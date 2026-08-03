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
