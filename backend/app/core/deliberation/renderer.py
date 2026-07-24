"""
Deliberation Renderer

The Renderer communicates deliberative structures without altering
their constitutional meaning.

Renderers preserve interpretability.

Renderers never deliberate.

Renderers never strengthen or weaken recommendations.

Renderers never conceal uncertainty.

Renderers never conceal tradeoffs.

Renderers never replace human judgment.

Nothing gained during deliberation may be lost during communication.

The Renderer communicates.

The Renderer does not decide.
"""

from typing import Any

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


def render_possibility(
    possibility: Possibility,
) -> dict[str, Any]:
    """Render one Possibility."""

    return possibility.to_dict()


def render_option(option: Option) -> dict[str, Any]:
    """Render one Option."""

    return option.to_dict()


def render_value(value: Value) -> dict[str, Any]:
    """Render one Value."""

    return value.to_dict()


def render_constraint(
    constraint: Constraint,
) -> dict[str, Any]:
    """Render one Constraint."""

    return constraint.to_dict()


def render_consequence(
    consequence: Consequence,
) -> dict[str, Any]:
    """Render one Consequence."""

    return consequence.to_dict()


def render_risk_assessment(
    assessment: RiskAssessment,
) -> dict[str, Any]:
    """Render one Risk Assessment."""

    return assessment.to_dict()


def render_benefit_assessment(
    assessment: BenefitAssessment,
) -> dict[str, Any]:
    """Render one Benefit Assessment."""

    return assessment.to_dict()


def render_tradeoff(
    tradeoff: Tradeoff,
) -> dict[str, Any]:
    """Render one Tradeoff."""

    return tradeoff.to_dict()


def render_proportionality_assessment(
    assessment: ProportionalityAssessment,
) -> dict[str, Any]:
    """Render one Proportionality Assessment."""

    return assessment.to_dict()


def render_restraint_assessment(
    assessment: RestraintAssessment,
) -> dict[str, Any]:
    """Render one Restraint Assessment."""

    return assessment.to_dict()


def render_deliberative_recommendation(
    recommendation: DeliberativeRecommendation,
) -> dict[str, Any]:
    """Render one Deliberative Recommendation."""

    return recommendation.to_dict()


def render_deliberation_report(
    report: DeliberationReport,
) -> dict[str, Any]:
    """Render one Deliberation Report."""

    return report.to_dict()


def render_deliberation_registry(
    registry: DeliberationRegistry,
) -> dict[str, Any]:
    """
    Render the complete Deliberation Registry.

    The structured representation preserves every constitutional
    deliberative artifact without altering its meaning.
    """

    return {
        "possibilities": [
            render_possibility(possibility)
            for possibility in registry.possibilities
        ],
        "options": [
            render_option(option)
            for option in registry.options
        ],
        "values": [
            render_value(value)
            for value in registry.values
        ],
        "constraints": [
            render_constraint(constraint)
            for constraint in registry.constraints
        ],
        "consequences": [
            render_consequence(consequence)
            for consequence in registry.consequences
        ],
        "risk_assessments": [
            render_risk_assessment(assessment)
            for assessment in registry.risk_assessments
        ],
        "benefit_assessments": [
            render_benefit_assessment(assessment)
            for assessment in registry.benefit_assessments
        ],
        "tradeoffs": [
            render_tradeoff(tradeoff)
            for tradeoff in registry.tradeoffs
        ],
        "proportionality_assessments": [
            render_proportionality_assessment(assessment)
            for assessment in registry.proportionality_assessments
        ],
        "restraint_assessments": [
            render_restraint_assessment(assessment)
            for assessment in registry.restraint_assessments
        ],
        "recommendations": [
            render_deliberative_recommendation(recommendation)
            for recommendation in registry.recommendations
        ],
        "reports": [
            render_deliberation_report(report)
            for report in registry.reports
        ],
    }


