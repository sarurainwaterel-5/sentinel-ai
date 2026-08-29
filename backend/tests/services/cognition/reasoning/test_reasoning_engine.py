from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
    SynthesizedProposition,
)

from app.services.cognition.reasoning.reasoning_engine import (
    ReasoningEngine,
)


class FakeEvidenceAnalyzer:
    def __init__(self, bundle):
        self.bundle = bundle
        self.calls = []

    def analyze(
        self,
        *,
        question,
        chunks,
        metadata,
    ):
        self.calls.append(
            {
                "question": question,
                "chunks": chunks,
                "metadata": metadata,
            }
        )

        return self.bundle


class FakePremiseExtractor:
    def __init__(self, premises):
        self.premises = premises
        self.calls = []

    def extract(self, evidence):
        self.calls.append(evidence)
        return self.premises


class FakeRelationshipAssessor:
    def __init__(self, relationship):
        self.relationship = relationship
        self.calls = []

    def assess(
        self,
        *,
        source,
        target,
    ):
        self.calls.append(
            {
                "source": source,
                "target": target,
            }
        )

        return self.relationship


class FakePropositionSynthesizer:
    def __init__(self, propositions):
        self.propositions = propositions
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

        return self.propositions


class FakeInferenceEngine:
    def __init__(self):
        self.calls = []

    def infer(self, evidence):
        self.calls.append(evidence)
        return []


class FakeConfidenceEngine:
    def assess(self, **kwargs):
        raise AssertionError(
            "Confidence should not run when no inference exists."
        )


def test_reasoning_engine_exposes_premise_reasoning_pipeline():
    premise_one = Premise(
        premise_id="premise-1",
        statement="Evidence provenance is preserved.",
        evidence_ids=["evidence-1"],
        domain_ids=["reasoning"],
    )

    premise_two = Premise(
        premise_id="premise-2",
        statement="Reasoning outputs remain traceable.",
        evidence_ids=["evidence-2"],
        domain_ids=["reasoning"],
    )

    relationship = PremiseRelationship(
        source_premise_id="premise-1",
        target_premise_id="premise-2",
        kind=PremiseRelationshipKind.SUPPORTS,
        basis="The first premise materially supports the second.",
        confidence=0.90,
    )

    proposition = SynthesizedProposition(
        proposition_id="proposition-1",
        statement=(
            "Preserving evidence provenance enables "
            "traceable reasoning outputs."
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

    evidence_bundle = EvidenceBundle(
    question="Does preserved evidence provenance enable traceable reasoning outputs?",
    supporting=[],
    conflicting=[],
    contextual=[],
    unknown=[],
    gaps=[],
    source_count=0,
    document_count=0,
    domain_count=0,
)

    engine = ReasoningEngine()

    engine.evidence = FakeEvidenceAnalyzer(
        evidence_bundle
    )

    engine.premises = FakePremiseExtractor(
        [
            premise_one,
            premise_two,
        ]
    )

    engine.relationships = FakeRelationshipAssessor(
        relationship
    )

    engine.propositions = FakePropositionSynthesizer(
        [
            proposition,
        ]
    )

    engine.inference = FakeInferenceEngine()
    engine.confidence = FakeConfidenceEngine()

    result = engine.reason(
        question="Can reasoning remain traceable?",
        chunks=[],
        metadata={
            "module": "reasoning",
        },
    )

    assert result.premises == [
        premise_one,
        premise_two,
    ]

    assert result.premise_relationships == [
        relationship,
    ]

    assert result.synthesized_propositions == [
        proposition,
    ]

    assert len(
        engine.premises.calls
    ) == 1

    assert len(
        engine.relationships.calls
    ) == 1

    assert len(
        engine.propositions.calls
    ) == 1

    assert engine.propositions.calls[0][
        "premises"
    ] == [
        premise_one,
        premise_two,
    ]

    assert engine.propositions.calls[0][
        "relationships"
    ] == [
        relationship,
    ]
