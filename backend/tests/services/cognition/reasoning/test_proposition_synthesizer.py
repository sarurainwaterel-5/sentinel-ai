from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)
from app.services.cognition.reasoning.proposition_synthesizer import (
    PropositionSynthesizer,
)


class FakePropositionGenerator:
    def __init__(
        self,
        statement,
    ):
        self.statement = statement
        self.calls = []

    def synthesize(
        self,
        *,
        premises,
        relationships,
    ):
        self.calls.append(
            {
                "premises": premises,
                "relationships": relationships,
            }
        )

        return self.statement


def test_synthesizer_derives_proposition_from_related_premises():
    premise_one = Premise(
        premise_id="premise-1",
        statement=(
            "The system preserves evidence provenance."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "reasoning",
        ],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement=(
            "Reasoning outputs remain traceable "
            "to supporting evidence."
        ),
        evidence_ids=[
            "evidence-2",
        ],
        domain_ids=[
            "reasoning",
        ],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis=(
            "The source proposition materially supports "
            "the target proposition."
        ),
        confidence=0.84,
    )

    generator = FakePropositionGenerator(
        (
            "Preserving evidence provenance enables "
            "reasoning outputs to remain traceable "
            "to their supporting evidence."
        )
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert len(propositions) == 1

    proposition = propositions[0]

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

    assert proposition.statement not in {
        premise_one.statement,
        premise_two.statement,
    }

    assert proposition.statement == (
        "Preserving evidence provenance enables "
        "reasoning outputs to remain traceable "
        "to their supporting evidence."
    )

    assert len(generator.calls) == 1


def test_synthesizer_requires_multiple_premises():
    premise = Premise(
        premise_id="premise-1",
        statement=(
            "The system preserves evidence provenance."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "reasoning",
        ],
    )

    generator = FakePropositionGenerator(
        "This statement should never be generated."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise,
        ],
        relationships=[],
    )

    assert propositions == []
    assert generator.calls == []


def test_synthesizer_ignores_independent_relationships():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.INDEPENDENT,
        basis="The premises do not materially inform one another.",
        confidence=0.91,
    )

    generator = FakePropositionGenerator(
        "This statement should never be generated."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[premise_one, premise_two],
        relationships=[relationship],
    )

    assert propositions == []
    assert generator.calls == []


def test_synthesizer_ignores_unresolved_relationships():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.UNRESOLVED,
        basis="The relationship cannot be established reliably.",
        confidence=0.42,
    )

    generator = FakePropositionGenerator(
        "This statement should never be generated."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[premise_one, premise_two],
        relationships=[relationship],
    )

    assert propositions == []
    assert generator.calls == []


def test_synthesizer_ignores_relationships_with_unknown_premise_ids():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-missing",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis="The source appears to support the missing target.",
        confidence=0.88,
    )

    generator = FakePropositionGenerator(
        "This statement should never be generated."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert propositions == []
    assert generator.calls == []


def test_synthesizer_deduplicates_evidence_and_domain_ids():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=[
            "evidence-1",
            "evidence-shared",
        ],
        domain_ids=[
            "reasoning",
            "shared-domain",
        ],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=[
            "evidence-2",
            "evidence-shared",
        ],
        domain_ids=[
            "reasoning",
            "shared-domain",
        ],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis="Premise one materially supports premise two.",
        confidence=0.90,
    )

    generator = FakePropositionGenerator(
        "A synthesized proposition."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert len(propositions) == 1

    proposition = propositions[0]

    assert proposition.evidence_ids == [
        "evidence-1",
        "evidence-shared",
        "evidence-2",
    ]

    assert proposition.domain_ids == [
        "reasoning",
        "shared-domain",
    ]


def test_synthesizer_rejects_empty_generated_statement():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis="Premise one supports premise two.",
        confidence=0.89,
    )

    generator = FakePropositionGenerator("   ")

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert propositions == []
    assert len(generator.calls) == 1


