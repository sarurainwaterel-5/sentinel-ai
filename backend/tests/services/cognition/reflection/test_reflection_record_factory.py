"""
Contract 027 — ReflectionRecord Factory.

The ReflectionRecord Factory transforms one completed governed
Reflection into one historical ReflectionRecord.

It may preserve:

- Reflection identity,
- mission/session/organization context,
- Reflection timestamp,
- Learning Event provenance,
- Pattern/Insight/Recommendation provenance,
- Reflection status,
- Reflection confidence,
- constitutional judgment,
- longitudinal Understanding provenance,
- reflective trends.

It may not:

- perform Reflection,
- recalculate confidence,
- reinterpret constitutional coherence,
- alter admissibility,
- persist records,
- execute Recommendations.

Historical recording preserves cognition.

It does not create new cognition.
"""

from datetime import UTC, datetime

from app.services.cognition.reflection.models import (
    ReflectionConfidence,
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionPatternKind,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
    ReflectionResult,
    ReflectionStatus,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceResult,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)

from app.services.cognition.reflection.reflection_record_factory import (
    ReflectionRecordFactory,
)


def make_governed_reflection(
    *,
    admissible: bool = True,
    coherent: bool = True,
    constitutional_score: float = 1.0,
    confidence_score: float = 0.86,
) -> GovernedReflectionResult:
    pattern = ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring engineering learning",
        description=(
            "Engineering recurs across accumulated learning."
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
    )

    insight = ReflectionInsight(
        insight_id="insight-1",
        title="Engineering remains recurrent",
        explanation=(
            "Engineering represents a repeated area "
            "within the examined learning history."
        ),
        pattern_ids=[
            "pattern-1",
        ],
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
        confidence=confidence_score,
    )

    recommendation = ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue engineering learning",
        description=(
            "Continue examining the established learning area."
        ),
        insight_ids=[
            "insight-1",
        ],
        pattern_ids=[
            "pattern-1",
        ],
        domain_ids=[
            "engineering",
        ],
        priority=1,
        requires_human_approval=True,
    )

    reflection = ReflectionResult(
        title="Engineering reflection",
        summary="Reflection completed.",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        patterns=[
            pattern,
        ],
        insights=[
            insight,
        ],
        recommendations=[
            recommendation,
        ],
        confidence=ReflectionConfidence(
            score=confidence_score,
            level=ReflectionConfidenceLevel.HIGH,
            basis="Reflective support was assessed.",
            factors=[],
            uncertainty=[],
        ),
        reflection_trace=[
            "History analyzed.",
            "Patterns discovered.",
            "Insights generated.",
            "Recommendations generated.",
        ],
        status=ReflectionStatus.COMPLETE,
    )

    coherence = ReflectionCoherenceResult(
        coherent=coherent,
        admissible=admissible,
        constitutional_score=constitutional_score,
        reflection_confidence=confidence_score,
        articles_consulted=[],
        conflicts=[],
        recommendations=[],
    )

    return GovernedReflectionResult(
        reflection=reflection,
        coherence=coherence,
        admissible=admissible,
    )


def test_factory_creates_reflection_record():
    factory = ReflectionRecordFactory()

    governed = make_governed_reflection()

    record = factory.create(
        reflection_id="reflection-001",
        governed=governed,
        reflected_at=datetime(
            2026,
            8,
            18,
            16,
            30,
            tzinfo=UTC,
        ),
        mission_id="mission-001",
        session_id="sprint-18",
        organization_id="default",
    )

    assert record.reflection_id == (
        "reflection-001"
    )


def test_factory_preserves_learning_event_provenance():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=datetime.now(UTC),
    )

    assert record.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_factory_preserves_derived_cognitive_provenance():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=datetime.now(UTC),
    )

    assert record.pattern_ids == [
        "pattern-1",
    ]

    assert record.insight_ids == [
        "insight-1",
    ]

    assert record.recommendation_ids == [
        "recommendation-1",
    ]


def test_factory_preserves_reflection_status():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=datetime.now(UTC),
    )

    assert record.status == "complete"


def test_factory_preserves_reflection_confidence():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(
            confidence_score=0.86,
        ),
        reflected_at=datetime.now(UTC),
    )

    assert (
        record.reflection_confidence_score
        == 0.86
    )

    assert (
        record.reflection_confidence_level
        == "high"
    )


def test_factory_preserves_constitutional_judgment():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(
            admissible=False,
            coherent=False,
            constitutional_score=0.40,
        ),
        reflected_at=datetime.now(UTC),
    )

    assert record.coherent is False
    assert record.admissible is False

    assert (
        record.constitutional_score
        == 0.40
    )


def test_factory_preserves_mission_context():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=datetime.now(UTC),
        mission_id="mission-001",
        session_id="sprint-18",
        organization_id="default",
    )

    assert record.mission_id == "mission-001"
    assert record.session_id == "sprint-18"
    assert record.organization_id == "default"


def test_factory_preserves_timestamp_exactly():
    factory = ReflectionRecordFactory()

    timestamp = datetime(
        2026,
        8,
        18,
        16,
        30,
        15,
        123456,
        tzinfo=UTC,
    )

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=timestamp,
    )

    assert record.reflected_at == timestamp


def test_factory_accepts_longitudinal_provenance():
    factory = ReflectionRecordFactory()

    record = factory.create(
        reflection_id="reflection-001",
        governed=make_governed_reflection(),
        reflected_at=datetime.now(UTC),
        longitudinal_understanding_ids=[
            "understanding-v1",
            "understanding-v2",
        ],
        reflective_trends=[
            "revision",
            "reinforcement",
        ],
    )

    assert (
        record.longitudinal_understanding_ids
        == [
            "understanding-v1",
            "understanding-v2",
        ]
    )

    assert record.reflective_trends == [
        "revision",
        "reinforcement",
    ]


def test_factory_does_not_modify_governed_reflection():
    factory = ReflectionRecordFactory()

    governed = make_governed_reflection()

    before = governed.model_dump()

    factory.create(
        reflection_id="reflection-001",
        governed=governed,
        reflected_at=datetime.now(UTC),
    )

    assert governed.model_dump() == before


def test_factory_has_no_persistence_authority():
    factory = ReflectionRecordFactory()

    assert not hasattr(
        factory,
        "save",
    )

    assert not hasattr(
        factory,
        "persist",
    )


def test_factory_has_no_cognitive_or_execution_authority():
    factory = ReflectionRecordFactory()

    forbidden = [
        "reflect",
        "discover_patterns",
        "generate_insights",
        "generate_recommendations",
        "calculate_confidence",
        "evaluate_coherence",
        "execute",
    ]

    for name in forbidden:
        assert not hasattr(
            factory,
            name,
        )
