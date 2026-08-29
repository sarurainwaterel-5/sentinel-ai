from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationshipKind,
)

from app.services.cognition.reasoning.premise_relationship_assessor import (
    PremiseRelationshipAssessor,
)

from app.services.cognition.reasoning.semantic_relationship_evaluator import (
    SemanticRelationshipAssessment,
)

from app.services.cognition.reasoning.semantic_relationship_policy import (
    SemanticRelationshipPolicy,
)


def test_unresolved_is_returned_when_relationship_cannot_be_established():
    premise_one = Premise(
        premise_id="premise-1",
        statement=(
            "SentinelAI preserves evidence provenance "
            "throughout reasoning."
        ),
        evidence_ids=["evidence-1"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement=(
            "The system exposes a responsive user interface."
        ),
        evidence_ids=["evidence-2"],
    )

    assessor = PremiseRelationshipAssessor()

    relationship = assessor.assess(
        source=premise_one,
        target=premise_two,
    )

    assert relationship.source_premise_id == (
        "premise-1"
    )

    assert relationship.target_premise_id == (
        "premise-2"
    )

    assert relationship.kind == (
        PremiseRelationshipKind.UNRESOLVED
    )

    assert relationship.confidence == 0.0

    assert relationship.basis

def test_distinct_known_domains_establish_independence():
    premise_one = Premise(
        premise_id="premise-1",
        statement=(
            "Liquidity sweeps may precede "
            "institutional displacement."
        ),
        evidence_ids=["evidence-1"],
        domain_ids=["trading"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement=(
            "Container health checks expose "
            "application availability."
        ),
        evidence_ids=["evidence-2"],
        domain_ids=["software-reliability"],
    )

    assessor = PremiseRelationshipAssessor()

    relationship = assessor.assess(
        source=premise_one,
        target=premise_two,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.INDEPENDENT
    )

    assert relationship.confidence > 0.0

    assert "domain" in (
        relationship.basis.casefold()
    )
def test_missing_domain_information_remains_unresolved():
    premise_one = Premise(
        premise_id="premise-1",
        statement="First proposition.",
        evidence_ids=["evidence-1"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Second proposition.",
        evidence_ids=["evidence-2"],
    )

    assessor = PremiseRelationshipAssessor()

    relationship = assessor.assess(
        source=premise_one,
        target=premise_two,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.UNRESOLVED
    )

class FakeSemanticEvaluator:
    def __init__(
        self,
        assessment,
    ):
        self.assessment = assessment
        self.calls = []

    def evaluate(
        self,
        *,
        source,
        target,
    ):
        self.calls.append(
            (source, target)
        )

        return self.assessment


def test_semantic_assessment_is_governed_and_promoted():
    source = Premise(
        premise_id="premise-1",
        statement=(
            "The system preserves evidence "
            "provenance."
        ),
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    target = Premise(
        premise_id="premise-2",
        statement=(
            "Reasoning outputs remain traceable "
            "to supporting evidence."
        ),
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    evaluator = FakeSemanticEvaluator(
        SemanticRelationshipAssessment(
            relationship="supports",
            basis=(
                "The source materially increases "
                "support for the target."
            ),
            confidence=0.84,
        )
    )

    policy = SemanticRelationshipPolicy(
        minimum_confidence=0.75,
    )

    assessor = PremiseRelationshipAssessor(
        semantic_evaluator=evaluator,
        semantic_policy=policy,
    )

    relationship = assessor.assess(
        source=source,
        target=target,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.SUPPORTS
    )

    assert relationship.confidence == 0.84

    assert len(evaluator.calls) == 1

def test_structural_relationship_precedes_semantic_assessment():
    source = Premise(
        premise_id="premise-1",
        statement=(
            "Liquidity sweeps may precede "
            "institutional displacement."
        ),
        evidence_ids=["evidence-1"],
        domain_ids=["trading"],
    )

    target = Premise(
        premise_id="premise-2",
        statement=(
            "Container health checks expose "
            "application availability."
        ),
        evidence_ids=["evidence-2"],
        domain_ids=["software-reliability"],
    )

    evaluator = FakeSemanticEvaluator(
        SemanticRelationshipAssessment(
            relationship="supports",
            basis=(
                "The source supposedly supports "
                "the target."
            ),
            confidence=0.99,
        )
    )

    policy = SemanticRelationshipPolicy(
        minimum_confidence=0.75,
    )

    assessor = PremiseRelationshipAssessor(
        semantic_evaluator=evaluator,
        semantic_policy=policy,
    )

    relationship = assessor.assess(
        source=source,
        target=target,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.INDEPENDENT
    )

    assert relationship.confidence == 0.8

    assert evaluator.calls == []
