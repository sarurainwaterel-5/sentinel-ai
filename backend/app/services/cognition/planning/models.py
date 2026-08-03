"""
Structured contracts for SentinelAI's cognitive planning layer.

These models make the path from supported reasoning to a proposed course
of action explicit, inspectable, and reusable across operational domains.

Planning:

- receives completed reasoning,
- defines an objective,
- selects a strategy,
- decomposes work into ordered steps,
- identifies dependencies and assumptions,
- evaluates risks,
- defines measurable success,
- estimates planning confidence.

Planning does not execute actions.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import (
    BaseModel,
    Field,
    field_validator,
    model_validator,
)

from app.services.cognition.reasoning.models import (
    ReasoningResult,
)


class PlanningStatus(StrEnum):
    """
    Lifecycle state of one planning operation.
    """

    COMPLETE = "complete"
    INSUFFICIENT_REASONING = "insufficient_reasoning"
    BLOCKED = "blocked"
    REQUIRES_CLARIFICATION = "requires_clarification"


class PlanningComplexity(StrEnum):
    """
    Estimated cognitive and operational complexity of a plan.

    Complexity is not a duration estimate.
    """

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PlanningConfidenceLevel(StrEnum):
    """
    Human-readable confidence bands for planning viability.
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"


class RiskLevel(StrEnum):
    """
    Qualitative likelihood and impact levels for planning risks.
    """

    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PlanningStepStatus(StrEnum):
    """
    Non-execution state assigned to a proposed planning step.

    Sprint 15 produces plans only. Steps begin as proposed and are never
    automatically marked as executing or completed.
    """

    PROPOSED = "proposed"
    BLOCKED = "blocked"
    REQUIRES_APPROVAL = "requires_approval"


class PlanningContext(BaseModel):
    """
    Input boundary for one planning operation.

    The planner receives completed reasoning and explicit planning
    controls. It does not independently retrieve evidence or invent a
    new reasoning conclusion.
    """

    objective: str = Field(
        min_length=1,
        description="The outcome the proposed plan should achieve.",
    )

    reasoning_result: ReasoningResult = Field(
        description=(
            "The authoritative reasoning result that planning must use "
            "as its factual and evidentiary foundation."
        ),
    )

    constraints: list[str] = Field(
        default_factory=list,
    )

    supplied_assumptions: list[str] = Field(
        default_factory=list,
    )

    workspace: str | None = None
    module: str | None = None
    topic: str | None = None
    organization_id: str = "default"

    mission_id: str | None = None
    session_id: str | None = None

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @field_validator(
        "objective",
        "organization_id",
        mode="before",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: Any,
    ) -> Any:
        """
        Normalize required boundaries and reject whitespace-only values.
        """

        if not isinstance(value, str):
            return value

        normalized = value.strip()

        if not normalized:
            raise ValueError(
                "Value must not be empty."
            )

        return normalized

    @field_validator(
        "workspace",
        "module",
        "topic",
        "mission_id",
        "session_id",
        mode="before",
    )
    @classmethod
    def normalize_optional_text(
        cls,
        value: Any,
    ) -> Any:
        """
        Convert whitespace-only optional text to None.
        """

        if value is None or not isinstance(value, str):
            return value

        normalized = value.strip()

        return normalized or None


class PlanningReasoningBasis(BaseModel):
    """
    Planning-safe representation of the reasoning foundation.

    This model allows later planning components to inspect the conclusion,
    confidence, limitations, and evidence strength without depending on
    raw retrieval objects.
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

    domain_count: int = Field(
        default=0,
        ge=0,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )

    missing_information: list[str] = Field(
        default_factory=list,
    )


class PlanningObjective(BaseModel):
    """
    Structured interpretation of the desired outcome.

    An objective describes the intended result rather than the actions
    used to reach it.
    """

    statement: str = Field(
        min_length=1,
    )

    desired_outcome: str = Field(
        min_length=1,
    )

    scope: str | None = None

    success_conditions: list[str] = Field(
        default_factory=list,
    )

    constraints: list[str] = Field(
        default_factory=list,
    )


class PlanningStrategy(BaseModel):
    """
    High-level approach selected to achieve the planning objective.

    Strategy determines the direction of the plan. It does not contain
    the complete ordered sequence of work.
    """

    name: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    rationale: str = Field(
        min_length=1,
    )

    supported_by_reasoning: list[str] = Field(
        default_factory=list,
    )

    rejected_alternatives: list[str] = Field(
        default_factory=list,
    )

    suitability_score: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
    )


class PlanningDependency(BaseModel):
    """
    One prerequisite or ordering condition within a plan.
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

    verification_method: str | None = None

    satisfied: bool = False


class PlanningAssumption(BaseModel):
    """
    One condition accepted for planning purposes but not yet verified.

    Assumptions remain visible because a viable plan may become invalid
    when an important assumption proves false.
    """

    statement: str = Field(
        min_length=1,
    )

    justification: str = Field(
        min_length=1,
    )

    source: str | None = None

    verified: bool = False

    risk_if_false: str = Field(
        min_length=1,
    )


class PlanningRisk(BaseModel):
    """
    One potential event or condition that could obstruct the plan.

    Mitigation reduces likelihood or impact. Contingency describes what
    should happen if the risk actually occurs.
    """

    risk_id: str = Field(
        min_length=1,
    )

    description: str = Field(
        min_length=1,
    )

    likelihood: RiskLevel

    impact: RiskLevel

    affected_step_ids: list[str] = Field(
        default_factory=list,
    )

    mitigation: str | None = None

    contingency: str | None = None


