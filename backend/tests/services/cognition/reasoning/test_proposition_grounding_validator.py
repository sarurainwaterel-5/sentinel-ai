import pytest

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    CandidateRelationshipReference,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)
from app.services.cognition.reasoning.proposition_grounding_validator import (
    PropositionGroundingValidator,
)


def premise(identifier, evidence=None):
    return Premise(
        premise_id=identifier,
        statement=f"Statement {identifier}.",
        evidence_ids=evidence if evidence is not None else [f"e-{identifier}"],
        domain_ids=["domain"],
    )


def relationship(source="a", target="b", kind=PremiseRelationshipKind.SUPPORTS):
    return PremiseRelationship(
        source_premise_id=source,
        target_premise_id=target,
        kind=kind,
        basis="Trusted assessment, never supplied by the candidate.",
        confidence=0.73,
    )


def reference(source="a", target="b", kind=PremiseRelationshipKind.SUPPORTS):
    return CandidateRelationshipReference(
        source_premise_id=source, target_premise_id=target, kind=kind
    )


def candidate(ids=None, references=None, **kwargs):
    return CandidateProposition(
        statement="Untrusted generated statement.",
        premise_ids=ids if ids is not None else ["a", "b"],
        relationship_references=references if references is not None else [reference()],
        **kwargs,
    )


def validate(proposed=None, premises=None, relationships=None):
    return PropositionGroundingValidator().validate(
        candidate=proposed if proposed is not None else candidate(),
        premises=premises if premises is not None else [premise("a"), premise("b")],
        relationships=relationships if relationships is not None else [relationship()],
    )


def test_valid_reference_reconstructs_only_trusted_lineage():
    result = validate(
        proposed=candidate(generator_metadata={"evidence_ids": ["fabricated"],
                                               "basis": "fabricated", "confidence": 1.0}),
        premises=[premise("a", ["shared", "e-a"]), premise("b", ["shared", "e-b"])],
    )
    assert result.structurally_valid
    assert result.rejection_reasons == ()
    assert result.premise_ids == ("a", "b")
    assert result.evidence_ids == ("shared", "e-a", "e-b")
    assert result.domain_ids == ("domain",)
    assert result.relationships == (relationship(),)
    assert result.relationships[0].confidence == 0.73
    assert result.semantic_grounding_verified is False


@pytest.mark.parametrize(
    ("proposed", "trusted_premises", "trusted_relationships", "reason"),
    [
        (candidate(ids=["a", "missing"]), None, None, "unknown_premise_reference"),
        (candidate(ids=["a", "a"]), None, None, "insufficient_distinct_premises"),
        (candidate(), [premise("a", [""]), premise("b")], None, "missing_evidence_lineage"),
        (candidate(references=[]), None, None, "missing_relationship_reference"),
        (candidate(references=[reference("b", "a")]), None, None,
         "unknown_or_reversed_relationship"),
        (candidate(references=[reference(kind=PremiseRelationshipKind.SUPPORTS)]),
         None, [relationship(kind=PremiseRelationshipKind.CONFLICTS)],
         "relationship_kind_mismatch"),
        (candidate(references=[reference("a", "missing")]), None, None,
         "relationship_outside_candidate_premises"),
        (candidate(ids=["a", "b", "c"]),
         [premise("a"), premise("b"), premise("c")], None,
         "unconnected_premise_reference"),
    ],
)
def test_invalid_references_fail_closed(
    proposed, trusted_premises, trusted_relationships, reason
):
    result = validate(proposed, trusted_premises, trusted_relationships)
    assert result.structurally_valid is False
    assert reason in result.rejection_reasons
    assert result.evidence_ids == ()
    assert result.relationships == ()


@pytest.mark.parametrize("kind", [PremiseRelationshipKind.INDEPENDENT,
                                  PremiseRelationshipKind.UNRESOLVED])
def test_policy_excludes_independent_and_unresolved(kind):
    result = validate(candidate(references=[reference(kind=kind)]),
                      relationships=[relationship(kind=kind)])
    assert result.structurally_valid is False
    assert "inadmissible_relationship_kind" in result.rejection_reasons


def test_conflict_is_preserved_without_becoming_support():
    result = validate(candidate(references=[reference(kind=PremiseRelationshipKind.CONFLICTS)]),
                      relationships=[relationship(kind=PremiseRelationshipKind.CONFLICTS)])
    assert result.structurally_valid
    assert result.relationships[0].kind is PremiseRelationshipKind.CONFLICTS


def test_unreferenced_conflict_between_participants_fails_closed():
    result = validate(
        candidate(references=[reference()]),
        relationships=[relationship(), relationship("b", "a", PremiseRelationshipKind.CONFLICTS)],
    )
    assert "suppressed_conflict" in result.rejection_reasons


def test_duplicate_references_are_deduplicated_in_input_order():
    result = validate(candidate(ids=["a", "b", "a"],
                                references=[reference(), reference()]))
    assert result.structurally_valid
    assert result.premise_ids == ("a", "b")
    assert result.relationships == (relationship(),)


def test_ambiguous_trusted_artifacts_fail_closed():
    altered = premise("a", ["different"])
    result = validate(premises=[premise("a"), altered, premise("b")])
    assert "ambiguous_trusted_premise" in result.rejection_reasons
    result = validate(relationships=[relationship(), relationship(kind=PremiseRelationshipKind.CONFLICTS)])
    assert "ambiguous_trusted_relationship" in result.rejection_reasons


def test_structural_pass_does_not_certify_unsupported_statement():
    result = validate(candidate())
    assert result.structurally_valid
    assert result.semantic_grounding_verified is False


def test_whitespace_statement_fails_closed():
    proposed = candidate().model_copy(update={"statement": "   "})
    result = validate(proposed)
    assert result.structurally_valid is False
    assert "blank_candidate_statement" in result.rejection_reasons
