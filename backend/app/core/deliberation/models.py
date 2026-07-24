"""
Deliberation Models

Deliberation Models represent the constitutional structures required
to compare responsible possibilities while preserving human agency,
restraint, and accountability to reality.

Models define structure.

Models never evaluate options.

Models never select recommendations.

Models never replace human judgment.
"""

from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from app.core.deliberation.language import (
    BenefitLevel,
    ConstraintStatus,
    OptionStatus,
    RecommendationStatus,
    RestraintStatus,
    ReversibilityStatus,
    RiskLevel,
)


@dataclass(slots=True)
class Possibility:
    """
    A candidate path that may be considered before formal deliberation.

    A Possibility is not yet an admitted Option.
    """

    possibility_id: str
    title: str
    description: str

    intended_outcome: str = ""

    conclusion_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    uncertainty: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Option:
    """
    A sufficiently structured Possibility admitted into formal deliberation.

    Admission does not imply preference or constitutional acceptability.
    """

    option_id: str
    possibility_id: str
    title: str
    description: str
    status: OptionStatus = "candidate"

    intended_outcome: str = ""
    required_conditions: list[str] = field(default_factory=list)

    conclusion_ids: list[str] = field(default_factory=list)
    assumption_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    value_ids: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    uncertainty: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Value:
    """
    A quality that should be preserved, protected, or advanced.

    Values guide deliberation without replacing evidence.
    """

    value_id: str
    name: str
    description: str

    principle_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    priority: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Constraint:
    """
    A boundary an Option must respect to remain constitutionally acceptable.
    """

    constraint_id: str
    name: str
    description: str
    status: ConstraintStatus = "unresolved"

    source: str = ""
    required: bool = True

    option_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Consequence:
    """
    An intended or foreseeable effect of selecting, rejecting, or delaying
    an Option.
    """

    consequence_id: str
    option_id: str
    description: str

    consequence_type: str = "foreseeable"
    timeframe: str = ""
    affected_parties: list[str] = field(default_factory=list)

    severity: RiskLevel | None = None
    reversibility: ReversibilityStatus = "unknown"

    evidence_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RiskAssessment:
    """
    A structured evaluation of an unwanted consequence associated with
    an Option.
    """

    risk_assessment_id: str
    option_id: str
    title: str
    explanation: str
    level: RiskLevel

    likelihood: float | None = None
    severity: RiskLevel = "unknown"
    exposure: str = ""
    detectability: str = ""
    reversibility: ReversibilityStatus = "unknown"

    consequence_ids: list[str] = field(default_factory=list)
    safeguard_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)

    uncertainty: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class BenefitAssessment:
    """
    A structured evaluation of a reasonably supported positive consequence
    associated with an Option.
    """

    benefit_assessment_id: str
    option_id: str
    title: str
    explanation: str
    level: BenefitLevel

    likelihood: float | None = None

    consequence_ids: list[str] = field(default_factory=list)
    evidence_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)
    value_ids: list[str] = field(default_factory=list)

    uncertainty: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Tradeoff:
    """
    A visible exchange between responsible qualities, outcomes, risks,
    benefits, or values.
    """

    tradeoff_id: str
    option_id: str
    description: str

    gains: list[str] = field(default_factory=list)
    losses: list[str] = field(default_factory=list)
    affected_parties: list[str] = field(default_factory=list)

    value_ids: list[str] = field(default_factory=list)
    risk_assessment_ids: list[str] = field(default_factory=list)
    benefit_assessment_ids: list[str] = field(default_factory=list)

    reversible: bool | None = None
    uncertainty: str = ""

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class ProportionalityAssessment:
    """
    An assessment of whether an Option's scope and risk are appropriate to
    the evidence, need, authority, and expected benefit.
    """

    proportionality_assessment_id: str
    option_id: str
    proportionate: bool | None
    explanation: str

    risk_assessment_ids: list[str] = field(default_factory=list)
    benefit_assessment_ids: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class RestraintAssessment:
    """
    A determination of whether action should proceed, pause, gather more
    evidence, defer to human authority, or not occur.
    """

    restraint_assessment_id: str
    option_id: str
    status: RestraintStatus
    explanation: str

    evidence_required: list[str] = field(default_factory=list)
    violated_constraint_ids: list[str] = field(default_factory=list)
    unresolved_risk_ids: list[str] = field(default_factory=list)
    principle_ids: list[str] = field(default_factory=list)

    human_review_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeliberativeRecommendation:
    """
    A revisable recommendation identifying a preferred Option or a
    constitutionally responsible form of restraint.

    A Recommendation is not a command or sovereign decision.
    """

    recommendation_id: str
    status: RecommendationStatus
    title: str
    explanation: str

    preferred_option_id: str | None = None
    alternative_option_ids: list[str] = field(default_factory=list)

    principle_ids: list[str] = field(default_factory=list)
    value_ids: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    tradeoff_ids: list[str] = field(default_factory=list)
    risk_assessment_ids: list[str] = field(default_factory=list)
    benefit_assessment_ids: list[str] = field(default_factory=list)
    proportionality_assessment_ids: list[str] = field(
        default_factory=list
    )
    restraint_assessment_ids: list[str] = field(default_factory=list)
    conclusion_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    confidence: float | None = None
    uncertainty: str = ""
    revision_conditions: list[str] = field(default_factory=list)

    human_decision_required: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeliberationReport:
    """
    One complete constitutional record of a deliberative cycle.
    """

    deliberation_report_id: str = field(
        default_factory=lambda: f"deliberation-report-{uuid4()}"
    )

    title: str = ""
    question: str = ""
    summary: str = ""

    possibility_ids: list[str] = field(default_factory=list)
    option_ids: list[str] = field(default_factory=list)
    value_ids: list[str] = field(default_factory=list)
    constraint_ids: list[str] = field(default_factory=list)
    consequence_ids: list[str] = field(default_factory=list)
    risk_assessment_ids: list[str] = field(default_factory=list)
    benefit_assessment_ids: list[str] = field(default_factory=list)
    tradeoff_ids: list[str] = field(default_factory=list)
    proportionality_assessment_ids: list[str] = field(
        default_factory=list
    )
    restraint_assessment_ids: list[str] = field(default_factory=list)
    recommendation_ids: list[str] = field(default_factory=list)
    reasoning_report_ids: list[str] = field(default_factory=list)
    domain_ids: list[str] = field(default_factory=list)

    human_judgment_preserved: bool = True

    deliberated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )

    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DeliberationRegistry:
    """
    SentinelAI's assembled deliberative state.

    The Registry preserves deliberative structures without evaluating,
    ranking, recommending, or deciding.
    """

    possibilities: list[Possibility] = field(default_factory=list)
    options: list[Option] = field(default_factory=list)
    values: list[Value] = field(default_factory=list)
    constraints: list[Constraint] = field(default_factory=list)
    consequences: list[Consequence] = field(default_factory=list)
    risk_assessments: list[RiskAssessment] = field(default_factory=list)
    benefit_assessments: list[BenefitAssessment] = field(
        default_factory=list
    )
    tradeoffs: list[Tradeoff] = field(default_factory=list)
    proportionality_assessments: list[ProportionalityAssessment] = field(
        default_factory=list
    )
    restraint_assessments: list[RestraintAssessment] = field(
        default_factory=list
    )
    recommendations: list[DeliberativeRecommendation] = field(
        default_factory=list
    )
    reports: list[DeliberationReport] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
