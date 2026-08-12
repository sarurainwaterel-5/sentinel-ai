"""
Contract tests for SentinelAI's VerificationConfidenceEngine.

Verification confidence evaluates the reliability and completeness of the
inspection process itself.

It does not evaluate whether the underlying PlanningResult is good.

A verification operation may therefore have high confidence while
correctly reporting failed checks against a poor plan.
"""

from app.services.cognition.verification.models import (
    VerificationCategory,
    VerificationCheck,
    VerificationInspection,
    VerificationOutcome,
    VerificationSeverity,
    VerificationStandard,
)
from app.services.cognition.verification.verification_confidence_engine import (
    VerificationConfidenceEngine,
)
from app.services.cognition.verification.verification_coverage_engine import (
    VerificationCoverageEngine,
)


def make_inspection(
    *,
    category: VerificationCategory,
    outcome: VerificationOutcome = VerificationOutcome.PASSED,
    completed: bool = True,
    with_trace: bool = True,
) -> VerificationInspection:
    """
    Build one valid specialist inspection fixture.
    """

    suffix = category.value

    standard = VerificationStandard(
        standard_id=f"standard-{suffix}",
        category=category,
        title=f"{suffix} standard",
        description=f"Verify {suffix}.",
    )

    check = VerificationCheck(
        check_id=f"check-{suffix}",
        category=category,
        standard_id=standard.standard_id,
        observation=f"{suffix} was inspected.",
        outcome=outcome,
        severity=(
            VerificationSeverity.INFORMATIONAL
            if outcome == VerificationOutcome.PASSED
            else VerificationSeverity.HIGH
        ),
        uncertainty=(
            ["The check could not be conclusively verified."]
            if outcome == VerificationOutcome.NOT_VERIFIABLE
            else []
        ),
    )

    return VerificationInspection(
        category=category,
        standards=[standard],
        checks=[check],
        findings=[],
        conditions=[],
        inspection_trace=(
            [f"Inspected {suffix}."]
            if with_trace
            else []
        ),
        completed=completed,
    )


def assess(
    *,
    requested_categories: list[VerificationCategory],
    inspections: list[VerificationInspection],
):
    """
    Produce coverage first, then assess verification confidence.
    """

    coverage = VerificationCoverageEngine().assess(
        requested_categories=requested_categories,
        inspections=inspections,
    )

    confidence = VerificationConfidenceEngine().assess(
        coverage=coverage,
        inspections=inspections,
    )

    return coverage, confidence


def test_complete_verification_produces_high_confidence():
    """
    Full category coverage with inspectable completed checks should
    produce high verification confidence.
    """

    categories = [
        VerificationCategory.STRUCTURAL_INTEGRITY,
        VerificationCategory.TRACEABILITY,
        VerificationCategory.COMPLETENESS,
        VerificationCategory.CONSTRAINT_COMPLIANCE,
    ]

    inspections = [
        make_inspection(category=category)
        for category in categories
    ]

    coverage, confidence = assess(
        requested_categories=categories,
        inspections=inspections,
    )

    assert coverage.coverage_score == 1.0
    assert coverage.skipped_categories == []

    assert confidence.level.value == "high"
    assert confidence.score >= 0.80

    assert confidence.factors
    assert confidence.uncertainty == []


def test_skipped_category_reduces_verification_confidence():
    """
    Missing requested verification coverage must reduce confidence in
    the inspection.
    """

    categories = [
        VerificationCategory.STRUCTURAL_INTEGRITY,
        VerificationCategory.TRACEABILITY,
        VerificationCategory.COMPLETENESS,
        VerificationCategory.CONSTRAINT_COMPLIANCE,
    ]

    complete_inspections = [
        make_inspection(category=category)
        for category in categories
    ]

    partial_inspections = complete_inspections[:-1]

    _, complete_confidence = assess(
        requested_categories=categories,
        inspections=complete_inspections,
    )

    partial_coverage, partial_confidence = assess(
        requested_categories=categories,
        inspections=partial_inspections,
    )

    assert partial_coverage.skipped_categories == [
        VerificationCategory.CONSTRAINT_COMPLIANCE,
    ]

    assert (
        partial_confidence.score
        < complete_confidence.score
    )

    assert partial_confidence.uncertainty


def test_unverifiable_checks_reduce_confidence_and_preserve_uncertainty():
    """
    NOT_VERIFIABLE checks represent uncertainty in the inspection itself
    and must reduce verification confidence.
    """

    categories = [
        VerificationCategory.STRUCTURAL_INTEGRITY,
        VerificationCategory.TRACEABILITY,
        VerificationCategory.COMPLETENESS,
    ]

    reliable_inspections = [
        make_inspection(
            category=VerificationCategory.STRUCTURAL_INTEGRITY,
        ),
        make_inspection(
            category=VerificationCategory.TRACEABILITY,
        ),
        make_inspection(
            category=VerificationCategory.COMPLETENESS,
        ),
    ]

    uncertain_inspections = [
        make_inspection(
            category=VerificationCategory.STRUCTURAL_INTEGRITY,
        ),
        make_inspection(
            category=VerificationCategory.TRACEABILITY,
            outcome=VerificationOutcome.NOT_VERIFIABLE,
        ),
        make_inspection(
            category=VerificationCategory.COMPLETENESS,
            outcome=VerificationOutcome.NOT_VERIFIABLE,
        ),
    ]

    _, reliable_confidence = assess(
        requested_categories=categories,
        inspections=reliable_inspections,
    )

    uncertain_coverage, uncertain_confidence = assess(
        requested_categories=categories,
        inspections=uncertain_inspections,
    )

    assert uncertain_coverage.unverifiable_count == 2

    assert (
        uncertain_confidence.score
        < reliable_confidence.score
    )

    assert uncertain_confidence.uncertainty


def test_failed_checks_do_not_automatically_reduce_verification_confidence():
    """
    A failed subject check does not imply a poor verification operation.

    Sentinel may confidently determine that a plan contains defects.
    """

    categories = [
        VerificationCategory.STRUCTURAL_INTEGRITY,
        VerificationCategory.TRACEABILITY,
        VerificationCategory.COMPLETENESS,
    ]

    passing_inspections = [
        make_inspection(
            category=category,
            outcome=VerificationOutcome.PASSED,
        )
        for category in categories
    ]

    failing_inspections = [
        make_inspection(
            category=category,
            outcome=VerificationOutcome.FAILED,
        )
        for category in categories
    ]

    passing_coverage, passing_confidence = assess(
        requested_categories=categories,
        inspections=passing_inspections,
    )

    failing_coverage, failing_confidence = assess(
        requested_categories=categories,
        inspections=failing_inspections,
    )

    assert passing_coverage.failed_count == 0
    assert failing_coverage.failed_count == 3

    assert (
        failing_confidence.score
        == passing_confidence.score
    )

    assert failing_confidence.level == passing_confidence.level
