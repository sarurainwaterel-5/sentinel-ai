"""20.3-G: explicit structural-only compatibility observations.

Passing these tests is not an entailment benchmark pass. Semantic attacks
with valid references pass only in explicit structural-only compatibility mode, but remain marked
unverified and are excluded from inference. Those cases document a known
limitation that must be closed before ADR-037 can be accepted for semantic use.
"""

import json

import pytest

from app.services.cognition.reasoning.models import (
    EvidenceBundle, EvidenceItem, EvidenceSource, Premise, PremiseRelationship,
)
from app.services.cognition.reasoning.proposition_synthesizer import PropositionSynthesizer
from app.services.cognition.reasoning.reasoning_engine import ReasoningEngine
from app.services.cognition.reasoning.semantic_generation_provider import (
    SemanticGenerationFailure, SemanticGenerationResponse,
)
from app.services.cognition.reasoning.semantic_proposition_generator import ProviderSemanticPropositionGenerator


def trusted_inputs():
    return (
        [Premise(premise_id="a", statement="Latency may increase under heavy load.",
                 evidence_ids=["doc-a:0"], domain_ids=["operations"]),
         Premise(premise_id="b", statement="High request volume was observed.",
                 evidence_ids=["doc-b:0"], domain_ids=["operations"])],
        [PremiseRelationship(source_premise_id="a", target_premise_id="b",
                             kind="complements", basis="Related observations, no causal claim.",
                             confidence=0.6)],
    )


def candidate(statement="Latency may increase under load; high request volume was observed."):
    return {
        "statement": statement,
        "premise_ids": ["a", "b"],
        "relationship_references": [{"source_premise_id": "a", "target_premise_id": "b",
                                     "kind": "complements"}],
    }


class Provider:
    def __init__(self, data, *, failure=None):
        self.data = data
        self.failure = failure
        self.calls = 0

    def generate(self, *, premises, relationships):
        self.calls += 1
        if self.failure:
            raise self.failure
        return SemanticGenerationResponse(
            content=json.dumps(self.data),
            provider_metadata={"evidence_ids": "forged", "private": "PRIVATE_MODEL_PAYLOAD"},
        )


def synthesizer(provider):
    return PropositionSynthesizer(
        structural_only_compatibility=True,
        semantic_generator=ProviderSemanticPropositionGenerator(provider=provider)
    )


# Each attack deliberately retains valid references. A reference check cannot
# establish whether any of these statements follows from the trusted text.
SEMANTIC_ATTACKS = [
    pytest.param("The service was compromised by an external attacker.", id="unsupported-fact"),
    pytest.param("Latency always increases under heavy load, with absolute certainty.", id="certainty-inflation"),
    pytest.param("High request volume caused the latency increase.", id="causal-overreach"),
    pytest.param("Latency cannot increase under heavy load.", id="negation-reversal"),
    pytest.param("High volume increased latency by exactly 37.482 milliseconds.", id="fabricated-precision"),
]


@pytest.mark.parametrize("statement", SEMANTIC_ATTACKS)
@pytest.mark.parametrize("supported", [True, False], ids=["complete", "insufficient-evidence"])
def test_semantic_attacks_remain_unverified_and_cannot_change_inference(monkeypatch, statement, supported):
    premises, relationships = trusted_inputs()
    data = candidate(statement)
    data["generator_metadata"] = {"semantic_grounding_verified": True, "confidence": 1.0,
                                  "evidence_ids": ["forged"], "private": "PRIVATE_MODEL_PAYLOAD"}
    provider = Provider(data)
    governed = synthesizer(provider)
    outcome = governed.synthesize_with_validation(premises=premises, relationships=relationships)
    # Explicit known limitation: structural acceptance is not semantic rejection.
    assert outcome.validation.structurally_valid
    assert outcome.validation.semantic_grounding_verified is False
    assert outcome.propositions[0].statement == statement
    assert outcome.propositions[0].evidence_ids == ["doc-a:0", "doc-b:0"]
    assert outcome.propositions[0].metadata["semantic_grounding_verified"] is False

    bundle = EvidenceBundle(
        question="What was observed?",
        supporting=[EvidenceItem(statement=premises[0].statement, disposition="supporting",
                                 source=EvidenceSource(document_id="doc-a", chunk_index=0,
                                                       text=premises[0].statement), relevance_score=0.8)]
        if supported else [], source_count=int(supported), document_count=int(supported),
    )
    baseline = ReasoningEngine()
    injected = ReasoningEngine(proposition_synthesizer=governed)
    for engine in (baseline, injected):
        monkeypatch.setattr(engine.evidence, "analyze", lambda **kwargs: bundle)
        monkeypatch.setattr(engine.premises, "extract", lambda evidence: premises)
        monkeypatch.setattr(engine.relationships, "assess", lambda **kwargs: relationships[0])
    reference = baseline.reason(question=bundle.question, chunks=[])
    result = injected.reason(question=bundle.question, chunks=[])
    assert result.status == reference.status
    assert result.inferences == reference.inferences
    assert result.conclusion == reference.conclusion
    assert result.metadata["proposition_synthesis"]["semantic_grounding_verified"] is False
    assert "PRIVATE_MODEL_PAYLOAD" not in result.model_dump_json()
    assert "forged" not in result.model_dump_json()
    assert statement not in json.dumps([i.model_dump() for i in result.inferences])


