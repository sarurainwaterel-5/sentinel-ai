"""
Deliberation Validator

The Validator protects constitutional integrity.

Validators verify that deliberative structures remain complete,
traceable, coherent, and constitutionally accountable.

Validators protect trust.

Validators never evaluate options.

Validators never compare recommendations.

Validators never replace human judgment.

Validators never deliberate.
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


def _require_text(value: str, field_name: str) -> None:
    """Require a non-empty textual value."""

    if not value.strip():
        raise ValueError(f"{field_name} is required.")


def _require_probability(
    value: float | None,
    field_name: str,
) -> None:
    """Require probability-like values to remain between 0.0 and 1.0."""

    if value is not None and not 0.0 <= value <= 1.0:
        raise ValueError(
            f"{field_name} must be between 0.0 and 1.0."
        )


def _ensure_unique_ids(
    *,
    object_name: str,
    object_ids: Iterable[str],
) -> None:
    """Reject duplicate identifiers within one deliberative object type."""

    ids = list(object_ids)

    if len(ids) != len(set(ids)):
        raise ValueError(
            f"Duplicate {object_name} identifiers were found."
        )


def _ensure_known_references(
    *,
    owner_name: str,
    referenced_ids: Iterable[str],
    known_ids: set[str],
    reference_name: str,
) -> None:
    """Require every internal reference to resolve within the Registry."""

    unknown_ids = sorted(set(referenced_ids) - known_ids)

    if unknown_ids:
        raise ValueError(
            f"{owner_name} references unknown {reference_name} IDs: "
            f"{', '.join(unknown_ids)}"
        )


def validate_possibility(
    possibility: Possibility,
) -> bool:
    """Validate one Possibility."""

    _require_text(
        possibility.possibility_id,
        "Possibility ID",
    )
    _require_text(
        possibility.title,
        "Possibility title",
    )
    _require_text(
        possibility.description,
        "Possibility description",
    )

    return True


def validate_option(option: Option) -> bool:
    """Validate one Option."""

    _require_text(option.option_id, "Option ID")
    _require_text(
        option.possibility_id,
        "Option Possibility ID",
    )
    _require_text(option.title, "Option title")
    _require_text(
        option.description,
        "Option description",
    )

    return True


def validate_value(value: Value) -> bool:
    """Validate one Value."""

    _require_text(value.value_id, "Value ID")
    _require_text(value.name, "Value name")
    _require_text(
        value.description,
        "Value description",
    )

    if value.priority is not None and value.priority < 1:
        raise ValueError(
            "Value priority must be greater than or equal to 1."
        )

    return True


def validate_constraint(
    constraint: Constraint,
) -> bool:
    """Validate one Constraint."""

    _require_text(
        constraint.constraint_id,
        "Constraint ID",
    )
    _require_text(
        constraint.name,
        "Constraint name",
    )
    _require_text(
        constraint.description,
        "Constraint description",
    )

    return True


def validate_consequence(
    consequence: Consequence,
) -> bool:
    """Validate one Consequence."""

    _require_text(
        consequence.consequence_id,
        "Consequence ID",
    )
    _require_text(
        consequence.option_id,
        "Consequence Option ID",
    )
    _require_text(
        consequence.description,
        "Consequence description",
    )

    return True


def validate_risk_assessment(
    assessment: RiskAssessment,
) -> bool:
    """Validate one Risk Assessment."""

    _require_text(
        assessment.risk_assessment_id,
        "Risk Assessment ID",
    )
    _require_text(
        assessment.option_id,
        "Risk Assessment Option ID",
    )
    _require_text(
        assessment.title,
        "Risk Assessment title",
    )
    _require_text(
        assessment.explanation,
        "Risk Assessment explanation",
    )

    _require_probability(
        assessment.likelihood,
        "Risk Assessment likelihood",
    )

    return True


def validate_benefit_assessment(
    assessment: BenefitAssessment,
) -> bool:
    """Validate one Benefit Assessment."""

    _require_text(
        assessment.benefit_assessment_id,
        "Benefit Assessment ID",
    )
    _require_text(
        assessment.option_id,
        "Benefit Assessment Option ID",
    )
    _require_text(
        assessment.title,
        "Benefit Assessment title",
    )
    _require_text(
        assessment.explanation,
        "Benefit Assessment explanation",
    )

    _require_probability(
        assessment.likelihood,
        "Benefit Assessment likelihood",
    )

    return True


def validate_tradeoff(
    tradeoff: Tradeoff,
) -> bool:
    """Validate one Tradeoff."""

    _require_text(
        tradeoff.tradeoff_id,
        "Tradeoff ID",
    )
    _require_text(
        tradeoff.option_id,
        "Tradeoff Option ID",
    )
    _require_text(
        tradeoff.description,
        "Tradeoff description",
    )

    if not tradeoff.gains and not tradeoff.losses:
        raise ValueError(
            "Every Tradeoff must identify at least one gain or loss."
        )

    return True


def validate_proportionality_assessment(
    assessment: ProportionalityAssessment,
) -> bool:
    """Validate one Proportionality Assessment."""

    _require_text(
        assessment.proportionality_assessment_id,
        "Proportionality Assessment ID",
    )
    _require_text(
        assessment.option_id,
        "Proportionality Assessment Option ID",
    )
    _require_text(
        assessment.explanation,
        "Proportionality Assessment explanation",
    )

    return True


def validate_restraint_assessment(
    assessment: RestraintAssessment,
) -> bool:
    """Validate one Restraint Assessment."""

    _require_text(
        assessment.restraint_assessment_id,
        "Restraint Assessment ID",
    )
    _require_text(
        assessment.option_id,
        "Restraint Assessment Option ID",
    )
    _require_text(
        assessment.explanation,
        "Restraint Assessment explanation",
    )

    if assessment.status == "defer_to_human":
        if not assessment.human_review_required:
            raise ValueError(
                "A defer-to-human Restraint Assessment must require "
                "human review."
            )

    return True


def validate_deliberative_recommendation(
    recommendation: DeliberativeRecommendation,
) -> bool:
    """Validate one Deliberative Recommendation."""

    _require_text(
        recommendation.recommendation_id,
        "Recommendation ID",
    )
    _require_text(
        recommendation.title,
        "Recommendation title",
    )
    _require_text(
        recommendation.explanation,
        "Recommendation explanation",
    )

    _require_probability(
        recommendation.confidence,
        "Recommendation confidence",
    )

    if not recommendation.human_decision_required:
        raise ValueError(
            "Every Deliberative Recommendation must preserve "
            "human decision authority."
        )

    option_required_statuses = {
        "preferred",
        "conditional",
    }

    if recommendation.status in option_required_statuses:
        if not recommendation.preferred_option_id:
            raise ValueError(
                "A preferred or conditional Recommendation must "
                "reference a preferred Option."
            )

    restraint_statuses = {
        "deferred",
        "no_acceptable_option",
        "human_decision_required",
    }

    if recommendation.status in restraint_statuses:
        if not recommendation.restraint_assessment_ids:
            raise ValueError(
                "A deferred, no-acceptable-option, or human-decision-required "
                "Recommendation must reference a Restraint Assessment."
            )

    return True


def validate_deliberation_report(
    report: DeliberationReport,
) -> bool:
    """Validate one Deliberation Report."""

    _require_text(
        report.deliberation_report_id,
        "Deliberation Report ID",
    )
    _require_text(
        report.title,
        "Deliberation Report title",
    )
    _require_text(
        report.question,
        "Deliberation Report question",
    )
    _require_text(
        report.summary,
        "Deliberation Report summary",
    )

    if not report.human_judgment_preserved:
        raise ValueError(
            "Every Deliberation Report must preserve human judgment."
        )

    if not report.option_ids:
        raise ValueError(
            "Every Deliberation Report must reference at least one Option."
        )

    if not report.recommendation_ids:
        raise ValueError(
            "Every Deliberation Report must reference at least one "
            "Recommendation."
        )

    return True


def validate_deliberation_registry(
    registry: DeliberationRegistry,
) -> bool:
    """
    Validate the complete Deliberation Registry.

    The Registry Validator protects:

    - object completeness
    - unique identity
    - internal traceability
    - human agency
    - constitutional responsibility

    It never determines which Option is preferable.
    """

    for possibility in registry.possibilities:
        validate_possibility(possibility)

    for option in registry.options:
        validate_option(option)

    for value in registry.values:
        validate_value(value)

    for constraint in registry.constraints:
        validate_constraint(constraint)

    for consequence in registry.consequences:
        validate_consequence(consequence)

    for assessment in registry.risk_assessments:
        validate_risk_assessment(assessment)

    for assessment in registry.benefit_assessments:
        validate_benefit_assessment(assessment)

    for tradeoff in registry.tradeoffs:
        validate_tradeoff(tradeoff)

    for assessment in registry.proportionality_assessments:
        validate_proportionality_assessment(assessment)

    for assessment in registry.restraint_assessments:
        validate_restraint_assessment(assessment)

    for recommendation in registry.recommendations:
        validate_deliberative_recommendation(recommendation)

    for report in registry.reports:
        validate_deliberation_report(report)

    possibility_ids = {
        possibility.possibility_id
        for possibility in registry.possibilities
    }
    option_ids = {
        option.option_id
        for option in registry.options
    }
    value_ids = {
        value.value_id
        for value in registry.values
    }
    constraint_ids = {
        constraint.constraint_id
        for constraint in registry.constraints
    }
    consequence_ids = {
        consequence.consequence_id
        for consequence in registry.consequences
    }
    risk_assessment_ids = {
        assessment.risk_assessment_id
        for assessment in registry.risk_assessments
    }
    benefit_assessment_ids = {
        assessment.benefit_assessment_id
        for assessment in registry.benefit_assessments
    }
    tradeoff_ids = {
        tradeoff.tradeoff_id
        for tradeoff in registry.tradeoffs
    }
    proportionality_assessment_ids = {
        assessment.proportionality_assessment_id
        for assessment in registry.proportionality_assessments
    }
    restraint_assessment_ids = {
        assessment.restraint_assessment_id
        for assessment in registry.restraint_assessments
    }
    recommendation_ids = {
        recommendation.recommendation_id
        for recommendation in registry.recommendations
    }

    _ensure_unique_ids(
        object_name="Possibility",
        object_ids=[
            possibility.possibility_id
            for possibility in registry.possibilities
        ],
    )
    _ensure_unique_ids(
        object_name="Option",
        object_ids=[
            option.option_id
            for option in registry.options
        ],
    )
    _ensure_unique_ids(
        object_name="Value",
        object_ids=[
            value.value_id
            for value in registry.values
        ],
    )
    _ensure_unique_ids(
        object_name="Constraint",
        object_ids=[
            constraint.constraint_id
            for constraint in registry.constraints
        ],
    )
    _ensure_unique_ids(
        object_name="Consequence",
        object_ids=[
            consequence.consequence_id
            for consequence in registry.consequences
        ],
    )
    _ensure_unique_ids(
        object_name="Risk Assessment",
        object_ids=[
            assessment.risk_assessment_id
            for assessment in registry.risk_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Benefit Assessment",
        object_ids=[
            assessment.benefit_assessment_id
            for assessment in registry.benefit_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Tradeoff",
        object_ids=[
            tradeoff.tradeoff_id
            for tradeoff in registry.tradeoffs
        ],
    )
    _ensure_unique_ids(
        object_name="Proportionality Assessment",
        object_ids=[
            assessment.proportionality_assessment_id
            for assessment in registry.proportionality_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Restraint Assessment",
        object_ids=[
            assessment.restraint_assessment_id
            for assessment in registry.restraint_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Recommendation",
        object_ids=[
            recommendation.recommendation_id
            for recommendation in registry.recommendations
        ],
    )
    _ensure_unique_ids(
        object_name="Deliberation Report",
        object_ids=[
            report.deliberation_report_id
            for report in registry.reports
        ],
    )

    for option in registry.options:
        owner = f"Option '{option.option_id}'"

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[option.possibility_id],
            known_ids=possibility_ids,
            reference_name="Possibility",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=option.value_ids,
            known_ids=value_ids,
            reference_name="Value",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=option.constraint_ids,
            known_ids=constraint_ids,
            reference_name="Constraint",
        )

    for constraint in registry.constraints:
        _ensure_known_references(
            owner_name=f"Constraint '{constraint.constraint_id}'",
            referenced_ids=constraint.option_ids,
            known_ids=option_ids,
            reference_name="Option",
        )

    for consequence in registry.consequences:
        _ensure_known_references(
            owner_name=f"Consequence '{consequence.consequence_id}'",
            referenced_ids=[consequence.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )

    for assessment in registry.risk_assessments:
        owner = (
            f"Risk Assessment "
            f"'{assessment.risk_assessment_id}'"
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[assessment.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.consequence_ids,
            known_ids=consequence_ids,
            reference_name="Consequence",
        )

    for assessment in registry.benefit_assessments:
        owner = (
            f"Benefit Assessment "
            f"'{assessment.benefit_assessment_id}'"
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[assessment.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.consequence_ids,
            known_ids=consequence_ids,
            reference_name="Consequence",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.value_ids,
            known_ids=value_ids,
            reference_name="Value",
        )

    for tradeoff in registry.tradeoffs:
        owner = f"Tradeoff '{tradeoff.tradeoff_id}'"

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[tradeoff.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=tradeoff.value_ids,
            known_ids=value_ids,
            reference_name="Value",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=tradeoff.risk_assessment_ids,
            known_ids=risk_assessment_ids,
            reference_name="Risk Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=tradeoff.benefit_assessment_ids,
            known_ids=benefit_assessment_ids,
            reference_name="Benefit Assessment",
        )

    for assessment in registry.proportionality_assessments:
        owner = (
            f"Proportionality Assessment "
            f"'{assessment.proportionality_assessment_id}'"
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[assessment.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.risk_assessment_ids,
            known_ids=risk_assessment_ids,
            reference_name="Risk Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.benefit_assessment_ids,
            known_ids=benefit_assessment_ids,
            reference_name="Benefit Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.constraint_ids,
            known_ids=constraint_ids,
            reference_name="Constraint",
        )

    for assessment in registry.restraint_assessments:
        owner = (
            f"Restraint Assessment "
            f"'{assessment.restraint_assessment_id}'"
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=[assessment.option_id],
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.violated_constraint_ids,
            known_ids=constraint_ids,
            reference_name="Constraint",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=assessment.unresolved_risk_ids,
            known_ids=risk_assessment_ids,
            reference_name="Risk Assessment",
        )

    for recommendation in registry.recommendations:
        owner = (
            f"Recommendation "
            f"'{recommendation.recommendation_id}'"
        )

        preferred_ids = (
            [recommendation.preferred_option_id]
            if recommendation.preferred_option_id
            else []
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=preferred_ids,
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.alternative_option_ids,
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.value_ids,
            known_ids=value_ids,
            reference_name="Value",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.constraint_ids,
            known_ids=constraint_ids,
            reference_name="Constraint",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.tradeoff_ids,
            known_ids=tradeoff_ids,
            reference_name="Tradeoff",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.risk_assessment_ids,
            known_ids=risk_assessment_ids,
            reference_name="Risk Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.benefit_assessment_ids,
            known_ids=benefit_assessment_ids,
            reference_name="Benefit Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=(
                recommendation.proportionality_assessment_ids
            ),
            known_ids=proportionality_assessment_ids,
            reference_name="Proportionality Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=recommendation.restraint_assessment_ids,
            known_ids=restraint_assessment_ids,
            reference_name="Restraint Assessment",
        )

    for report in registry.reports:
        owner = (
            f"Deliberation Report "
            f"'{report.deliberation_report_id}'"
        )

        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.possibility_ids,
            known_ids=possibility_ids,
            reference_name="Possibility",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.option_ids,
            known_ids=option_ids,
            reference_name="Option",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.value_ids,
            known_ids=value_ids,
            reference_name="Value",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.constraint_ids,
            known_ids=constraint_ids,
            reference_name="Constraint",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.consequence_ids,
            known_ids=consequence_ids,
            reference_name="Consequence",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.risk_assessment_ids,
            known_ids=risk_assessment_ids,
            reference_name="Risk Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.benefit_assessment_ids,
            known_ids=benefit_assessment_ids,
            reference_name="Benefit Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.tradeoff_ids,
            known_ids=tradeoff_ids,
            reference_name="Tradeoff",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=(
                report.proportionality_assessment_ids
            ),
            known_ids=proportionality_assessment_ids,
            reference_name="Proportionality Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.restraint_assessment_ids,
            known_ids=restraint_assessment_ids,
            reference_name="Restraint Assessment",
        )
        _ensure_known_references(
            owner_name=owner,
            referenced_ids=report.recommendation_ids,
            known_ids=recommendation_ids,
            reference_name="Recommendation",
        )

    return True

