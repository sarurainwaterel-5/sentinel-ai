"""
Contract 018 — Understanding Evolution Analysis.

Understanding Evolution Analysis examines authoritative Understanding
states across Learning Events.

It may identify:

- stability,
- strengthening,
- weakening,
- revision,
- contradiction,
- unresolved evolution.

It may not:

- infer change from chronology alone,
- invent missing Understanding records,
- manufacture evidence relationships,
- perform Reflection,
- generate Recommendations,
- modify historical cognition.

Change must be observed before change may be characterized.
"""

from datetime import UTC, datetime

from app.core.cognition.models import (
    LearningEvent,
    Understanding,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionAnalyzer,
    UnderstandingEvolutionKind,
)


def dt(
    year: int,
    month: int,
    day: int,
) -> datetime:
    return datetime(
        year,
        month,
        day,
        tzinfo=UTC,
    )


def make_event(
    *,
    event_id: str,
    learned_at: datetime,
    understanding_ids: list[str],
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=["engineering"],
        understandings_added=understanding_ids,
        learned_at=learned_at,
        summary=f"Learning recorded for {event_id}.",
    )


def make_understanding(
    *,
    understanding_id: str,
    title: str,
    explanation: str,
    evidence_ids: list[str],
    confidence: float | None,
) -> Understanding:
    return Understanding(
        understanding_id=understanding_id,
        title=title,
        explanation=explanation,
        domain_ids=["engineering"],
        evidence_ids=evidence_ids,
        confidence=confidence,
    )


def test_same_understanding_with_same_support_is_stable():
    analyzer = UnderstandingEvolutionAnalyzer()

    understanding = make_understanding(
        understanding_id="understanding-1",
        title="Contract boundaries matter",
        explanation=(
            "Cognitive responsibilities should remain separated."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        confidence=0.80,
    )

    result = analyzer.analyze(
        learning_events=[
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                understanding_ids=[
                    "understanding-1",
                ],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 2, 1),
                understanding_ids=[
                    "understanding-1",
                ],
            ),
        ],
        understandings={
            "understanding-1": understanding,
        },
    )

    assert len(result.evolutions) == 1

    assert (
        result.evolutions[0].kind
        == UnderstandingEvolutionKind.STABLE
    )


def test_same_understanding_with_increased_confidence_is_strengthened():
    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="Evidence-grounded cognition",
        explanation=(
            "Conclusions require visible evidence support."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        confidence=0.60,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="Evidence-grounded cognition",
        explanation=(
            "Conclusions require visible evidence support."
        ),
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.85,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
    )

    assert (
        result.kind
        == UnderstandingEvolutionKind.STRENGTHENED
    )

    assert result.confidence_delta == 0.25

    assert result.evidence_added == [
        "evidence-2",
    ]


def test_same_understanding_with_reduced_confidence_is_weakened():
    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="Traceability principle",
        explanation=(
            "Traceability strongly supports reliable cognition."
        ),
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.90,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="Traceability principle",
        explanation=(
            "Traceability strongly supports reliable cognition."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        confidence=0.55,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
    )

    assert (
        result.kind
        == UnderstandingEvolutionKind.WEAKENED
    )

    assert result.confidence_delta == -0.35

    assert result.evidence_removed == [
        "evidence-2",
    ]


def test_material_explanation_change_is_revised():
    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="Reflection comparability",
        explanation=(
            "All Learning Events must share one domain."
        ),
        evidence_ids=[
            "evidence-1",
        ],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="Reflection comparability",
        explanation=(
            "At least one domain must recur across multiple "
            "Learning Events."
        ),
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=0.90,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
    )

    assert (
        result.kind
        == UnderstandingEvolutionKind.REVISED
    )

    assert (
        result.earlier_understanding_id
        == "understanding-v1"
    )

    assert (
        result.later_understanding_id
        == "understanding-v2"
    )


def test_opposing_explanations_are_not_automatically_called_contradiction():
    """
    String difference alone is not enough to prove contradiction.
    """

    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="System behavior",
        explanation="The system requires universal comparability.",
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="System behavior",
        explanation="The system uses cohort comparability.",
        evidence_ids=["evidence-2"],
        confidence=0.80,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
    )

    assert (
        result.kind
        != UnderstandingEvolutionKind.CONTRADICTED
    )


def test_explicit_contradiction_requires_declared_relationship():
    """
    Contradiction authority requires explicit structured support.
    """

    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="Comparability rule",
        explanation=(
            "Universal domain intersection is required."
        ),
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="Comparability rule",
        explanation=(
            "Universal domain intersection is not required."
        ),
        evidence_ids=["evidence-2"],
        confidence=0.90,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
        contradicted_understanding_ids=[
            "understanding-v1",
        ],
    )

    assert (
        result.kind
        == UnderstandingEvolutionKind.CONTRADICTED
    )


def test_missing_confidence_prevents_strengthening_claim():
    analyzer = UnderstandingEvolutionAnalyzer()

    earlier = make_understanding(
        understanding_id="understanding-v1",
        title="Cognitive principle",
        explanation="A stable principle.",
        evidence_ids=["evidence-1"],
        confidence=None,
    )

    later = make_understanding(
        understanding_id="understanding-v2",
        title="Cognitive principle",
        explanation="A stable principle.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
        ],
        confidence=None,
    )

    result = analyzer.compare(
        earlier=earlier,
        later=later,
    )

    assert (
        result.kind
        == UnderstandingEvolutionKind.UNRESOLVED
    )


def test_chronology_alone_does_not_imply_strengthening():
    analyzer = UnderstandingEvolutionAnalyzer()

    understanding = make_understanding(
        understanding_id="understanding-1",
        title="Stable understanding",
        explanation="Nothing changed.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    result = analyzer.analyze(
        learning_events=[
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                understanding_ids=[
                    "understanding-1",
                ],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 12, 1),
                understanding_ids=[
                    "understanding-1",
                ],
            ),
        ],
        understandings={
            "understanding-1": understanding,
        },
    )

    assert (
        result.evolutions[0].kind
        == UnderstandingEvolutionKind.STABLE
    )


def test_missing_understanding_record_is_exposed():
    analyzer = UnderstandingEvolutionAnalyzer()

    result = analyzer.analyze(
        learning_events=[
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                understanding_ids=[
                    "understanding-missing",
                ],
            ),
        ],
        understandings={},
    )

    assert result.missing_understanding_ids == [
        "understanding-missing",
    ]

    assert result.limitations


def test_analyzer_preserves_authoritative_understandings():
    analyzer = UnderstandingEvolutionAnalyzer()

    understanding = make_understanding(
        understanding_id="understanding-1",
        title="Immutable understanding",
        explanation="Historical cognition remains preserved.",
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    before = understanding.to_dict()

    analyzer.analyze(
        learning_events=[
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                understanding_ids=[
                    "understanding-1",
                ],
            ),
        ],
        understandings={
            "understanding-1": understanding,
        },
    )

    assert understanding.to_dict() == before


def test_analyzer_has_no_reflection_or_execution_authority():
    analyzer = UnderstandingEvolutionAnalyzer()

    forbidden = [
        "reflect",
        "generate_insights",
        "generate_recommendations",
        "execute",
        "rewrite_understanding",
    ]

    for name in forbidden:
        assert not hasattr(
            analyzer,
            name,
        )
