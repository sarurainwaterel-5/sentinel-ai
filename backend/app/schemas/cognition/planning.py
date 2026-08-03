"""
Public API contracts for SentinelAI's cognitive planning subsystem.

These schemas separate:

- planning objectives and retrieval controls,
- authoritative structured plans,
- reasoning provenance,
- human-readable communication,
- constitutional coherence,
- workflow metadata.

The internal planning models remain owned by the planning subsystem.
These API schemas expose a stable, consumer-friendly representation.

Planning recommends a course of action.

Planning does not execute actions.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


class PlanningRequest(BaseModel):
    """
    Request one evidence-aware planning operation.

    The objective identifies the desired outcome.

    Sentinel may use the objective to retrieve relevant knowledge and
    produce reasoning before constructing a plan. API consumers remain
    decoupled from Qdrant and the internal planning implementation.
    """

    objective: str = Field(
        min_length=1,
        description="The outcome Sentinel should create a plan to achieve.",
    )

    workspace: str = Field(
        default="bridge",
        min_length=1,
        description=(
            "The cognitive workspace initiating the planning operation."
        ),
    )

    module: str | None = Field(
        default=None,
        description=(
            "Optional knowledge-module filter, such as engineering, "
            "trading, sre, or incident_response."
        ),
    )

    topic: str | None = Field(
        default=None,
        description="Optional topic filter within the selected module.",
    )

    organization_id: str = Field(
        default="default",
        min_length=1,
        description="Organization boundary used during knowledge retrieval.",
    )

    limit: int = Field(
        default=5,
        ge=1,
        le=25,
        description="Maximum number of knowledge chunks to retrieve.",
    )

    score_threshold: float = Field(
        default=0.45,
        ge=0.0,
        le=1.0,
        description=(
            "Minimum semantic similarity score accepted during retrieval."
        ),
    )

    constraints: list[str] = Field(
        default_factory=list,
        description=(
            "Known limitations the plan must respect, such as time, "
            "budget, policy, safety, or operational boundaries."
        ),
    )

    mission_id: str | None = Field(
        default=None,
        description="Optional teaching or operational mission identifier.",
    )

    session_id: str | None = Field(
        default=None,
        description="Optional conversation or planning-session identifier.",
    )

    @field_validator(
        "objective",
        "workspace",
        "organization_id",
        mode="before",
    )
    @classmethod
    def normalize_required_text(cls, value: Any) -> Any:
        """
        Reject whitespace-only required values and normalize boundaries.
        """

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        if not normalized:
            raise ValueError("Value must not be empty.")

        return normalized

    @field_validator(
        "module",
        "topic",
        "mission_id",
        "session_id",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(cls, value: Any) -> Any:
        """
        Normalize optional text and convert whitespace-only values to None.
        """

        if value is None or not isinstance(value, str):
            return value

        normalized = value.strip()

        return normalized or None

    @field_validator(
        "constraints",
        mode="before",
    )
    @classmethod
    def normalize_constraints(cls, value: Any) -> Any:
        """
        Normalize constraint text and remove blank entries.

        Pydantic will perform final list validation after this boundary.
        """

        if value is None:
            return []

        if not isinstance(value, list):
            return value

        normalized: list[Any] = []

        for item in value:
            if not isinstance(item, str):
                normalized.append(item)
                continue

            cleaned = item.strip()

            if cleaned:
                normalized.append(cleaned)

        return normalized


class PlanningConfidenceSummary(BaseModel):
    """
    Consumer-facing confidence in the proposed plan.

    Planning confidence evaluates the strength and completeness of the
    proposed approach. It is distinct from confidence in the reasoning
    conclusion that preceded planning.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: str

    basis: str

    factors: list[dict[str, Any]] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )


