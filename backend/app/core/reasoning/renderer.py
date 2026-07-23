"""
Reasoning Renderer

Renderers communicate reasoning.

Renderers transform constitutional reasoning structures into clear,
traceable representations for people and systems.

Renderers preserve meaning.

Renderers never organize.

Renderers never validate.

Renderers never reason.

A Renderer faithfully communicates the reasoning process without
altering its meaning.
"""

from typing import Any

from app.core.reasoning.models import (
    Assumption,
    CoherenceAssessment,
    Conclusion,
    Counterargument,
    EvidenceAssessment,
    Inference,
    Premise,
    ReasoningRegistry,
    ReasoningReport,
)


def render_premise(premise: Premise) -> dict[str, Any]:
    """Render one Premise."""

    return premise.to_dict()


def render_assumption(assumption: Assumption) -> dict[str, Any]:
    """Render one Assumption."""

    return assumption.to_dict()


def render_evidence_assessment(
    assessment: EvidenceAssessment,
) -> dict[str, Any]:
    """Render one Evidence Assessment."""

    return assessment.to_dict()


def render_counterargument(
    counterargument: Counterargument,
) -> dict[str, Any]:
    """Render one Counterargument."""

    return counterargument.to_dict()


def render_inference(inference: Inference) -> dict[str, Any]:
    """Render one Inference."""

    return inference.to_dict()


def render_conclusion(conclusion: Conclusion) -> dict[str, Any]:
    """Render one Conclusion."""

    return conclusion.to_dict()


def render_coherence_assessment(
    assessment: CoherenceAssessment,
) -> dict[str, Any]:
    """Render one Coherence Assessment."""

    return assessment.to_dict()


def render_reasoning_report(
    report: ReasoningReport,
) -> dict[str, Any]:
    """Render one Reasoning Report."""

    return report.to_dict()


def render_reasoning_registry(
    registry: ReasoningRegistry,
) -> dict[str, Any]:
    """
    Render the complete Reasoning Registry.

    Rendering preserves the structure and traceability of the Registry
    without altering its meaning.
    """

    return {
        "premises": [
            render_premise(premise)
            for premise in registry.premises
        ],
        "assumptions": [
            render_assumption(assumption)
            for assumption in registry.assumptions
        ],
        "evidence_assessments": [
            render_evidence_assessment(assessment)
            for assessment in registry.evidence_assessments
        ],
        "counterarguments": [
            render_counterargument(counterargument)
            for counterargument in registry.counterarguments
        ],
        "inferences": [
            render_inference(inference)
            for inference in registry.inferences
        ],
        "conclusions": [
            render_conclusion(conclusion)
            for conclusion in registry.conclusions
        ],
        "coherence_assessments": [
            render_coherence_assessment(assessment)
            for assessment in registry.coherence_assessments
        ],
        "reports": [
            render_reasoning_report(report)
            for report in registry.reports
        ],
    }


def render_reasoning_narrative(
    registry: ReasoningRegistry,
) -> str:
    """
    Render a concise human-readable account of the Reasoning Registry.

    This narrative communicates the recorded reasoning structure.
    It does not add interpretation beyond the supplied objects.
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

        if registry.premises:
            lines.extend(["Premises", "--------"])
            lines.extend(
                f"- {premise.statement}"
                for premise in registry.premises
                if premise.premise_id in report.premise_ids
            )
            lines.append("")

        if registry.assumptions:
            lines.extend(["Assumptions", "-----------"])
            lines.extend(
                f"- {assumption.statement}"
                for assumption in registry.assumptions
                if assumption.assumption_id in report.assumption_ids
            )
            lines.append("")

        if registry.evidence_assessments:
            lines.extend(["Evidence Assessments", "--------------------"])
            lines.extend(
                (
                    f"- [{assessment.position}] "
                    f"{assessment.explanation}"
                )
                for assessment in registry.evidence_assessments
                if assessment.assessment_id
                in report.evidence_assessment_ids
            )
            lines.append("")

        if registry.counterarguments:
            lines.extend(["Counterarguments", "----------------"])
            lines.extend(
                f"- {counterargument.statement}"
                for counterargument in registry.counterarguments
                if counterargument.counterargument_id
                in report.counterargument_ids
            )
            lines.append("")

        if registry.inferences:
            lines.extend(["Inferences", "----------"])
            lines.extend(
                f"- {inference.explanation}"
                for inference in registry.inferences
                if inference.inference_id in report.inference_ids
            )
            lines.append("")

        if registry.conclusions:
            lines.extend(["Conclusions", "-----------"])
            for conclusion in registry.conclusions:
                if conclusion.conclusion_id not in report.conclusion_ids:
                    continue

                confidence = (
                    "unreported"
                    if conclusion.confidence is None
                    else f"{conclusion.confidence:.2f}"
                )

                lines.extend(
                    [
                        f"- {conclusion.statement}",
                        f"  Status: {conclusion.status}",
                        f"  Confidence: {confidence}",
                        f"  Justification: {conclusion.justification}",
                        (
                            f"  Uncertainty: {conclusion.uncertainty}"
                            if conclusion.uncertainty
                            else "  Uncertainty: none recorded"
                        ),
                    ]
                )
            lines.append("")

        if registry.coherence_assessments:
            lines.extend(["Coherence", "---------"])
            lines.extend(
                (
                    f"- [{assessment.status}] "
                    f"{assessment.explanation}"
                )
                for assessment in registry.coherence_assessments
                if assessment.coherence_assessment_id
                in report.coherence_assessment_ids
            )
            lines.append("")

        lines.extend(["Summary", "-------", report.summary, ""])

    return "\n".join(lines).rstrip()
