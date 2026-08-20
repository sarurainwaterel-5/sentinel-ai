"""
Contract 028 — Automatic Reflection Persistence Integration.

A completed governed Reflection becomes historical cognition as part
of the Reflection application workflow.

Persistence occurs:

Learning Event Resolution
    ->
Governed Reflection
    ->
Historical Recording
    ->
Formatting
    ->
Public Response

Persistence does not:

- perform Reflection,
- alter governed cognition,
- alter confidence,
- alter constitutional judgment,
- determine admissibility,
- execute Recommendations.

All Reflection outcomes are historical outcomes.

Complete, insufficient, and constitutionally inadmissible Reflection
must remain preservable.
"""

from datetime import UTC, datetime

from app.core.cognition.models import LearningEvent

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

from app.services.cognition.reflection.reflection_api import (
    ReflectionAPIRequest,
)

from app.services.cognition.reflection.reflection_application_service import (
    ReflectionApplicationService,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceResult,
)

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)

from app.services.cognition.reflection.reflection_record_factory import (
    ReflectionRecordFactory,
)


def make_event(
    event_id: str,
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=["engineering"],
        evidence_added=[
            f"evidence-{event_id}",
        ],
        summary=f"Learning recorded for {event_id}.",
    )


def make_governed(
    *,
    status: ReflectionStatus = ReflectionStatus.COMPLETE,
    confidence_score: float = 0.86,
    confidence_level: ReflectionConfidenceLevel = (
        ReflectionConfidenceLevel.HIGH
    ),
    coherent: bool = True,
    admissible: bool = True,
    constitutional_score: float = 1.0,
) -> GovernedReflectionResult:
    patterns = []
    insights = []
    recommendations = []

    if status == ReflectionStatus.COMPLETE:
        pattern = ReflectionPattern(
            pattern_id="pattern-1",
            kind=ReflectionPatternKind.RECURRENCE,
            title="Recurring engineering learning",
            description="Engineering recurs.",
            learning_event_ids=[
                "learning-1",
                "learning-2",
            ],
            evidence_ids=[
                "evidence-1",
            ],
            domain_ids=["engineering"],
        )

        insight = ReflectionInsight(
            insight_id="insight-1",
            title="Engineering remains recurrent",
            explanation="Engineering recurs.",
            pattern_ids=["pattern-1"],
            learning_event_ids=[
                "learning-1",
                "learning-2",
            ],
            evidence_ids=[
                "evidence-1",
            ],
            domain_ids=["engineering"],
            confidence=confidence_score,
        )

        recommendation = ReflectionRecommendation(
            recommendation_id="recommendation-1",
            kind=ReflectionRecommendationKind.STRENGTHEN,
            title="Continue engineering learning",
            description="Continue examining engineering.",
            insight_ids=["insight-1"],
            pattern_ids=["pattern-1"],
            domain_ids=["engineering"],
            priority=1,
            requires_human_approval=True,
        )

        patterns = [pattern]
        insights = [insight]
        recommendations = [recommendation]

    reflection = ReflectionResult(
        title="Historical reflection",
        summary="Reflection result.",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        patterns=patterns,
        insights=insights,
        recommendations=recommendations,
        confidence=ReflectionConfidence(
            score=confidence_score,
            level=confidence_level,
            basis="Historical support assessed.",
            factors=[],
            uncertainty=[],
        ),
        reflection_trace=[
            "Historical Reflection completed.",
        ],
        status=status,
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


class StubResolver:
    def __init__(self):
        self.events = [
            make_event("learning-1"),
            make_event("learning-2"),
        ]

    def resolve(self, learning_event_ids):
        return self.events


class StubOrchestrator:
    def __init__(self, governed):
        self.governed = governed

    def reflect(
        self,
        *,
        learning_events,
        title,
        constitutional_context,
    ):
        return self.governed


class StubFormatter:
    def format(self, governed):
        return "FORMATTED REFLECTION"


class RecordingRepository:
    def __init__(self):
        self.saved: list[ReflectionRecord] = []

    def save(self, record):
        self.saved.append(
            record.model_copy(
                deep=True
            )
        )


def request() -> ReflectionAPIRequest:
    return ReflectionAPIRequest(
        title="Historical reflection",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        constitutional_context=(
            "Reflection remains accountable to reality."
        ),
        mission_id="mission-001",
        session_id="sprint-18",
        organization_id="default",
    )


FIXED_TIME = datetime(
    2026,
    8,
    18,
    16,
    30,
    tzinfo=UTC,
)


def make_service(
    *,
    governed=None,
    repository=None,
):
    governed = (
        governed
        or make_governed()
    )

    repository = (
        repository
        or RecordingRepository()
    )

    service = ReflectionApplicationService(
        resolver=StubResolver(),
        orchestrator=StubOrchestrator(
            governed
        ),
        formatter=StubFormatter(),
        record_factory=ReflectionRecordFactory(),
        history_repository=repository,
        reflection_id_factory=(
            lambda: "reflection-001"
        ),
        clock=(
            lambda: FIXED_TIME
        ),
    )

    return (
        service,
        repository,
        governed,
    )


def test_completed_reflection_is_persisted_automatically():
    service, repository, _ = (
        make_service()
    )

    service.reflect(
        request()
    )

    assert len(
        repository.saved
    ) == 1

    assert (
        repository.saved[0].reflection_id
        == "reflection-001"
    )


def test_persisted_record_preserves_governed_cognition():
    service, repository, governed = (
        make_service()
    )

    service.reflect(
        request()
    )

    record = repository.saved[0]

    assert (
        record.learning_event_ids
        == governed.reflection.learning_event_ids
    )

    assert record.pattern_ids == [
        pattern.pattern_id
        for pattern
        in governed.reflection.patterns
    ]

    assert record.insight_ids == [
        insight.insight_id
        for insight
        in governed.reflection.insights
    ]

    assert record.recommendation_ids == [
        recommendation.recommendation_id
        for recommendation
        in governed.reflection.recommendations
    ]


def test_persisted_record_preserves_constitutional_judgment():
    governed = make_governed(
        coherent=False,
        admissible=False,
        constitutional_score=0.40,
    )

    service, repository, _ = (
        make_service(
            governed=governed
        )
    )

    service.reflect(
        request()
    )

    record = repository.saved[0]

    assert record.coherent is False
    assert record.admissible is False
    assert record.constitutional_score == 0.40


def test_inadmissible_reflection_is_still_persisted():
    governed = make_governed(
        coherent=False,
        admissible=False,
        constitutional_score=0.20,
    )

    service, repository, _ = (
        make_service(
            governed=governed
        )
    )

    service.reflect(
        request()
    )

    assert len(repository.saved) == 1
    assert repository.saved[0].admissible is False


def test_insufficient_evidence_reflection_is_persisted():
    governed = make_governed(
        status=(
            ReflectionStatus
            .INSUFFICIENT_EVIDENCE
        ),
        confidence_score=0.263,
        confidence_level=(
            ReflectionConfidenceLevel.LOW
        ),
    )

    service, repository, _ = (
        make_service(
            governed=governed
        )
    )

    service.reflect(
        request()
    )

    record = repository.saved[0]

    assert (
        record.status
        == "insufficient_evidence"
    )

    assert (
        record.reflection_confidence_score
        == 0.263
    )

    assert record.pattern_ids == []
    assert record.insight_ids == []
    assert record.recommendation_ids == []


def test_record_preserves_mission_context():
    service, repository, _ = (
        make_service()
    )

    service.reflect(
        request()
    )

    record = repository.saved[0]

    assert record.mission_id == "mission-001"
    assert record.session_id == "sprint-18"
    assert record.organization_id == "default"


def test_record_uses_injected_identity_and_clock():
    service, repository, _ = (
        make_service()
    )

    service.reflect(
        request()
    )

    record = repository.saved[0]

    assert (
        record.reflection_id
        == "reflection-001"
    )

    assert record.reflected_at == FIXED_TIME


def test_persistence_does_not_modify_governed_reflection():
    governed = make_governed()

    before = governed.model_dump()

    service, _, _ = make_service(
        governed=governed
    )

    service.reflect(
        request()
    )

    assert governed.model_dump() == before


def test_public_response_is_not_rewritten_by_persistence():
    service, _, governed = (
        make_service()
    )

    response = service.reflect(
        request()
    )

    assert response.title == (
        governed.reflection.title
    )

    assert response.status == (
        governed.reflection.status.value
    )

    assert (
        response.reflection_confidence_score
        == governed.reflection.confidence.score
    )

    assert response.admissible == (
        governed.admissible
    )

    assert (
        response.formatted_reflection
        == "FORMATTED REFLECTION"
    )


def test_persistence_failure_is_not_silently_ignored():
    class FailingRepository:
        def save(self, record):
            raise RuntimeError(
                "history persistence failed"
            )

    service, _, _ = make_service(
        repository=FailingRepository()
    )

    try:
        service.reflect(
            request()
        )
    except RuntimeError as exc:
        assert (
            str(exc)
            == "history persistence failed"
        )
    else:
        raise AssertionError(
            "Persistence failure was silently ignored."
        )


def test_application_service_has_no_repository_mutation_authority():
    service, _, _ = make_service()

    forbidden = [
        "update_history",
        "rewrite_history",
        "delete_history",
        "repair_history",
    ]

    for name in forbidden:
        assert not hasattr(
            service,
            name,
        )
