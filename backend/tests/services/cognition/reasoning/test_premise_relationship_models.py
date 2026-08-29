import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.models import (
    PremiseRelationship,
    PremiseRelationshipKind,
)


def test_premise_relationship_preserves_direction_and_basis():
    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis=(
            "The source proposition provides evidence "
            "consistent with the target proposition."
        ),
        confidence=0.9,
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
    assert relationship.confidence == 0.9


def test_premise_relationship_requires_distinct_premises():
    with pytest.raises(ValidationError):
        PremiseRelationship(
            source_premise_id="premise-1",
            target_premise_id="premise-1",
            kind=PremiseRelationshipKind.SUPPORTS,
            basis="A premise cannot relate to itself.",
            confidence=1.0,
        )


def test_unresolved_relationship_is_valid():
    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.UNRESOLVED,
        basis=(
            "The available propositions do not provide "
            "enough information to establish a supported "
            "semantic relationship."
        ),
        confidence=0.0,
    )

    assert relationship.kind == (
        PremiseRelationshipKind.UNRESOLVED
    )

    assert relationship.confidence == 0.0

    assert relationship.basis


