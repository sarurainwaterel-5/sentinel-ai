"""Governed synthesis stays observable and separate from evidence inference."""

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


class Provider:
    def __init__(self, mode):
        self.mode = mode
        self.calls = 0

    def generate(self, *, premises, relationships):
        self.calls += 1
        if self.mode in {"unavailable", "refused", "malformed_response"}:
            raise SemanticGenerationFailure(self.mode)
        if self.mode == "exception":
            raise RuntimeError("PRIVATE_PROVIDER_PAYLOAD")
        if self.mode == "malformed":
            return SemanticGenerationResponse(content="PRIVATE_PROVIDER_PAYLOAD")
        data = {
            "statement": "The two premises are proposed together.",
            "premise_ids": [p.premise_id for p in premises],
            "relationship_references": [{
                "source_premise_id": r.source_premise_id,
                "target_premise_id": r.target_premise_id,
                "kind": r.kind.value,
            } for r in relationships],
            "generator_metadata": {"private": "PRIVATE_PROVIDER_PAYLOAD"},
        }
        if self.mode == "unknown_reference":
            data["premise_ids"] = ["a", "unknown"]
        return SemanticGenerationResponse(
            content=json.dumps(data), provider_metadata={"private": "PRIVATE_PROVIDER_PAYLOAD"}
        )


def configured_engine(monkeypatch, *, supported, synthesizer=None):
    bundle = EvidenceBundle(
        question="What is supported?",
        supporting=[EvidenceItem(
            statement="Evidence provenance is preserved.", disposition="supporting",
            source=EvidenceSource(document_id="document-a", chunk_index=0,
                                  text="Evidence provenance is preserved."),
            relevance_score=0.9,
        )] if supported else [],
        source_count=1 if supported else 0,
        document_count=1 if supported else 0,
    )
    premises = [Premise(premise_id="a", statement="A.", evidence_ids=["e-a"]),
                Premise(premise_id="b", statement="B.", evidence_ids=["e-b"])]
    relationship = PremiseRelationship(
        source_premise_id="a", target_premise_id="b", kind="supports",
        basis="Trusted.", confidence=0.7,
    )
    engine = ReasoningEngine(proposition_synthesizer=synthesizer)
    monkeypatch.setattr(engine.evidence, "analyze", lambda **kwargs: bundle)
    monkeypatch.setattr(engine.premises, "extract", lambda evidence: premises)
    monkeypatch.setattr(engine.relationships, "assess", lambda **kwargs: relationship)
    return engine


@pytest.mark.parametrize("supported", [True, False])
@pytest.mark.parametrize("mode,reason", [
    ("accepted", None), ("unavailable", "provider_unavailable"),
    ("refused", "provider_refused"), ("malformed_response", "provider_malformed_response"),
    ("malformed", "malformed_generation"), ("exception", "generator_failure"),
    ("unknown_reference", "unknown_premise_reference"),
])
def test_injected_governance_preserves_inference_and_reports_safe_outcomes(
    monkeypatch, supported, mode, reason
):
    provider = Provider(mode)
    synthesizer = PropositionSynthesizer(
        semantic_generator=ProviderSemanticPropositionGenerator(provider=provider)
    )
    baseline = configured_engine(monkeypatch, supported=supported).reason(
        question="What is supported?", chunks=[]
    )
    engine = configured_engine(monkeypatch, supported=supported, synthesizer=synthesizer)
    assert engine.propositions is synthesizer
    result = engine.reason(question="What is supported?", chunks=[])
    assert provider.calls == 1
    assert result.inferences == baseline.inferences
    assert result.conclusion == baseline.conclusion
    assert result.status == baseline.status
    assert result.status == ("complete" if supported else "insufficient_evidence")
    assert "PRIVATE_PROVIDER_PAYLOAD" not in result.model_dump_json()
    summary = result.metadata["proposition_synthesis"]
    assert summary["semantic_grounding_verified"] is False
    if reason is None:
        assert summary["status"] == "accepted"
        assert summary["rejection_reasons"] == []
        assert result.synthesized_propositions[0].evidence_ids == ["e-a", "e-b"]
        assert result.synthesized_propositions[0].metadata["semantic_grounding_verified"] is False
        assert any("semantic grounding remains unverified" in stage for stage in result.reasoning_trace)
    else:
        assert summary["status"] == "rejected"
        assert reason in summary["rejection_reasons"]
        assert result.synthesized_propositions == []
        assert "Proposition synthesis produced no admissible candidate." in result.reasoning_trace


def test_default_engine_requires_no_provider_or_credentials(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    engine = configured_engine(monkeypatch, supported=True)
    assert engine.propositions is None
    result = engine.reason(question="What is supported?", chunks=[])
    assert result.metadata == {}
    assert result.synthesized_propositions == []
    assert not any("synthesi" in stage.casefold() for stage in result.reasoning_trace)
