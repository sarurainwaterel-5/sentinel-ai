from app.services.cognition.reasoning.models import (
    SynthesizedProposition,
)


def test_synthesized_proposition_preserves_premise_lineage():
    proposition = SynthesizedProposition(
        proposition_id="proposition-1",
        statement=(
            "Traceable evidence supports "
            "inspectable reasoning."
        ),
        premise_ids=[
            "premise-1",
            "premise-2",
        ],
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        domain_ids=[
            "reasoning",
        ],
    )

    assert proposition.proposition_id == (
        "proposition-1"
    )

    assert proposition.statement == (
        "Traceable evidence supports "
        "inspectable reasoning."
    )

    assert proposition.premise_ids == [
        "premise-1",
        "premise-2",
    ]

    assert proposition.evidence_ids == [
        "evidence-1",
        "evidence-2",
    ]

    assert proposition.domain_ids == [
        "reasoning",
    ]


import pytest
from pydantic import ValidationError


def test_synthesized_proposition_requires_multiple_premises():
    with pytest.raises(ValidationError):
        SynthesizedProposition(
            proposition_id="proposition-1",
            statement=(
                "A single premise cannot constitute "
                "proposition synthesis."
            ),
            premise_ids=[
                "premise-1",
            ],
            evidence_ids=[
                "evidence-1",
            ],
        )
