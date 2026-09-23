import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.models import (
    CandidateRelationshipReference,
    CandidateProposition,
    PremiseRelationshipKind,
)


def test_candidate_proposition_preserves_untrusted_candidate_data():
    candidate = CandidateProposition(
        statement="Premise A and Premise B jointly support C.",
        premise_ids=["premise-a", "premise-b"],
        relationship_references=[
            CandidateRelationshipReference(
                source_premise_id="premise-a",
                target_premise_id="premise-b",
                kind=PremiseRelationshipKind.SUPPORTS,
            )
        ],
        qualifications=["Subject to the supplied evidence."],
        generator_metadata={"provider": "test"},
    )

    assert candidate.statement == (
        "Premise A and Premise B jointly support C."
    )
    assert candidate.premise_ids == [
        "premise-a",
        "premise-b",
    ]
    assert candidate.relationship_references == [
        CandidateRelationshipReference(
            source_premise_id="premise-a",
            target_premise_id="premise-b",
            kind=PremiseRelationshipKind.SUPPORTS,
        ),
    ]
    assert candidate.qualifications == [
        "Subject to the supplied evidence."
    ]
    assert candidate.generator_metadata == {
        "provider": "test",
    }


def test_candidate_proposition_requires_non_empty_statement():
    with pytest.raises(ValidationError):
        CandidateProposition(
            statement="",
            premise_ids=["premise-a", "premise-b"],
        )


def test_candidate_proposition_requires_at_least_two_premises():
    with pytest.raises(ValidationError):
        CandidateProposition(
            statement="Candidate statement.",
            premise_ids=["premise-a"],
        )


def test_candidate_proposition_defaults_optional_metadata():
    candidate = CandidateProposition(
        statement="Candidate statement.",
        premise_ids=["premise-a", "premise-b"],
    )

    assert candidate.relationship_references == []
    assert candidate.qualifications == []
    assert candidate.generator_metadata == {}


@pytest.mark.parametrize(
    "reference",
    [
        {"source_premise_id": "", "target_premise_id": "b", "kind": "supports"},
        {"source_premise_id": "a", "target_premise_id": "a", "kind": "supports"},
        {"source_premise_id": "a", "target_premise_id": "b", "kind": "invented"},
    ],
)
def test_candidate_rejects_malformed_relationship_reference(reference):
    with pytest.raises(ValidationError):
        CandidateProposition(
            statement="Candidate statement.",
            premise_ids=["a", "b"],
            relationship_references=[reference],
        )


def test_candidate_rejects_nonexistent_relationship_ids():
    with pytest.raises(ValidationError):
        CandidateProposition(
            statement="Candidate statement.",
            premise_ids=["a", "b"],
            relationship_ids=["invented-id"],
        )
