"""
Contract tests for SentinelAI's VerificationEngine.

The VerificationEngine coordinates specialist verification, coverage,
confidence, and final verification status.

It does not perform specialist verification logic directly.
"""

from app.services.cognition.planning.models import (
    PlanningComplexity,
    PlanningConfidence,
    PlanningConfidenceLevel,
    PlanningObjective,
    PlanningReasoningBasis,
    PlanningResult,
    PlanningRisk,
    PlanningStatus,
    PlanningStep,
    PlanningStrategy,
    RiskLevel,
)
from app.services.cognition.verification.models import (
    VerificationContext,
    VerificationStatus,
)
from app.services.cognition.verification.verification_engine import (
    VerificationEngine,
)


def build_clean_plan() -> PlanningResult:
    conclusion = (
        "A staged upgrade with validation between transitions "
        "reduces operational exposure."
    )

    constraints = [
        "Require human approval before change.",
    ]

    return PlanningResult(
        objective=PlanningObjective(
            statement="Upgrade the service safely.",
            desired_outcome="Upgrade the service safely.",
            constraints=constraints,
        ),
        reasoning_basis=PlanningReasoningBasis(
            question="How should the service be upgraded?",
            conclusion=conclusion,
            confidence_score=0.86,
            confidence_level="high",
            reasoning_status="complete",
        ),
        strategy=PlanningStrategy(
            name="Phased verification-led strategy",
            description=(
                "Advance through bounded upgrade phases."
            ),
            rationale=(
                "Bounded phases reduce operational exposure."
            ),
            supported_by_reasoning=[
                conclusion,
            ],
            suitability_score=0.88,
        ),
        steps=[
            PlanningStep(
                step_id="step-1",
                sequence=1,
                title="Validate prerequisites",
                description=(
                    "Confirm readiness before change."
                ),
                rationale=(
                    "The staged strategy requires known-safe "
                    "starting conditions."
                ),
                risk_ids=[
                    "risk-1",
                ],
                completion_criteria=[
                    "Readiness is confirmed.",
                ],
                requires_human_approval=True,
            ),
        ],
        constraints=constraints,
        risks=[
            PlanningRisk(
                risk_id="risk-1",
                description="The upgrade may fail.",
                likelihood=RiskLevel.MODERATE,
                impact=RiskLevel.HIGH,
                affected_step_ids=[
                    "step-1",
                ],
                mitigation="Validate before change.",
                contingency="Rollback to the prior version.",
            ),
        ],
        success_criteria=[
            "The upgraded service remains healthy.",
        ],
        estimated_complexity=PlanningComplexity.MEDIUM,
        confidence=PlanningConfidence(
            score=0.81,
            level=PlanningConfidenceLevel.HIGH,
            basis=(
                "The plan is structured, bounded, and supported."
            ),
        ),
        status=PlanningStatus.COMPLETE,
    )


def test_clean_plan_returns_verified():
    plan = build_clean_plan()

    result = VerificationEngine().verify(
        context=VerificationContext(
            subject=plan,
            governing_constraints=[
                "Require human approval before change.",
            ],
        )
    )

    assert result.status == VerificationStatus.VERIFIED
    assert result.coverage.coverage_score == 1.0
    assert result.confidence.level.value == "high"
    assert result.findings == []
    assert result.conditions == []
    assert result.checks
    assert result.standards

    print()
    print("Clean verification branch passed.")


def test_defective_plan_returns_requires_revision():
    plan = build_clean_plan()

    broken = plan.model_copy(
        update={
            "success_criteria": [],
        },
    )

    result = VerificationEngine().verify(
        context=VerificationContext(
            subject=broken,
            governing_constraints=[
                "Require human approval before change.",
            ],
        )
    )

    assert (
        result.status
        == VerificationStatus.REQUIRES_REVISION
    )
    assert result.findings
    assert result.conditions

    assert any(
        finding.blocking
        for finding in result.findings
    )

    print()
    print("Requires-revision branch passed.")


def test_missing_reasoning_basis_returns_insufficient_basis():
    plan = build_clean_plan()

    broken_reasoning = plan.reasoning_basis.model_copy(
        update={
            "conclusion": None,
            "reasoning_status": "insufficient_evidence",
        },
    )

    broken = plan.model_copy(
        update={
            "reasoning_basis": broken_reasoning,
        },
    )

    result = VerificationEngine().verify(
        context=VerificationContext(
            subject=broken,
            governing_constraints=[
                "Require human approval before change.",
            ],
        )
    )

    assert (
        result.status
        == VerificationStatus.INSUFFICIENT_BASIS
    )

    assert result.coverage.unverifiable_count >= 1
    assert result.confidence.uncertainty

    print()
    print("Insufficient-basis branch passed.")
