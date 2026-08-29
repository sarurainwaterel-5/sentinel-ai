from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationshipKind,
)

from app.services.cognition.reasoning.semantic_relationship_evaluator import (
    SemanticRelationshipAssessment,
)

from app.services.cognition.reasoning.semantic_relationship_policy import (
    SemanticRelationshipPolicy,
)


def test_low_confidence_semantic_assessment_is_not_promoted():
    source = Premise(
        premise_id="premise-1",
        statement="Source proposition.",
        evidence_ids=["evidence-1"],
    )

    target = Premise(
        premise_id="premise-2",
        statement="Target proposition.",
        evidence_ids=["evidence-2"],
    )

    assessment = SemanticRelationshipAssessment(
        relationship="supports",
        basis=(
            "The source appears to provide some "
            "support for the target."
        ),
        confidence=0.55,
    )

    policy = SemanticRelationshipPolicy(
        minimum_confidence=0.75,
    )

    relationship = policy.promote(
        source=source,
        target=target,
        assessment=assessment,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.UNRESOLVED
    )

    assert relationship.confidence == 0.0

    assert "confidence" in (
        relationship.basis.casefold()
    )
def test_admissible_semantic_assessment_is_promoted_without_rewriting():
    source = Premise(
        premise_id="premise-1",
        statement="Source proposition.",
        evidence_ids=["evidence-1"],
    )

    target = Premise(
        premise_id="premise-2",
        statement="Target proposition.",
        evidence_ids=["evidence-2"],
    )

    assessment = SemanticRelationshipAssessment(
        relationship="supports",
        basis=(
            "The source materially increases support "
            "for the target proposition."
        ),
        confidence=0.84,
    )

    policy = SemanticRelationshipPolicy(
        minimum_confidence=0.75,
    )

    relationship = policy.promote(
        source=source,
        target=target,
        assessment=assessment,
    )

    assert relationship.source_premise_id == (
        "premise-1"
    )

    assert relationship.target_premise_id == (
        "premise-2"
    )

    assert relationship.kind == (
        PremiseRelationshipKind.SUPPORTS
    )

    assert relationship.basis == (
        assessment.basis
    )

    assert relationship.confidence == (
        assessment.confidence
    )
