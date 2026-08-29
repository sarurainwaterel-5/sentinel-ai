import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.semantic_relationship_evaluator import (
    SemanticPremiseRelationshipEvaluator,
    SemanticRelationshipAssessment,
)

from types import SimpleNamespace

from app.services.cognition.reasoning.models import (
    Premise,
)


def test_semantic_assessment_preserves_bounded_judgment():
    assessment = SemanticRelationshipAssessment(
        relationship="supports",
        basis=(
            "The source proposition provides information "
            "that increases support for the target proposition."
        ),
        confidence=0.82,
    )

    assert assessment.relationship == "supports"
    assert assessment.basis
    assert assessment.confidence == 0.82


def test_semantic_assessment_rejects_unknown_relationship():
    with pytest.raises(ValidationError):
        SemanticRelationshipAssessment(
            relationship="probably_related",
            basis="The propositions appear related.",
            confidence=0.7,
        )


def test_semantic_assessment_rejects_unbounded_confidence():
    with pytest.raises(ValidationError):
        SemanticRelationshipAssessment(
            relationship="supports",
            basis="Supported relationship.",
            confidence=1.2,
        )
class FakeCompletions:
    def __init__(self, assessment):
        self.assessment = assessment
        self.calls = []

    def parse(self, **kwargs):
        self.calls.append(kwargs)

        return SimpleNamespace(
            choices=[
                SimpleNamespace(
                    message=SimpleNamespace(
                        refusal=None,
                        parsed=self.assessment,
                    )
                )
            ]
        )


class FakeClient:
    def __init__(self, assessment):
        self.chat = SimpleNamespace(
            completions=FakeCompletions(
                assessment
            )
        )


def test_evaluator_returns_structured_semantic_assessment():
    expected = SemanticRelationshipAssessment(
        relationship="supports",
        basis=(
            "The source proposition provides information "
            "that increases support for the target."
        ),
        confidence=0.84,
    )

    client = FakeClient(expected)

    evaluator = SemanticPremiseRelationshipEvaluator(
        client=client,
        model="test-model",
    )

    source = Premise(
        premise_id="premise-1",
        statement=(
            "The reasoning system preserves "
            "evidence provenance."
        ),
        evidence_ids=["evidence-1"],
    )

    target = Premise(
        premise_id="premise-2",
        statement=(
            "Reasoning outputs remain traceable "
            "to supporting evidence."
        ),
        evidence_ids=["evidence-2"],
    )

    result = evaluator.evaluate(
        source=source,
        target=target,
    )

    assert result == expected

    calls = (
        client.chat.completions.calls
    )

    assert len(calls) == 1

    assert calls[0]["model"] == "test-model"

    assert calls[0]["response_format"] is (
        SemanticRelationshipAssessment
    )
