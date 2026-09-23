"""Adversarial checks for the synthesizer's promotion boundary."""

import pytest

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    CandidateRelationshipReference,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)
from app.services.cognition.reasoning.proposition_synthesizer import (
    PropositionSynthesizer,
)


def inputs(kind=PremiseRelationshipKind.SUPPORTS):
    premises = [
        Premise(premise_id="a", statement="A.", evidence_ids=["e-a"]),
        Premise(premise_id="b", statement="B.", evidence_ids=["e-b"]),
    ]
    relationship = PremiseRelationship(
        source_premise_id="a", target_premise_id="b", kind=kind,
        basis="Trusted basis.", confidence=0.62,
    )
    return premises, [relationship]


def candidate(kind=PremiseRelationshipKind.SUPPORTS, **changes):
    data = dict(
        statement="Untrusted semantic claim.",
        premise_ids=["a", "b"],
        relationship_references=[CandidateRelationshipReference(
            source_premise_id="a", target_premise_id="b", kind=kind,
        )],
        generator_metadata={"evidence_ids": ["forged"], "confidence": 1.0},
    )
    data.update(changes)
    return CandidateProposition(**data)


class Generator:
    def __init__(self, value):
        self.value = value

    def generate(self, *, premises, relationships):
        if isinstance(self.value, Exception):
            raise self.value
        return self.value


def outcome(value, *, premises=None, relationships=None):
    default_premises, default_relationships = inputs()
    return PropositionSynthesizer(
        semantic_generator=Generator(value),
    ).synthesize_with_validation(
        premises=premises if premises is not None else default_premises,
        relationships=relationships if relationships is not None else default_relationships,
    )


def test_accepted_candidate_retains_explicit_semantic_boundary():
    result = outcome(candidate())
    assert len(result.propositions) == 1
    assert result.validation.structurally_valid
    assert result.validation.semantic_grounding_verified is False
    assert result.propositions[0].metadata["semantic_grounding_verified"] is False


def test_accepted_candidate_uses_reconstructed_provenance():
    result = outcome(candidate())
    assert result.rejection_reasons == ()
    assert len(result.propositions) == 1
    proposition = result.propositions[0]
    assert proposition.evidence_ids == ["e-a", "e-b"]
    assert proposition.metadata == {
        "relationship_kinds": ["supports"],
        "semantic_grounding_verified": False,
    }


@pytest.mark.parametrize(
    ("value", "reason"),
    [
        (RuntimeError("model unavailable"), "generator_failure"),
        (None, "invalid_candidate"),
        ("Raw statement from legacy generator", "invalid_candidate"),
        (candidate(premise_ids=["a", "missing"]), "unknown_premise_reference"),
        (candidate(kind=PremiseRelationshipKind.CONFLICTS), "relationship_kind_mismatch"),
        (candidate(relationship_references=[CandidateRelationshipReference(
            source_premise_id="b", target_premise_id="a",
            kind=PremiseRelationshipKind.SUPPORTS,
        )]), "unknown_or_reversed_relationship"),
    ],
)
def test_invalid_output_never_creates_fallback(value, reason):
    result = outcome(value)
    assert result.propositions == []
    assert reason in result.rejection_reasons
    if result.validation is not None:
        assert result.validation.structurally_valid is False


def test_conflict_cannot_be_recast_as_support():
    premises, relationships = inputs(PremiseRelationshipKind.CONFLICTS)
    result = outcome(candidate(), premises=premises, relationships=relationships)
    assert result.propositions == []
    assert "relationship_kind_mismatch" in result.rejection_reasons


def test_conflict_context_is_retained_after_validation():
    premises, relationships = inputs(PremiseRelationshipKind.CONFLICTS)
    result = outcome(candidate(PremiseRelationshipKind.CONFLICTS),
                     premises=premises, relationships=relationships)
    assert result.propositions[0].metadata["relationship_kinds"] == ["conflicts"]


@pytest.mark.parametrize("kind", [PremiseRelationshipKind.INDEPENDENT,
                                  PremiseRelationshipKind.UNRESOLVED])
def test_inadmissible_relationship_is_never_offered_for_synthesis(kind):
    premises, relationships = inputs(kind)
    result = outcome(candidate(kind), premises=premises, relationships=relationships)
    assert result.propositions == []
    assert result.rejection_reasons == ("no_eligible_relationships",)


def test_untrusted_metadata_and_qualifications_cannot_override_lineage():
    proposed = candidate(
        qualifications=["An unverified qualification."],
        generator_metadata={
            "premise_ids": ["forged"], "evidence_ids": ["forged"],
            "domain_ids": ["forged"], "relationship_kinds": ["conflicts"],
            "semantic_grounding_verified": True,
        },
    )
    result = outcome(proposed)
    proposition = result.propositions[0]
    assert proposition.premise_ids == ["a", "b"]
    assert proposition.evidence_ids == ["e-a", "e-b"]
    assert proposition.domain_ids == []
    assert proposition.metadata == {
        "relationship_kinds": ["supports"],
        "semantic_grounding_verified": False,
    }


def test_duplicate_provenance_is_normalized_in_first_seen_order():
    premises, relationships = inputs()
    premises[0].evidence_ids = ["shared", "e-a", "shared"]
    premises[1].evidence_ids = ["shared", "e-b"]
    premises[0].domain_ids = ["domain", "domain"]
    premises[1].domain_ids = ["domain", "other"]
    result = outcome(candidate(premise_ids=["a", "b", "a"],
                               relationship_references=[
                                   candidate().relationship_references[0],
                                   candidate().relationship_references[0],
                               ]), premises=premises, relationships=relationships)
    assert result.propositions[0].evidence_ids == ["shared", "e-a", "e-b"]
    assert result.propositions[0].domain_ids == ["domain", "other"]
    assert result.propositions[0].premise_ids == ["a", "b"]
