"""
Contract 014 — Reflection Application Service.

The application service coordinates the public Reflection workflow.

It does not:

- create Learning Events,
- resolve history itself,
- perform Reflection,
- calculate confidence,
- determine constitutional coherence,
- rewrite governed cognition,
- execute Recommendations.

The service coordinates authorities.

Authorities retain their responsibilities.
"""

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.reflection_api import (
    ReflectionAPIRequest,
)

from app.services.cognition.reflection.reflection_application_service import (
    ReflectionApplicationService,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceResult,
)

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

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)


def make_event(
    *,
    event_id: str,
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=["engineering"],
        evidence_added=[
            f"evidence-{event_id}",
        ],
        summary=(
            f"Learning recorded for {event_id}."
        ),
    )


def make_governed_result() -> GovernedReflectionResult:
    pattern = ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring engineering learning",
        description=(
            "Engineering recurs across accumulated learning."
        ),
        learning_event_ids=[
            "learning-8",
            "learning-12",
        ],
        evidence_ids=[],
        domain_ids=["engineering"],
    )

    insight = ReflectionInsight(
        insight_id="insight-1",
        title="Engineering remains recurrent",
        explanation=(
            "Engineering represents a repeated learning area."
        ),
        pattern_ids=["pattern-1"],
        learning_event_ids=[
            "learning-8",
            "learning-12",
        ],
        evidence_ids=[],
        domain_ids=["engineering"],
        confidence=0.80,
    )

    recommendation = ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue engineering learning",
        description=(
            "Future learning should continue examining engineering."
        ),
        insight_ids=["insight-1"],
        pattern_ids=["pattern-1"],
        domain_ids=["engineering"],
        priority=1,
        requires_human_approval=True,
    )

    reflection = ReflectionResult(
        title="Engineering reflection",
        summary="Reflection completed.",
        learning_event_ids=[
            "learning-8",
            "learning-12",
        ],
        patterns=[pattern],
        insights=[insight],
        recommendations=[recommendation],
        confidence=ReflectionConfidence(
            score=0.88,
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
        coherent=True,
        admissible=True,
        constitutional_score=1.0,
        reflection_confidence=0.88,
        articles_consulted=[],
        conflicts=[],
        recommendations=[],
    )

    return GovernedReflectionResult(
        reflection=reflection,
        coherence=coherence,
        admissible=True,
    )


class StubResolver:
    def __init__(
        self,
        events,
    ):
        self.events = events
        self.calls = []

    def resolve(
        self,
        learning_event_ids,
    ):
        self.calls.append(
            list(learning_event_ids)
        )
        return self.events


class StubOrchestrator:
    def __init__(
        self,
        result,
    ):
        self.result = result
        self.calls = []

    def reflect(
        self,
        *,
        learning_events,
        title,
        constitutional_context,
    ):
        self.calls.append(
            {
                "learning_events": learning_events,
                "title": title,
                "constitutional_context": constitutional_context,
            }
        )
        return self.result


class StubFormatter:
    def __init__(
        self,
        output="FORMATTED REFLECTION",
    ):
        self.output = output
        self.calls = []

    def format(
        self,
        governed,
    ):
        self.calls.append(
            governed
        )
        return self.output


def make_request():
    return ReflectionAPIRequest(
        title="Engineering reflection",
        learning_event_ids=[
            "learning-8",
            "learning-12",
        ],
        constitutional_context=(
            "Reflection remains accountable to reality."
        ),
        mission_id="reflection-mission-001",
        session_id="session-001",
        organization_id="default",
    )


def test_service_resolves_authoritative_history():
    events = [
        make_event(
            event_id="learning-8",
        ),
        make_event(
            event_id="learning-12",
        ),
    ]

    resolver = StubResolver(
        events
    )

    service = ReflectionApplicationService(
        resolver=resolver,
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    service.reflect(
        make_request()
    )

    assert resolver.calls == [
        [
            "learning-8",
            "learning-12",
        ]
    ]


def test_service_passes_resolved_objects_to_orchestrator():
    events = [
        make_event(
            event_id="learning-8",
        ),
        make_event(
            event_id="learning-12",
        ),
    ]

    orchestrator = StubOrchestrator(
        make_governed_result()
    )

    service = ReflectionApplicationService(
        resolver=StubResolver(
            events
        ),
        orchestrator=orchestrator,
        formatter=StubFormatter(),
    )

    service.reflect(
        make_request()
    )

    assert (
        orchestrator.calls[0]["learning_events"]
        is events
    )


def test_service_preserves_title_and_constitutional_context():
    orchestrator = StubOrchestrator(
        make_governed_result()
    )

    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=orchestrator,
        formatter=StubFormatter(),
    )

    request = make_request()

    service.reflect(
        request
    )

    call = orchestrator.calls[0]

    assert call["title"] == request.title
    assert (
        call["constitutional_context"]
        == request.constitutional_context
    )


def test_service_formats_governed_reflection():
    governed = make_governed_result()

    formatter = StubFormatter(
        output="SENTINEL REFLECTION"
    )

    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=StubOrchestrator(
            governed
        ),
        formatter=formatter,
    )

    response = service.reflect(
        make_request()
    )

    assert formatter.calls == [
        governed
    ]

    assert (
        response.formatted_reflection
        == "SENTINEL REFLECTION"
    )


def test_response_preserves_governed_judgments():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    response = service.reflect(
        make_request()
    )

    assert response.status == "complete"
    assert response.admissible is True
    assert response.coherent is True

    assert (
        response.reflection_confidence_score
        == 0.88
    )

    assert (
        response.constitutional_score
        == 1.0
    )


def test_response_preserves_learning_event_provenance():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    response = service.reflect(
        make_request()
    )

    assert response.learning_event_ids == [
        "learning-8",
        "learning-12",
    ]


def test_response_preserves_human_approval_boundary():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    response = service.reflect(
        make_request()
    )

    assert (
        response.human_approval_required
        is True
    )


def test_response_preserves_mission_context():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            [
                make_event(
                    event_id="learning-8",
                ),
                make_event(
                    event_id="learning-12",
                ),
            ]
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    response = service.reflect(
        make_request()
    )

    assert (
        response.mission_id
        == "reflection-mission-001"
    )

    assert (
        response.session_id
        == "session-001"
    )

    assert (
        response.organization_id
        == "default"
    )


def test_service_has_no_reflection_authority():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            []
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    assert not hasattr(
        service,
        "discover_patterns",
    )

    assert not hasattr(
        service,
        "generate_insights",
    )

    assert not hasattr(
        service,
        "calculate_confidence",
    )


def test_service_has_no_execution_authority():
    service = ReflectionApplicationService(
        resolver=StubResolver(
            []
        ),
        orchestrator=StubOrchestrator(
            make_governed_result()
        ),
        formatter=StubFormatter(),
    )

    assert not hasattr(
        service,
        "execute",
    )

    assert not hasattr(
        service,
        "execution_authorized",
    )
