"""
Deliberation Engine

The Engine orchestrates constitutional deliberation.

The Engine coordinates the Builder, Validator, and Renderer to produce
a constitutionally accountable deliberative result.

Engines orchestrate.

Engines never evaluate options.

Engines never resolve tradeoffs.

Engines never strengthen recommendations.

Engines never replace human judgment.

The Engine delegates responsibility.

The Engine preserves constitutional boundaries.
"""

from collections.abc import Iterable
from typing import Any

from app.core.deliberation.builder import (
    build_deliberation_registry,
)
from app.core.deliberation.models import (
    BenefitAssessment,
    Consequence,
    Constraint,
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
from app.core.deliberation.renderer import (
    render_deliberation_narrative,
    render_deliberation_registry,
)
from app.core.deliberation.validator import (
    validate_deliberation_registry,
)

def run_deliberation(
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
    restraint_assessments: Iterable[
        RestraintAssessment
    ] = (),
    recommendations: Iterable[
        DeliberativeRecommendation
    ] = (),
    reports: Iterable[
        DeliberationReport
    ] = (),
) -> dict[str, Any]:
    """
    Execute one constitutional deliberation pipeline.

    Responsibilities

    - Build
    - Validate
    - Render

    Non-responsibilities

    - Deliberation
    - Evaluation
    - Recommendation generation
    - Human decision-making
    """

    registry = build_deliberation_registry(
        possibilities=possibilities,
        options=options,
        values=values,
        constraints=constraints,
        consequences=consequences,
        risk_assessments=risk_assessments,
        benefit_assessments=benefit_assessments,
        tradeoffs=tradeoffs,
        proportionality_assessments=(
            proportionality_assessments
        ),
        restraint_assessments=(
            restraint_assessments
        ),
        recommendations=recommendations,
        reports=reports,
    )

    validate_deliberation_registry(
        registry,
    )

    return render_deliberation_registry(
        registry,
    )

def run_deliberation_narrative(
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
    restraint_assessments: Iterable[
        RestraintAssessment
    ] = (),
    recommendations: Iterable[
        DeliberativeRecommendation
    ] = (),
    reports: Iterable[
        DeliberationReport
    ] = (),
) -> str:
    """
    Execute one deliberation pipeline and render a
    human-readable constitutional report.
    """

    registry = build_deliberation_registry(
        possibilities=possibilities,
        options=options,
        values=values,
        constraints=constraints,
        consequences=consequences,
        risk_assessments=risk_assessments,
        benefit_assessments=benefit_assessments,
        tradeoffs=tradeoffs,
        proportionality_assessments=(
            proportionality_assessments
        ),
        restraint_assessments=(
            restraint_assessments
        ),
        recommendations=recommendations,
        reports=reports,
    )

    validate_deliberation_registry(
        registry,
    )

    return render_deliberation_narrative(
        registry,
    )


