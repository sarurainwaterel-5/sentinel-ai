from app.services.cognition.reasoning.models import (
    ConfidenceAssessment,
    ConfidenceLevel,
    EvidenceBundle,
    EvidenceGap,
    Inference,
)
from app.services.cognition.reasoning.reasoning_engine import (
    ReasoningEngine,
)


def test_missing_information_is_semantically_distinct_from_limitations(
    monkeypatch,
):
    """
    Limitations constrain the current conclusion.

    Missing information identifies evidence that would
    materially improve the judgment.

    Confidence uncertainty must remain an independent
    epistemic concept.
    """

    engine = ReasoningEngine()

    evidence_bundle = EvidenceBundle(
        question="What does the evidence support?",
        gaps=[
            EvidenceGap(
                description=(
                    "Independent corroborating evidence "
                    "is not currently available."
                ),
                impact=(
                    "The conclusion cannot yet be "
                    "independently corroborated."
                ),
                recommended_source=(
                    "An independent primary or "
                    "authoritative secondary source."
                ),
            ),
        ],
        source_count=1,
        document_count=1,
        domain_count=1,
    )

    inference = Inference(
        statement="The available evidence supports the claim.",
        supporting_evidence_ids=["document-1:0"],
        limitations=[
            (
                "The candidate inference is supported "
                "by only one retrieved evidence item."
            ),
            (
                "The available support comes from one "
                "document and has not been independently "
                "corroborated."
            ),
        ],
    )

    confidence = ConfidenceAssessment(
        score=0.45,
        level=ConfidenceLevel.LOW,
        basis=(
            "Confidence is limited by evidence volume "
            "and source independence."
        ),
        factors=[],
        uncertainty=[
            (
                "The conclusion is supported by only "
                "one retrieved evidence item."
            ),
        ],
    )

    monkeypatch.setattr(
        engine.evidence,
        "analyze",
        lambda **kwargs: evidence_bundle,
    )

    monkeypatch.setattr(
        engine.inference,
        "infer",
        lambda bundle: [inference],
    )

    monkeypatch.setattr(
        engine.confidence,
        "assess",
        lambda **kwargs: confidence,
    )

    result = engine.reason(
        question="What does the evidence support?",
        chunks=[],
    )

    conclusion = result.conclusion

    assert conclusion is not None

    assert conclusion.limitations == inference.limitations

    assert conclusion.missing_information == [
        (
            "Independent corroborating evidence "
            "is not currently available."
        )
    ]

    assert (
        conclusion.missing_information
        != conclusion.limitations
    )

    assert (
        conclusion.missing_information
        != conclusion.confidence.uncertainty
    )
from types import SimpleNamespace

from app.schemas.cognition.reasoning import (
    ReasoningRequest,
)

from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    EvidenceGap,
    ReasoningResult,
)

from app.services.cognition.reasoning.reasoning_orchestrator import (
    ReasoningOrchestrator,
)


def test_insufficient_evidence_keeps_limitations_distinct_from_missing_information(
    monkeypatch,
):
    """
    When no conclusion can be formed:

    - limitations describe the present reasoning boundary;
    - missing information preserves the actual evidence gaps;
    - confidence uncertainty may also reference those gaps.
    """

    orchestrator = ReasoningOrchestrator()

    evidence_bundle = EvidenceBundle(
        question="What does the evidence support?",
        gaps=[
            EvidenceGap(
                description=(
                    "Independent corroborating evidence "
                    "is not currently available."
                ),
                impact=(
                    "The claim cannot be independently "
                    "corroborated."
                ),
                recommended_source=(
                    "An independent authoritative source."
                ),
            ),
        ],
        source_count=0,
        document_count=0,
        domain_count=0,
    )

    reasoning_result = ReasoningResult(
        question="What does the evidence support?",
        evidence=evidence_bundle,
        inferences=[],
        conclusion=None,
        reasoning_trace=[
            "Retrieved relevant evidence.",
            "Organized evidence.",
            "No supported inference could be produced.",
        ],
        status="insufficient_evidence",
    )

    monkeypatch.setattr(
        orchestrator.identity_service,
        "build_constitution_context",
        lambda **kwargs: {
            "constitutional_context": "Test constitution.",
            "sources": [],
        },
    )

    monkeypatch.setattr(
        orchestrator.retrieval_service,
        "search",
        lambda **kwargs: [],
    )

    monkeypatch.setattr(
        orchestrator.reasoning_engine,
        "reason",
        lambda **kwargs: reasoning_result,
    )

    monkeypatch.setattr(
        orchestrator.formatter,
        "format",
        lambda **kwargs: SimpleNamespace(
            answer="Insufficient evidence.",
            evidence_explanation="No supported evidence.",
            confidence_explanation="Confidence is low.",
            limitations_explanation=(
                "The available evidence is insufficient "
                "to support a conclusion."
            ),
            next_step_explanation=(
                "Collect additional evidence."
            ),
            recommended_next_step=(
                "Collect additional evidence."
            ),
        ),
    )

    monkeypatch.setattr(
        orchestrator.coherence_engine,
        "evaluate",
        lambda **kwargs: SimpleNamespace(
            model_dump=lambda: {
                "coherent": True,
                "constitutional_score": 1.0,
                "articles_consulted": [],
                "conflicts": [],
                "recommendations": [],
            }
        ),
    )

    request = ReasoningRequest(
        question="What does the evidence support?",
    )

    response = orchestrator.reason(request)

    assert response.reasoning.status == "insufficient_evidence"
    assert response.reasoning.conclusion is None

    assert response.reasoning.limitations == [
        (
            "The available evidence was insufficient "
            "to support a conclusion."
        )
    ]

    assert response.reasoning.missing_information == [
        (
            "Independent corroborating evidence "
            "is not currently available."
        )
    ]

    assert (
        response.reasoning.limitations
        != response.reasoning.missing_information
    )