@pytest.mark.parametrize("attack,reason", [
    ("premise", "unknown_premise_reference"),
    ("reversed", "unknown_or_reversed_relationship"),
    ("missing", "missing_relationship_reference"),
    ("kind", "relationship_kind_mismatch"),
    ("suppressed_conflict", "suppressed_conflict"),
    ("invented_provenance", "malformed_generation"),
    ("blank", "blank_candidate_statement"),
])
def test_structural_attacks_fail_closed(attack, reason):
    premises, relationships = trusted_inputs()
    data = candidate()
    if attack == "premise":
        data["premise_ids"] = ["a", "unknown"]
    elif attack == "reversed":
        data["relationship_references"][0].update(source_premise_id="b", target_premise_id="a")
    elif attack == "missing":
        data["relationship_references"] = []
    elif attack == "kind":
        data["relationship_references"][0]["kind"] = "supports"
    elif attack == "suppressed_conflict":
        relationships.append(PremiseRelationship(source_premise_id="b", target_premise_id="a",
                                                kind="conflicts", basis="Trusted conflict.", confidence=0.8))
    elif attack == "invented_provenance":
        data["evidence_ids"] = ["forged"]
    elif attack == "blank":
        data["statement"] = "   "
    outcome = synthesizer(Provider(data)).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert reason in outcome.rejection_reasons
    if outcome.validation is not None:
        assert not outcome.validation.structurally_valid
        assert outcome.validation.evidence_ids == ()
        assert not outcome.validation.semantic_grounding_verified


def test_conflict_references_do_not_certify_a_statement_that_suppresses_conflict():
    premises, relationships = trusted_inputs()
    premises[0].statement = "The service is healthy."
    premises[1].statement = "The service is not healthy."
    relationships = [PremiseRelationship(
        source_premise_id="a", target_premise_id="b", kind="conflicts",
        basis="Contradictory health reports.", confidence=0.9,
    )]
    data = candidate("Both sources agree without any contradiction.")
    data["relationship_references"][0]["kind"] = "conflicts"
    outcome = synthesizer(Provider(data)).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.validation.structurally_valid
    assert outcome.propositions[0].metadata == {"relationship_kinds": ["conflicts"],
                                              "semantic_grounding_verified": False}


@pytest.mark.parametrize("reason", ["unavailable", "refused", "malformed_response"])
def test_provider_failure_yields_no_fallback_and_no_claimed_grounding(reason):
    premises, relationships = trusted_inputs()
    provider = Provider(candidate(), failure=SemanticGenerationFailure(reason))
    outcome = synthesizer(provider).synthesize_with_validation(premises=premises, relationships=relationships)
    assert provider.calls == 1
    assert outcome.propositions == []
    assert outcome.validation is None
    assert outcome.rejection_reasons == (f"provider_{reason}",)


def test_faithful_control_reconstructs_provenance_without_claiming_entailment():
    premises, relationships = trusted_inputs()
    outcome = synthesizer(Provider(candidate())).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.validation.structurally_valid
    assert outcome.rejection_reasons == ()
    assert outcome.propositions[0].evidence_ids == ["doc-a:0", "doc-b:0"]
    assert outcome.propositions[0].metadata["semantic_grounding_verified"] is False
