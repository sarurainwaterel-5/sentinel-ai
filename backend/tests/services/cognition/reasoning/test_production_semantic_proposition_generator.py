"""Production parser and governance checks without a model or credentials."""

import json

import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship
from app.services.cognition.reasoning.proposition_synthesizer import PropositionSynthesizer
from app.services.cognition.reasoning.semantic_generation_provider import (
    SemanticGenerationFailure,
    SemanticGenerationResponse,
)
from app.services.cognition.reasoning.semantic_proposition_generator import (
    ProviderSemanticPropositionGenerator,
    SemanticPropositionGenerator,
)


def inputs():
    return (
        [Premise(premise_id="a", statement="A.", evidence_ids=["e-a"]),
         Premise(premise_id="b", statement="B.", evidence_ids=["e-b"])],
        [PremiseRelationship(source_premise_id="a", target_premise_id="b",
                             kind="supports", basis="Trusted.", confidence=0.7)],
    )


def payload(**changes):
    data = {
        "statement": "A and B are proposed together.",
        "premise_ids": ["a", "b"],
        "relationship_references": [{"source_premise_id": "a",
                                     "target_premise_id": "b", "kind": "supports"}],
        "qualifications": ["Subject to the supplied evidence."],
        "generator_metadata": {"note": "untrusted"},
    }
    data.update(changes)
    return json.dumps(data)


class Provider:
    def __init__(self, content=None, *, failure=None, response=None):
        self.response = response if response is not None else SemanticGenerationResponse(
            content=content or payload(), provider_metadata={"model": "test"}
        )
        self.failure = failure
        self.calls = []

    def generate(self, *, premises, relationships):
        self.calls.append((premises, relationships))
        if self.failure:
            raise self.failure
        return self.response


def outcome(provider):
    premises, relationships = inputs()
    return PropositionSynthesizer(
        structural_only_compatibility=True,
        semantic_generator=ProviderSemanticPropositionGenerator(provider=provider)
    ).synthesize_with_validation(premises=premises, relationships=relationships)


def test_production_generator_parses_candidate_and_retains_untrusted_metadata():
    provider = Provider()
    generator: SemanticPropositionGenerator = ProviderSemanticPropositionGenerator(provider=provider)
    premises, relationships = inputs()
    candidate = generator.generate(premises=premises, relationships=relationships)
    assert isinstance(candidate, CandidateProposition)
    assert candidate.premise_ids == ["a", "b"]
    assert candidate.relationship_references[0].kind.value == "supports"
    assert candidate.qualifications == ["Subject to the supplied evidence."]
    assert candidate.generator_metadata == {"note": "untrusted", "provider_metadata": {"model": "test"}}
    assert provider.calls == [(premises, relationships)]
    provider.response.provider_metadata["model"] = "changed"
    assert candidate.generator_metadata["provider_metadata"]["model"] == "test"


@pytest.mark.parametrize("content", [
    "not JSON", "```json\n{}\n```", "null", "[]", "{}",
    payload(statement=""), payload(statement=42), payload(premise_ids=["a"]),
    payload(premise_ids=[1, 2]), payload(evidence_ids=["forged"]),
    payload(relationship_ids=["invented"]),
    payload(relationship_references=[{"source_premise_id": "a", "target_premise_id": "b", "kind": "invented"}]),
])
def test_malformed_generation_is_rejected_without_repair_or_fallback(content):
    provider = Provider(content)
    premises, relationships = inputs()
    with pytest.raises(ValidationError):
        ProviderSemanticPropositionGenerator(provider=provider).generate(
            premises=premises, relationships=relationships
        )
    result = outcome(provider)
    assert result.propositions == []
    assert result.rejection_reasons == ("malformed_generation",)


@pytest.mark.parametrize("reason", ["unavailable", "refused", "malformed_response"])
def test_provider_failures_propagate_and_remain_distinct(reason):
    failure = SemanticGenerationFailure(reason)
    provider = Provider(failure=failure)
    premises, relationships = inputs()
    with pytest.raises(SemanticGenerationFailure) as raised:
        ProviderSemanticPropositionGenerator(provider=provider).generate(
            premises=premises, relationships=relationships
        )
    assert raised.value is failure
    result = outcome(provider)
    assert result.propositions == []
    assert result.rejection_reasons == (f"provider_{reason}",)


@pytest.mark.parametrize("response", ["raw JSON", {"content": payload()}])
def test_invalid_provider_response_contract_fails_closed(response):
    result = outcome(Provider(response=response))
    assert result.propositions == []
    assert result.rejection_reasons == ("provider_malformed_response",)


def test_valid_candidate_cannot_launder_provider_or_generator_provenance():
    provider = Provider(payload(generator_metadata={"semantic_grounding_verified": True,
                                                   "evidence_ids": ["forged"]}))
    provider.response.provider_metadata.update({"evidence_ids": "forged", "confidence": "1.0"})
    result = outcome(provider)
    assert result.validation.structurally_valid
    proposition = result.propositions[0]
    assert proposition.evidence_ids == ["e-a", "e-b"]
    assert proposition.metadata == {"semantic_grounding_verified": False, "relationship_kinds": ["supports"]}
    assert "forged" not in proposition.model_dump_json()


def test_parsing_does_not_validate_unknown_references():
    provider = Provider(payload(premise_ids=["a", "missing"]))
    premises, relationships = inputs()
    candidate = ProviderSemanticPropositionGenerator(provider=provider).generate(
        premises=premises, relationships=relationships
    )
    assert candidate.premise_ids == ["a", "missing"]
    result = outcome(provider)
    assert result.propositions == []
    assert "unknown_premise_reference" in result.rejection_reasons


def test_provider_mutation_cannot_replace_trusted_lineage():
    class MutatingProvider(Provider):
        def generate(self, *, premises, relationships):
            premises[0].evidence_ids[:] = ["forged"]
            premises[0].metadata["injected"] = True
            relationships[0].basis = "forged"
            return super().generate(premises=premises, relationships=relationships)

    premises, relationships = inputs()
    result = PropositionSynthesizer(
        structural_only_compatibility=True,
        semantic_generator=ProviderSemanticPropositionGenerator(provider=MutatingProvider())
    ).synthesize_with_validation(premises=premises, relationships=relationships)
    assert result.propositions[0].evidence_ids == ["e-a", "e-b"]
    assert premises[0].metadata == {}
    assert relationships[0].basis == "Trusted."


def test_arbitrary_unsupported_statement_is_never_certified_by_parsing():
    result = outcome(Provider(payload(statement="An unsupported fact with fabricated precision: 99.99%.")))
    assert result.validation.structurally_valid
    assert result.validation.semantic_grounding_verified is False
    assert result.propositions[0].metadata["semantic_grounding_verified"] is False
