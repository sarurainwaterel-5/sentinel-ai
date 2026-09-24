"""Contract tests for the provider boundary; no model or SDK is used."""

import pytest
from pydantic import ValidationError

from app.services.cognition.reasoning.models import (
    CandidateProposition,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)
from app.services.cognition.reasoning.proposition_synthesizer import (
    PropositionSynthesizer,
)
from app.services.cognition.reasoning.semantic_generation_provider import (
    SemanticGenerationFailure,
    SemanticGenerationProvider,
    SemanticGenerationResponse,
)


def trusted_inputs():
    return (
        [
            Premise(premise_id="a", statement="A.", evidence_ids=["e-a"]),
            Premise(premise_id="b", statement="B.", evidence_ids=["e-b"]),
        ],
        [PremiseRelationship(
            source_premise_id="a", target_premise_id="b",
            kind=PremiseRelationshipKind.SUPPORTS,
            basis="Trusted assessment.", confidence=0.7,
        )],
    )


VALID_CANDIDATE = (
    '{"statement":"A and B are proposed together.",'
    '"premise_ids":["a","b"],'
    '"relationship_references":[{"source_premise_id":"a",'
    '"target_premise_id":"b","kind":"supports"}]}'
)


class FakeProvider:
    def __init__(self, response=None, failure=None):
        self.response = response
        self.failure = failure
        self.calls = []

    def generate(self, *, premises, relationships):
        self.calls.append((premises, relationships))
        if self.failure:
            raise self.failure
        return self.response


class FutureGeneratorStub:
    """Test-only sketch of the future parser; not a production generator."""

    def __init__(self, provider: SemanticGenerationProvider):
        self.provider = provider

    def generate(self, *, premises, relationships):
        response = self.provider.generate(
            premises=premises, relationships=relationships
        )
        candidate = CandidateProposition.model_validate_json(response.content)
        return candidate.model_copy(update={
            "generator_metadata": response.provider_metadata,
        })


def test_provider_protocol_uses_only_sentinel_inputs_and_plain_output():
    premises, relationships = trusted_inputs()
    provider: SemanticGenerationProvider = FakeProvider(
        SemanticGenerationResponse(content=VALID_CANDIDATE)
    )
    response = provider.generate(premises=premises, relationships=relationships)
    assert isinstance(response, SemanticGenerationResponse)
    assert response.content == VALID_CANDIDATE
    assert provider.calls == [(premises, relationships)]
    assert response.provider_metadata == {}


def test_provider_output_remains_untrusted_through_future_generator_boundary():
    premises, relationships = trusted_inputs()
    provider = FakeProvider(SemanticGenerationResponse(
        content=VALID_CANDIDATE,
        provider_metadata={"evidence_ids": "forged", "confidence": "1.0"},
    ))
    candidate = FutureGeneratorStub(provider).generate(
        premises=premises, relationships=relationships
    )
    assert isinstance(candidate, CandidateProposition)
    assert candidate.generator_metadata["evidence_ids"] == "forged"

    outcome = PropositionSynthesizer(
        semantic_generator=FutureGeneratorStub(provider)
    ).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.validation.structurally_valid
    proposition = outcome.propositions[0]
    assert proposition.evidence_ids == ["e-a", "e-b"]
    assert proposition.metadata["semantic_grounding_verified"] is False
    assert "forged" not in str(proposition.model_dump())


@pytest.mark.parametrize("reason", ["unavailable", "refused", "malformed_response"])
def test_provider_failure_has_bounded_reason_and_no_fallback(reason):
    premises, relationships = trusted_inputs()
    failure = SemanticGenerationFailure(reason)
    provider = FakeProvider(failure=failure)
    with pytest.raises(SemanticGenerationFailure) as raised:
        provider.generate(premises=premises, relationships=relationships)
    assert raised.value.reason == reason

    outcome = PropositionSynthesizer(
        semantic_generator=FutureGeneratorStub(provider)
    ).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == (f"provider_{reason}",)


@pytest.mark.parametrize("content", ["not JSON", '{"statement":"claim"}'])
def test_malformed_provider_output_cannot_be_promoted(content):
    premises, relationships = trusted_inputs()
    provider = FakeProvider(SemanticGenerationResponse(content=content))
    outcome = PropositionSynthesizer(
        semantic_generator=FutureGeneratorStub(provider)
    ).synthesize_with_validation(premises=premises, relationships=relationships)
    assert outcome.propositions == []
    assert outcome.rejection_reasons == ("malformed_generation",)


def test_empty_provider_response_is_invalid_without_fallback():
    with pytest.raises(ValidationError):
        SemanticGenerationResponse(content="")


def test_provider_cannot_inject_arbitrary_failure_text_into_reason():
    with pytest.raises(ValueError, match="Unknown semantic generation"):
        SemanticGenerationFailure("secret provider payload")
