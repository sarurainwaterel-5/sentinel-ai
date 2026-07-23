"""
Reasoning Validator

Validators protect the constitutional integrity of Reasoning.

Validators verify that reasoning structures satisfy SentinelAI's
constitutional requirements before orchestration.

Validators preserve trust by ensuring structural integrity.

Validators never organize.

Validators never reason.

Validators never render.

Truth belongs to reality.

Reasoning belongs to the Engine.

Trust belongs to the Validator.
"""

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


def validate_premise(premise: Premise) -> bool:
    """Validate one Premise."""

    if not premise.premise_id.strip():
        raise ValueError("Premise ID is required.")

    if not premise.statement.strip():
        raise ValueError("Premise statement is required.")

    return True


def validate_assumption(assumption: Assumption) -> bool:
    """Validate one Assumption."""

    if not assumption.assumption_id.strip():
        raise ValueError("Assumption ID is required.")

    if not assumption.statement.strip():
        raise ValueError("Assumption statement is required.")

    if not assumption.rationale.strip():
        raise ValueError("Assumption rationale is required.")

    if not assumption.acknowledged:
        raise ValueError(
            "Every assumption must be explicitly acknowledged."
        )

    return True


def validate_evidence_assessment(
    assessment: EvidenceAssessment,
) -> bool:
    """Validate one Evidence Assessment."""

    if not assessment.assessment_id.strip():
        raise ValueError("Evidence Assessment ID is required.")

    if not assessment.proposition_id.strip():
        raise ValueError("Evidence Assessment proposition ID is required.")

    if not assessment.evidence_id.strip():
        raise ValueError("Evidence Assessment evidence ID is required.")

    if not assessment.explanation.strip():
        raise ValueError("Evidence Assessment explanation is required.")

    if assessment.weight is not None and not 0.0 <= assessment.weight <= 1.0:
        raise ValueError(
            "Evidence Assessment weight must be between 0.0 and 1.0."
        )

    return True


def validate_counterargument(
    counterargument: Counterargument,
) -> bool:
    """Validate one Counterargument."""

    if not counterargument.counterargument_id.strip():
        raise ValueError("Counterargument ID is required.")

    if not counterargument.statement.strip():
        raise ValueError("Counterargument statement is required.")

    if not counterargument.explanation.strip():
        raise ValueError("Counterargument explanation is required.")

    if (
        not counterargument.challenges_premise_ids
        and not counterargument.challenges_conclusion_ids
    ):
        raise ValueError(
            "Every counterargument must challenge at least one "
            "premise or conclusion."
        )

    return True


def validate_inference(inference: Inference) -> bool:
    """Validate one Inference."""

    if not inference.inference_id.strip():
        raise ValueError("Inference ID is required.")

    if not inference.explanation.strip():
        raise ValueError("Inference explanation is required.")

    if not inference.premise_ids:
        raise ValueError(
            "Every inference must reference at least one premise."
        )

    return True


def validate_conclusion(conclusion: Conclusion) -> bool:
    """Validate one Conclusion."""

    if not conclusion.conclusion_id.strip():
        raise ValueError("Conclusion ID is required.")

    if not conclusion.statement.strip():
        raise ValueError("Conclusion statement is required.")

    if not conclusion.justification.strip():
        raise ValueError("Conclusion justification is required.")

    if not conclusion.premise_ids:
        raise ValueError(
            "Every conclusion must reference at least one premise."
        )

    if not conclusion.inference_ids:
        raise ValueError(
            "Every conclusion must reference at least one inference."
        )

    if conclusion.confidence is not None:
        if not 0.0 <= conclusion.confidence <= 1.0:
            raise ValueError(
                "Conclusion confidence must be between 0.0 and 1.0."
            )

    return True


def validate_coherence_assessment(
    assessment: CoherenceAssessment,
) -> bool:
    """Validate one Coherence Assessment."""

    if not assessment.coherence_assessment_id.strip():
        raise ValueError("Coherence Assessment ID is required.")

    if not assessment.explanation.strip():
        raise ValueError("Coherence Assessment explanation is required.")

    if not assessment.conclusion_ids:
        raise ValueError(
            "Every Coherence Assessment must reference at least "
            "one conclusion."
        )

    return True


