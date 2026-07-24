"""
Deliberation Builder

The Builder organizes deliberation.

The Builder assembles constitutional deliberative objects into a
coherent Deliberation Registry.

Builders organize.

Builders never evaluate options.

Builders never resolve tradeoffs.

Builders never recommend action.

Builders never replace human judgment.
"""

from collections.abc import Iterable

from app.core.deliberation.models import (
    BenefitAssessment,
    Consequence,
    Constraint,
    DeliberationRegistry,
    DeliberationReport,
    DeliberativeRecommendation,
    Option,
    Possibility,
    ProportionalityAssessment,
    RestraintAssessment,
    RiskAssessment,
    Tradeoff,
    Value,
)


def build_deliberation_registry(
    *,
    possibilities: Iterable[Possibility] = (),
    options: Iterable[Option] = (),
    values: Iterable[Value] = (),
    constraints: Iterable[Constraint] = (),
    consequences: Iterable[Consequence] = (),
    risk_assessments: Iterable[RiskAssessment] = (),
    benefit_assessments: Iterable[BenefitAssessment] = (),
    tradeoffs: Iterable[Tradeoff] = (),
    proportionality_assessments: Iterable[
        ProportionalityAssessment
    ] = (),
    restraint_assessments: Iterable[RestraintAssessment] = (),
    recommendations: Iterable[DeliberativeRecommendation] = (),
    reports: Iterable[DeliberationReport] = (),
) -> DeliberationRegistry:
    """
    Assemble SentinelAI's deliberative state.

    Builder responsibilities:

    - Organize deliberative objects.
    - Preserve the supplied deliberative state.
    - Return one coherent Deliberation Registry.

    Builder non-responsibilities:

    - Admitting possibilities as options
    - Evaluating risks or benefits
    - Resolving tradeoffs
    - Assessing proportionality
    - Assessing restraint
    - Selecting recommendations
    - Validation
    - Rendering
    - Persistence
    - Human decision-making
    """

    return DeliberationRegistry(
        possibilities=list(possibilities),
        options=list(options),
        values=list(values),
        constraints=list(constraints),
        consequences=list(consequences),
        risk_assessments=list(risk_assessments),
        benefit_assessments=list(benefit_assessments),
        tradeoffs=list(tradeoffs),
        proportionality_assessments=list(
            proportionality_assessments
        ),
        restraint_assessments=list(restraint_assessments),
        recommendations=list(recommendations),
        reports=list(reports),
    )


def build_empty_deliberation_registry() -> DeliberationRegistry:
    """
    Construct an empty but structurally valid Deliberation Registry.

    An empty registry means no deliberative objects were supplied.

    It does not imply that deliberation failed, that no options exist,
    or that restraint is required.
    """

    return build_deliberation_registry()

