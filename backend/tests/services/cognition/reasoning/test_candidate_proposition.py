import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.models import (
    CandidateProposition,
)


def test_candidate_proposition_preserves_untrusted_candidate_data():
    candidate = CandidateProposition(
        statement="Premise A and Premise B jointly support C.",
        premise_ids=["premise-a", "premise-b"],
        relationship_ids=["relationship-a-b"],
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
    assert candidate.relationship_ids == [
        "relationship-a-b",
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

    assert candidate.relationship_ids == []
    assert candidate.qualifications == []
    assert candidate.generator_metadata == {}