class PlanningStep(BaseModel):
    """
    One discrete, ordered, inspectable recommendation within a plan.

    A planning step describes proposed action. It does not represent
    execution.
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

    status: PlanningStepStatus = (
        PlanningStepStatus.REQUIRES_APPROVAL
    )


class PlanningConfidenceFactor(BaseModel):
    """
    One explainable factor contributing to planning confidence.
    """

    name: str

    contribution: float = Field(
        ge=-1.0,
        le=1.0,
    )

    explanation: str


class PlanningConfidence(BaseModel):
    """
    Transparent assessment of plan viability and completeness.

    Planning confidence is distinct from reasoning confidence. Strong
    evidence may support a conclusion while the available constraints,
    assumptions, dependencies, or risks still produce a weak plan.
    """

    score: float = Field(
        ge=0.0,
        le=1.0,
    )

    level: PlanningConfidenceLevel

    basis: str

    factors: list[PlanningConfidenceFactor] = Field(
        default_factory=list,
    )

    uncertainty: list[str] = Field(
        default_factory=list,
    )

class PlanningRiskAnalysis(BaseModel):
    """
    Complete inspectable output of one planning-risk analysis.

    This model identifies structural planning exposure. It does not
    calculate overall planning confidence.
    """

    dependencies: list[PlanningDependency] = Field(
        default_factory=list,
    )

    assumptions: list[PlanningAssumption] = Field(
        default_factory=list,
    )

    risks: list[PlanningRisk] = Field(
        default_factory=list,
    )

    unresolved_conditions: list[str] = Field(
        default_factory=list,
    )

    analysis_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe risk-analysis stages. "
            "This is not private chain-of-thought."
        ),
    )


class PlanningResult(BaseModel):
    """
    Complete inspectable output of one planning operation.

    This is the authoritative internal planning result. A formatter may
    explain it, but may not alter its objective, strategy, steps, risks,
    confidence, or status.
    """

    objective: PlanningObjective

    reasoning_basis: PlanningReasoningBasis

    strategy: PlanningStrategy | None = None

    steps: list[PlanningStep] = Field(
        default_factory=list,
    )

    dependencies: list[PlanningDependency] = Field(
        default_factory=list,
    )

    assumptions: list[PlanningAssumption] = Field(
        default_factory=list,
    )

    constraints: list[str] = Field(
        default_factory=list,
    )

    risks: list[PlanningRisk] = Field(
        default_factory=list,
    )

    success_criteria: list[str] = Field(
        default_factory=list,
    )

    estimated_complexity: PlanningComplexity

    confidence: PlanningConfidence

    planning_trace: list[str] = Field(
        default_factory=list,
        description=(
            "High-level, user-safe planning stages. "
            "This is not private chain-of-thought."
        ),
    )

    status: PlanningStatus = PlanningStatus.COMPLETE

    metadata: dict[str, Any] = Field(
        default_factory=dict,
    )

    @model_validator(mode="after")
    def validate_plan_structure(
        self,
    ) -> "PlanningResult":
        """
        Validate identifiers and references across the plan.

        This ensures steps, dependencies, and risks form one coherent
        planning graph rather than disconnected lists.
        """

        step_ids = [
            step.step_id
            for step in self.steps
        ]

        dependency_ids = [
            dependency.dependency_id
            for dependency in self.dependencies
        ]

        risk_ids = [
            risk.risk_id
            for risk in self.risks
        ]

        if len(step_ids) != len(set(step_ids)):
            raise ValueError(
                "Planning step IDs must be unique."
            )

        if len(dependency_ids) != len(set(dependency_ids)):
            raise ValueError(
                "Planning dependency IDs must be unique."
            )

        if len(risk_ids) != len(set(risk_ids)):
            raise ValueError(
                "Planning risk IDs must be unique."
            )

        valid_step_ids = set(step_ids)
        valid_dependency_ids = set(dependency_ids)
        valid_risk_ids = set(risk_ids)

        for step in self.steps:
            unknown_dependencies = (
                set(step.dependency_ids)
                - valid_dependency_ids
            )

            if unknown_dependencies:
                raise ValueError(
                    f"Step '{step.step_id}' references unknown "
                    "dependency IDs: "
                    f"{sorted(unknown_dependencies)}"
                )

            unknown_risks = (
                set(step.risk_ids)
                - valid_risk_ids
            )

            if unknown_risks:
                raise ValueError(
                    f"Step '{step.step_id}' references unknown "
                    f"risk IDs: {sorted(unknown_risks)}"
                )

        for dependency in self.dependencies:
            unknown_steps = (
                set(
                    dependency.required_before_step_ids
                )
                - valid_step_ids
            )

            if unknown_steps:
                raise ValueError(
                    f"Dependency '{dependency.dependency_id}' "
                    "references unknown step IDs: "
                    f"{sorted(unknown_steps)}"
                )

        for risk in self.risks:
            unknown_steps = (
                set(risk.affected_step_ids)
                - valid_step_ids
            )

            if unknown_steps:
                raise ValueError(
                    f"Risk '{risk.risk_id}' references unknown "
                    f"step IDs: {sorted(unknown_steps)}"
                )

        sequences = [
            step.sequence
            for step in self.steps
        ]

        if len(sequences) != len(set(sequences)):
            raise ValueError(
                "Planning step sequence values must be unique."
            )

        if sequences:
            expected_sequences = list(
                range(
                    1,
                    len(sequences) + 1,
                )
            )

            if sorted(sequences) != expected_sequences:
                raise ValueError(
                    "Planning step sequence values must be "
                    "contiguous and begin at 1."
                )

        return self