class PlanningReasoningBasisSummary(BaseModel):
    """
    Authoritative reasoning basis supplied to the planning subsystem.

    This preserves the path from evidence to conclusion to plan without
    exposing internal reasoning implementation details.
    """

    question: str

    conclusion: str | None = None

    confidence_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )

    confidence_level: str = "low"

    reasoning_status: str

    evidence_source_count: int = Field(
        default=0,
        ge=0,
    )

    document_count: int = Field(
        default=0,
        ge=0,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )


class PlanningDependencySummary(BaseModel):
    """
    A condition or prerequisite required by one or more planning steps.
    """

    dependency_id: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    required_before_step_ids: list[str] = Field(
        default_factory=list,
    )

    satisfied: bool = False

    verification_method: str | None = None


class PlanningRiskSummary(BaseModel):
    """
    A potential event or condition that could obstruct the plan.

    Every identified risk should include a mitigation whenever one can
    be responsibly recommended.
    """

    risk_id: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    likelihood: str

    impact: str

    mitigation: str | None = None

    affected_step_ids: list[str] = Field(
        default_factory=list,
    )


class PlanningStepSummary(BaseModel):
    """
    One discrete, ordered, and inspectable planning step.

    A step recommends an action but does not execute it.
    """

    step_id: str = Field(
        min_length=1,
    )

    sequence: int = Field(
        ge=1,
    )

    title: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    rationale: str = Field(
        min_length=1,
        description=(
            "Why this step exists and how it advances the objective."
        ),
    )

    dependency_ids: list[str] = Field(
        default_factory=list,
    )

    risk_ids: list[str] = Field(
        default_factory=list,
    )

    completion_criteria: list[str] = Field(
        default_factory=list,
    )

    requires_human_approval: bool = True


class PlanningSummary(BaseModel):
    """
    Authoritative structured plan produced by Sentinel's planning core.

    This section is machine-readable and does not require downstream
    consumers to parse the human-readable planning narrative.
    """

    objective: str

    reasoning_basis: PlanningReasoningBasisSummary

    strategy: str | None = None

    strategy_rationale: str | None = None

    steps: list[PlanningStepSummary] = Field(
        default_factory=list,
    )

    dependencies: list[PlanningDependencySummary] = Field(
        default_factory=list,
    )

    assumptions: list[str] = Field(
        default_factory=list,
    )

    constraints: list[str] = Field(
        default_factory=list,
    )

    risks: list[PlanningRiskSummary] = Field(
        default_factory=list,
    )

    success_criteria: list[str] = Field(
        default_factory=list,
    )

    estimated_complexity: str

    confidence: PlanningConfidenceSummary

    planning_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe planning stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: str


class PlanningCommunicationSummary(BaseModel):
    """
    Human-readable presentation generated after planning is complete.

    These fields may improve clarity but may not change the authoritative
    strategy, steps, dependencies, risks, confidence, or success criteria.
    """

    answer: str

    strategy_explanation: str

    steps_explanation: str

    risk_explanation: str

    success_explanation: str


class PlanningCoherenceResult(BaseModel):
    """
    Constitutional coherence evaluation for a proposed plan.

    Coherence remains independent from planning confidence.
    """

    coherent: bool

    constitutional_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    articles_consulted: list[str] = Field(
        default_factory=list,
    )

    conflicts: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class PlanningResponse(BaseModel):
    """
    Final public response from Sentinel's cognitive planning pipeline.

    The response preserves clear boundaries between:

    - planning communication,
    - the authoritative structured plan,
    - reasoning provenance,
    - constitutional coherence,
    - workflow metadata.

    No field in this response represents completed execution.
    """

    answer: str

    communication: PlanningCommunicationSummary

    planning: PlanningSummary

    coherence: PlanningCoherenceResult

    constitutional_sources: list[str] = Field(
        default_factory=list,
    )

    knowledge_sources: list[str] = Field(
        default_factory=list,
    )

    workspace: str

    module: str | None = None

    topic: str | None = None

    organization_id: str = "default"

    mission_id: str | None = None

    session_id: str | None = None
