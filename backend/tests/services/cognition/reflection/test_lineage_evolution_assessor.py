"""
Contract 020 — Lineage-Grounded Evolution.

This assessor compares declared Understanding lineage against observed
evolution in authoritative Understanding states.

It may determine:

- declared relationship,
- observed evolution,
- whether the declaration is supported,
- where lineage and observed cognition disagree.

It may not:

- rewrite lineage,
- modify Understanding objects,
- perform Reflection,
- generate Recommendations,
- repair historical cognition.

Declared history is inspected.

It is not blindly trusted.
"""

from app.core.cognition.models import Understanding

from app.services.cognition.reflection.lineage_evolution_assessor import (
    LineageEvolutionAssessor,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionAnalyzer,
    UnderstandingEvolutionKind,
)

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineage,
    UnderstandingLineageEdge,
    UnderstandingLineageKind,
)


def make_understanding(
    *,
    understanding_id: str,
    explanation: str,
    evidence_ids: list[str],
    confidence: float | None,
) -> Understanding:
    return Understanding(
        understanding_id=understanding_id,
        title="Comparability doctrine",
        explanation=explanation,
        domain_ids=["cognition"],
        evidence_ids=evidence_ids,
        confidence=confidence,
    )


def make_lineage(
    *,
    earlier: Understanding,
    later: Understanding,
    kind: UnderstandingLineageKind,
) -> UnderstandingLineage:
    return UnderstandingLineage(
        understandings={
            earlier.understanding_id: earlier,
            later.understanding_id: later,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id=(
                    earlier.understanding_id
                ),
                later_understanding_id=(
                    later.understanding_id
                ),
                kind=kind,
            ),
        ],
    )


def test_strengthened_declaration_supported_by_observed_strengthening():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Evidence supports the principle.",
        evidence_ids=["evidence-1"],
        confidence=0.60,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Evidence supports the principle.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.85,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.STRENGTHENED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assert len(result.assessments) == 1

    assessment = result.assessments[0]

    assert (
        assessment.declared_kind
        == UnderstandingLineageKind.STRENGTHENED
    )

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.STRENGTHENED
    )

    assert assessment.supported is True


def test_strengthened_declaration_rejected_when_observed_weakened():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Evidence supports the principle.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.90,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Evidence supports the principle.",
        evidence_ids=["evidence-1"],
        confidence=0.55,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.STRENGTHENED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assessment = result.assessments[0]

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.WEAKENED
    )

    assert assessment.supported is False
    assert assessment.conflict is True


def test_revision_declaration_supported_by_material_change():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation=(
            "All Learning Events must share one universal domain."
        ),
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation=(
            "A comparable domain cohort is sufficient when "
            "the domain recurs across multiple Learning Events."
        ),
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.90,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.REVISED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assessment = result.assessments[0]

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.REVISED
    )

    assert assessment.supported is True


def test_declared_contradiction_requires_observed_contradiction():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-2"],
        confidence=0.80,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.CONTRADICTED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assessment = result.assessments[0]

    assert (
        assessment.observed_kind
        != UnderstandingEvolutionKind.CONTRADICTED
    )

    assert assessment.supported is False


def test_assessor_uses_explicit_contradiction_support_when_declared():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Universal comparability is not required.",
        evidence_ids=["evidence-2"],
        confidence=0.90,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.CONTRADICTED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage,
        contradiction_support={
            "understanding-v2": [
                "understanding-v1",
            ]
        },
    )

    assessment = result.assessments[0]

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.CONTRADICTED
    )

    assert assessment.supported is True


def test_unresolved_observation_cannot_support_strong_declaration():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Stable meaning.",
        evidence_ids=["evidence-1"],
        confidence=None,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Stable meaning.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=None,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.STRENGTHENED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assessment = result.assessments[0]

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.UNRESOLVED
    )

    assert assessment.supported is False


def test_assessor_preserves_lineage_and_understandings():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Stable meaning.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Stable meaning.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.STRENGTHENED,
    )

    earlier_before = earlier.to_dict()
    later_before = later.to_dict()

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    assessor.assess(
        lineage=lineage
    )

    assert earlier.to_dict() == earlier_before
    assert later.to_dict() == later_before

    assert (
        lineage.edges[0].kind
        == UnderstandingLineageKind.STRENGTHENED
    )


def test_assessment_preserves_both_declared_and_observed_states():
    earlier = make_understanding(
        understanding_id="understanding-v1",
        explanation="Stable meaning.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.90,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        explanation="Stable meaning.",
        evidence_ids=["evidence-1"],
        confidence=0.50,
    )

    lineage = make_lineage(
        earlier=earlier,
        later=later,
        kind=UnderstandingLineageKind.STRENGTHENED,
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assessment = result.assessments[0]

    assert (
        assessment.declared_kind
        == UnderstandingLineageKind.STRENGTHENED
    )

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.WEAKENED
    )

    assert assessment.supported is False


def test_empty_lineage_produces_empty_assessment():
    lineage = UnderstandingLineage(
        understandings={},
        edges=[],
    )

    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    result = assessor.assess(
        lineage=lineage
    )

    assert result.assessments == []
    assert result.conflict_count == 0


def test_assessor_has_no_repair_or_execution_authority():
    assessor = LineageEvolutionAssessor(
        evolution_analyzer=UnderstandingEvolutionAnalyzer()
    )

    forbidden = [
        "rewrite_lineage",
        "repair_lineage",
        "rewrite_understanding",
        "reflect",
        "generate_recommendations",
        "execute",
    ]

    for name in forbidden:
        assert not hasattr(
            assessor,
            name,
        )