def render_deliberation_narrative(
    registry: DeliberationRegistry,
) -> str:
    """
    Render a human-readable account of the Deliberation Registry.

    The narrative preserves options, risks, benefits, tradeoffs,
    restraint, uncertainty, and human authority.

    It does not add interpretation beyond the supplied artifacts.
    """

    lines: list[str] = []

    for report in registry.reports:
        lines.extend(
            [
                report.title,
                "=" * len(report.title),
                "",
                "Question",
                "--------",
                report.question,
                "",
            ]
        )

        report_options = [
            option
            for option in registry.options
            if option.option_id in report.option_ids
        ]

        if report_options:
            lines.extend(["Options", "-------"])

            for option in report_options:
                lines.extend(
                    [
                        f"- {option.title}",
                        f"  Status: {option.status}",
                        f"  Description: {option.description}",
                    ]
                )

                if option.intended_outcome:
                    lines.append(
                        f"  Intended outcome: {option.intended_outcome}"
                    )

                if option.uncertainty:
                    lines.append(
                        f"  Uncertainty: {option.uncertainty}"
                    )

            lines.append("")

        report_constraints = [
            constraint
            for constraint in registry.constraints
            if constraint.constraint_id in report.constraint_ids
        ]

        if report_constraints:
            lines.extend(["Constraints", "-----------"])

            for constraint in report_constraints:
                lines.extend(
                    [
                        f"- {constraint.name}",
                        f"  Status: {constraint.status}",
                        f"  Required: {constraint.required}",
                        f"  Description: {constraint.description}",
                    ]
                )

            lines.append("")

        report_risks = [
            assessment
            for assessment in registry.risk_assessments
            if assessment.risk_assessment_id
            in report.risk_assessment_ids
        ]

        if report_risks:
            lines.extend(["Risk Assessments", "----------------"])

            for assessment in report_risks:
                likelihood = (
                    "unreported"
                    if assessment.likelihood is None
                    else f"{assessment.likelihood:.2f}"
                )

                lines.extend(
                    [
                        f"- {assessment.title}",
                        f"  Level: {assessment.level}",
                        f"  Likelihood: {likelihood}",
                        f"  Severity: {assessment.severity}",
                        (
                            "  Reversibility: "
                            f"{assessment.reversibility}"
                        ),
                        f"  Explanation: {assessment.explanation}",
                    ]
                )

                if assessment.uncertainty:
                    lines.append(
                        f"  Uncertainty: {assessment.uncertainty}"
                    )

            lines.append("")

        report_benefits = [
            assessment
            for assessment in registry.benefit_assessments
            if assessment.benefit_assessment_id
            in report.benefit_assessment_ids
        ]

        if report_benefits:
            lines.extend(["Benefit Assessments", "-------------------"])

            for assessment in report_benefits:
                likelihood = (
                    "unreported"
                    if assessment.likelihood is None
                    else f"{assessment.likelihood:.2f}"
                )

                lines.extend(
                    [
                        f"- {assessment.title}",
                        f"  Level: {assessment.level}",
                        f"  Likelihood: {likelihood}",
                        f"  Explanation: {assessment.explanation}",
                    ]
                )

                if assessment.uncertainty:
                    lines.append(
                        f"  Uncertainty: {assessment.uncertainty}"
                    )

            lines.append("")

        report_tradeoffs = [
            tradeoff
            for tradeoff in registry.tradeoffs
            if tradeoff.tradeoff_id in report.tradeoff_ids
        ]

        if report_tradeoffs:
            lines.extend(["Tradeoffs", "---------"])

            for tradeoff in report_tradeoffs:
                lines.append(f"- {tradeoff.description}")

                if tradeoff.gains:
                    lines.append(
                        "  Gains: " + ", ".join(tradeoff.gains)
                    )

                if tradeoff.losses:
                    lines.append(
                        "  Losses: " + ", ".join(tradeoff.losses)
                    )

                if tradeoff.uncertainty:
                    lines.append(
                        f"  Uncertainty: {tradeoff.uncertainty}"
                    )

            lines.append("")

        report_proportionality = [
            assessment
            for assessment in registry.proportionality_assessments
            if assessment.proportionality_assessment_id
            in report.proportionality_assessment_ids
        ]

        if report_proportionality:
            lines.extend(["Proportionality", "---------------"])

            for assessment in report_proportionality:
                status = (
                    "unresolved"
                    if assessment.proportionate is None
                    else str(assessment.proportionate)
                )

                lines.extend(
                    [
                        f"- Proportionate: {status}",
                        f"  Explanation: {assessment.explanation}",
                    ]
                )

            lines.append("")

        report_restraint = [
            assessment
            for assessment in registry.restraint_assessments
            if assessment.restraint_assessment_id
            in report.restraint_assessment_ids
        ]

        if report_restraint:
            lines.extend(["Restraint Assessments", "---------------------"])

            for assessment in report_restraint:
                lines.extend(
                    [
                        f"- Status: {assessment.status}",
                        f"  Explanation: {assessment.explanation}",
                        (
                            "  Human review required: "
                            f"{assessment.human_review_required}"
                        ),
                    ]
                )

                if assessment.evidence_required:
                    lines.append(
                        "  Evidence required: "
                        + ", ".join(assessment.evidence_required)
                    )

            lines.append("")

        report_recommendations = [
            recommendation
            for recommendation in registry.recommendations
            if recommendation.recommendation_id
            in report.recommendation_ids
        ]

        if report_recommendations:
            lines.extend(["Recommendations", "---------------"])

            for recommendation in report_recommendations:
                confidence = (
                    "unreported"
                    if recommendation.confidence is None
                    else f"{recommendation.confidence:.2f}"
                )

                preferred_option = (
                    recommendation.preferred_option_id
                    or "no preferred option"
                )

                lines.extend(
                    [
                        f"- {recommendation.title}",
                        f"  Status: {recommendation.status}",
                        f"  Preferred option: {preferred_option}",
                        f"  Confidence: {confidence}",
                        f"  Explanation: {recommendation.explanation}",
                    ]
                )

                if recommendation.uncertainty:
                    lines.append(
                        f"  Uncertainty: {recommendation.uncertainty}"
                    )

                if recommendation.revision_conditions:
                    lines.append(
                        "  Revision conditions: "
                        + "; ".join(
                            recommendation.revision_conditions
                        )
                    )

                lines.append(
                    "  Human decision required: "
                    f"{recommendation.human_decision_required}"
                )

            lines.append("")

        lines.extend(
            [
                "Human Judgment",
                "--------------",
                (
                    "Preserved"
                    if report.human_judgment_preserved
                    else "Not preserved"
                ),
                "",
                "Summary",
                "-------",
                report.summary,
                "",
            ]
        )

    return "\n".join(lines).rstrip()