def validate_reasoning_report(
    report: ReasoningReport,
) -> bool:
    """Validate one Reasoning Report."""

    if not report.reasoning_report_id.strip():
        raise ValueError("Reasoning Report ID is required.")

    if not report.title.strip():
        raise ValueError("Reasoning Report title is required.")

    if not report.question.strip():
        raise ValueError("Reasoning Report question is required.")

    if not report.summary.strip():
        raise ValueError("Reasoning Report summary is required.")

    if not report.conclusion_ids:
        raise ValueError(
            "Every Reasoning Report must reference at least one conclusion."
        )

    if not report.coherence_assessment_ids:
        raise ValueError(
            "Every Reasoning Report must reference at least one "
            "Coherence Assessment."
        )

    return True


def _ensure_unique_ids(
    *,
    object_name: str,
    object_ids: list[str],
) -> None:
    """Reject duplicate identifiers within one reasoning object type."""

    if len(object_ids) != len(set(object_ids)):
        raise ValueError(
            f"Duplicate {object_name} identifiers were found."
        )


def _ensure_known_references(
    *,
    owner_name: str,
    referenced_ids: list[str],
    known_ids: set[str],
    reference_name: str,
) -> None:
    """Verify that every structural reference resolves inside the Registry."""

    unknown_ids = sorted(set(referenced_ids) - known_ids)

    if unknown_ids:
        raise ValueError(
            f"{owner_name} references unknown {reference_name} IDs: "
            f"{', '.join(unknown_ids)}"
        )