def test_synthesizer_preserves_conflicting_relationship_context():
    premise_one = Premise(
        premise_id="premise-1",
        statement="The service is healthy.",
        evidence_ids=["evidence-1"],
        domain_ids=["operations"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="The service is experiencing elevated failures.",
        evidence_ids=["evidence-2"],
        domain_ids=["operations"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.CONFLICTS,
        basis=(
            "The two premises present materially "
            "inconsistent operational states."
        ),
        confidence=0.94,
    )

    generator = FakePropositionGenerator(
        (
            "The available evidence presents conflicting "
            "signals about the service health state."
        )
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert len(propositions) == 1

    proposition = propositions[0]

    assert proposition.premise_ids == [
        "premise-1",
        "premise-2",
    ]

    assert proposition.evidence_ids == [
        "evidence-1",
        "evidence-2",
    ]

    assert proposition.statement == (
        "The available evidence presents conflicting "
        "signals about the service health state."
    )

    assert proposition.metadata["relationship_kinds"] == [
        "conflicts",
    ]


def test_synthesizer_preserves_conflicting_relationship_context():
    premise_one = Premise(
        premise_id="premise-1",
        statement="The service is healthy.",
        evidence_ids=["evidence-1"],
        domain_ids=["operations"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="The service is experiencing elevated failures.",
        evidence_ids=["evidence-2"],
        domain_ids=["operations"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.CONFLICTS,
        basis=(
            "The two premises present materially "
            "inconsistent operational states."
        ),
        confidence=0.94,
    )

    generator = FakePropositionGenerator(
        (
            "The available evidence presents conflicting "
            "signals about the service health state."
        )
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
        ],
        relationships=[
            relationship,
        ],
    )

    assert len(propositions) == 1

    proposition = propositions[0]

    assert proposition.premise_ids == [
        "premise-1",
        "premise-2",
    ]

    assert proposition.evidence_ids == [
        "evidence-1",
        "evidence-2",
    ]

    assert proposition.statement == (
        "The available evidence presents conflicting "
        "signals about the service health state."
    )

    assert proposition.metadata["relationship_kinds"] == [
        "conflicts",
    ]


def test_synthesizer_handles_multiple_relationships_across_three_premises():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Premise one.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Premise two.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    premise_three = Premise(
        premise_id="premise-3",
        statement="Premise three.",
        evidence_ids=["evidence-3"],
        domain_ids=["reasoning"],
    )

    relationship_one = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis="Premise one supports premise two.",
        confidence=0.90,
    )

    relationship_two = PremiseRelationship(
        source_premise_id="premise-2",
        target_premise_id="premise-3",
        kind=PremiseRelationshipKind.COMPLEMENTS,
        basis="Premise two complements premise three.",
        confidence=0.87,
    )

    generator = FakePropositionGenerator(
        "A higher-order proposition derived from three premises."
    )

    synthesizer = PropositionSynthesizer(
        semantic_generator=generator,
    )

    propositions = synthesizer.synthesize(
        premises=[
            premise_one,
            premise_two,
            premise_three,
        ],
        relationships=[
            relationship_one,
            relationship_two,
        ],
    )

    assert len(propositions) == 1

    proposition = propositions[0]

    assert proposition.premise_ids == [
        "premise-1",
        "premise-2",
        "premise-3",
    ]

    assert proposition.evidence_ids == [
        "evidence-1",
        "evidence-2",
        "evidence-3",
    ]

    assert proposition.metadata["relationship_kinds"] == [
        "supports",
        "complements",
    ]

    assert len(generator.calls) == 1

    call = generator.calls[0]

    assert [
        premise.premise_id
        for premise in call["premises"]
    ] == [
        "premise-1",
        "premise-2",
        "premise-3",
    ]

    assert call["relationships"] == [
        relationship_one,
        relationship_two,
    ]