def validate_reasoning_registry(
    registry: ReasoningRegistry,
) -> bool:
    """
    Validate the complete Reasoning Registry.

    The Registry Validator verifies:

    - contained object structure
    - unique identifiers
    - internal referential integrity

    It does not determine whether a conclusion is true.
    """

    for premise in registry.premises:
        validate_premise(premise)

    for assumption in registry.assumptions:
        validate_assumption(assumption)

    for assessment in registry.evidence_assessments:
        validate_evidence_assessment(assessment)

    for counterargument in registry.counterarguments:
        validate_counterargument(counterargument)

    for inference in registry.inferences:
        validate_inference(inference)

    for conclusion in registry.conclusions:
        validate_conclusion(conclusion)

    for assessment in registry.coherence_assessments:
        validate_coherence_assessment(assessment)

    for report in registry.reports:
        validate_reasoning_report(report)

    premise_ids = {
        premise.premise_id
        for premise in registry.premises
    }
    assumption_ids = {
        assumption.assumption_id
        for assumption in registry.assumptions
    }
    evidence_assessment_ids = {
        assessment.assessment_id
        for assessment in registry.evidence_assessments
    }
    counterargument_ids = {
        counterargument.counterargument_id
        for counterargument in registry.counterarguments
    }
    inference_ids = {
        inference.inference_id
        for inference in registry.inferences
    }
    conclusion_ids = {
        conclusion.conclusion_id
        for conclusion in registry.conclusions
    }
    coherence_assessment_ids = {
        assessment.coherence_assessment_id
        for assessment in registry.coherence_assessments
    }
    report_ids = {
        report.reasoning_report_id
        for report in registry.reports
    }

    _ensure_unique_ids(
        object_name="Premise",
        object_ids=[
            premise.premise_id
            for premise in registry.premises
        ],
    )
    _ensure_unique_ids(
        object_name="Assumption",
        object_ids=[
            assumption.assumption_id
            for assumption in registry.assumptions
        ],
    )
    _ensure_unique_ids(
        object_name="Evidence Assessment",
        object_ids=[
            assessment.assessment_id
            for assessment in registry.evidence_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Counterargument",
        object_ids=[
            counterargument.counterargument_id
            for counterargument in registry.counterarguments
        ],
    )
    _ensure_unique_ids(
        object_name="Inference",
        object_ids=[
            inference.inference_id
            for inference in registry.inferences
        ],
    )
    _ensure_unique_ids(
        object_name="Conclusion",
        object_ids=[
            conclusion.conclusion_id
            for conclusion in registry.conclusions
        ],
    )
    _ensure_unique_ids(
        object_name="Coherence Assessment",
        object_ids=[
            assessment.coherence_assessment_id
            for assessment in registry.coherence_assessments
        ],
    )
    _ensure_unique_ids(
        object_name="Reasoning Report",
        object_ids=[
            report.reasoning_report_id
            for report in registry.reports
        ],
    )

    for inference in registry.inferences:
        _ensure_known_references(
            owner_name=f"Inference '{inference.inference_id}'",
            referenced_ids=inference.premise_ids,
            known_ids=premise_ids,
            reference_name="Premise",
        )
        _ensure_known_references(
            owner_name=f"Inference '{inference.inference_id}'",
            referenced_ids=inference.assumption_ids,
            known_ids=assumption_ids,
            reference_name="Assumption",
        )
        _ensure_known_references(
            owner_name=f"Inference '{inference.inference_id}'",
            referenced_ids=inference.evidence_assessment_ids,
            known_ids=evidence_assessment_ids,
            reference_name="Evidence Assessment",
        )

    for counterargument in registry.counterarguments:
        _ensure_known_references(
            owner_name=(
                f"Counterargument "
                f"'{counterargument.counterargument_id}'"
            ),
            referenced_ids=counterargument.challenges_premise_ids,
            known_ids=premise_ids,
            reference_name="Premise",
        )
        _ensure_known_references(
            owner_name=(
                f"Counterargument "
                f"'{counterargument.counterargument_id}'"
            ),
            referenced_ids=counterargument.challenges_conclusion_ids,
            known_ids=conclusion_ids,
            reference_name="Conclusion",
        )

    for conclusion in registry.conclusions:
        owner_name = f"Conclusion '{conclusion.conclusion_id}'"

        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=conclusion.premise_ids,
            known_ids=premise_ids,
            reference_name="Premise",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=conclusion.assumption_ids,
            known_ids=assumption_ids,
            reference_name="Assumption",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=conclusion.inference_ids,
            known_ids=inference_ids,
            reference_name="Inference",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=conclusion.evidence_assessment_ids,
            known_ids=evidence_assessment_ids,
            reference_name="Evidence Assessment",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=conclusion.counterargument_ids,
            known_ids=counterargument_ids,
            reference_name="Counterargument",
        )

    for assessment in registry.coherence_assessments:
        _ensure_known_references(
            owner_name=(
                f"Coherence Assessment "
                f"'{assessment.coherence_assessment_id}'"
            ),
            referenced_ids=assessment.premise_ids,
            known_ids=premise_ids,
            reference_name="Premise",
        )
        _ensure_known_references(
            owner_name=(
                f"Coherence Assessment "
                f"'{assessment.coherence_assessment_id}'"
            ),
            referenced_ids=assessment.assumption_ids,
            known_ids=assumption_ids,
            reference_name="Assumption",
        )
        _ensure_known_references(
            owner_name=(
                f"Coherence Assessment "
                f"'{assessment.coherence_assessment_id}'"
            ),
            referenced_ids=assessment.conclusion_ids,
            known_ids=conclusion_ids,
            reference_name="Conclusion",
        )

    for report in registry.reports:
        owner_name = f"Reasoning Report '{report.reasoning_report_id}'"

        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.premise_ids,
            known_ids=premise_ids,
            reference_name="Premise",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.assumption_ids,
            known_ids=assumption_ids,
            reference_name="Assumption",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.evidence_assessment_ids,
            known_ids=evidence_assessment_ids,
            reference_name="Evidence Assessment",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.counterargument_ids,
            known_ids=counterargument_ids,
            reference_name="Counterargument",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.inference_ids,
            known_ids=inference_ids,
            reference_name="Inference",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.conclusion_ids,
            known_ids=conclusion_ids,
            reference_name="Conclusion",
        )
        _ensure_known_references(
            owner_name=owner_name,
            referenced_ids=report.coherence_assessment_ids,
            known_ids=coherence_assessment_ids,
            reference_name="Coherence Assessment",
        )

    return True
