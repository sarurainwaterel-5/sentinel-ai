"""
Contract 011 — Public Reflection API Boundary.

The public Reflection contract exposes governed Reflection without
granting API consumers authority over internal reflective cognition.

The boundary:

- accepts Learning Events and Reflection mission context,
- preserves structured governed Reflection,
- exposes deterministic communication,
- preserves constitutional admissibility,
- preserves human-approval requirements,
- does not expose execution authority.

The API contract represents cognition.

It does not perform cognition.
"""

from app.services.cognition.reflection.reflection_api import (
    ReflectionAPIRequest,
    ReflectionAPIResponse,
)


def test_request_accepts_learning_events():
    request = ReflectionAPIRequest(
        title="Engineering reflection",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        constitutional_context=(
            "Reflection remains accountable to reality."
        ),
    )

    assert request.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_request_requires_reflection_title():
    request = ReflectionAPIRequest(
        title="Engineering reflection",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        constitutional_context="Constitution.",
    )

    assert request.title == "Engineering reflection"


def test_request_requires_constitutional_context():
    request = ReflectionAPIRequest(
        title="Governed reflection",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        constitutional_context=(
            "Reflection preserves intellectual humility."
        ),
    )

    assert request.constitutional_context


def test_request_preserves_optional_mission_context():
    request = ReflectionAPIRequest(
        title="Mission reflection",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        constitutional_context="Constitution.",
        mission_id="mission-18-001",
        session_id="session-001",
        organization_id="default",
    )

    assert request.mission_id == "mission-18-001"
    assert request.session_id == "session-001"
    assert request.organization_id == "default"


def test_response_preserves_reflection_status():
    response = ReflectionAPIResponse(
        title="Engineering reflection",
        status="complete",
        admissible=True,
        coherent=True,
        reflection_confidence_score=0.90,
        reflection_confidence_level="high",
        constitutional_score=1.0,
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_count=1,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection="REFLECTION: Engineering reflection",
    )

    assert response.status == "complete"


def test_response_keeps_confidence_and_coherence_separate():
    response = ReflectionAPIResponse(
        title="Independent judgments",
        status="complete",
        admissible=False,
        coherent=False,
        reflection_confidence_score=0.99,
        reflection_confidence_level="high",
        constitutional_score=0.20,
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_count=1,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection="INADMISSIBLE",
    )

    assert response.reflection_confidence_score == 0.99
    assert response.constitutional_score == 0.20
    assert response.admissible is False

    assert not hasattr(
        response,
        "combined_score",
    )


def test_response_preserves_learning_event_provenance():
    response = ReflectionAPIResponse(
        title="Traceable reflection",
        status="complete",
        admissible=True,
        coherent=True,
        reflection_confidence_score=0.88,
        reflection_confidence_level="high",
        constitutional_score=1.0,
        learning_event_ids=[
            "learning-4",
            "learning-8",
            "learning-12",
        ],
        pattern_count=2,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection="Traceable reflection.",
    )

    assert response.learning_event_ids == [
        "learning-4",
        "learning-8",
        "learning-12",
    ]


def test_response_surfaces_human_approval_boundary():
    response = ReflectionAPIResponse(
        title="Governed reflection",
        status="complete",
        admissible=True,
        coherent=True,
        reflection_confidence_score=0.90,
        reflection_confidence_level="high",
        constitutional_score=1.0,
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_count=1,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection="Human approval required.",
    )

    assert response.human_approval_required is True


def test_response_exposes_deterministic_communication():
    response = ReflectionAPIResponse(
        title="Readable reflection",
        status="complete",
        admissible=True,
        coherent=True,
        reflection_confidence_score=0.90,
        reflection_confidence_level="high",
        constitutional_score=1.0,
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_count=1,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection=(
            "REFLECTION: Readable reflection"
        ),
    )

    assert (
        response.formatted_reflection
        == "REFLECTION: Readable reflection"
    )


def test_response_contains_no_execution_authority():
    response = ReflectionAPIResponse(
        title="No execution authority",
        status="complete",
        admissible=True,
        coherent=True,
        reflection_confidence_score=0.90,
        reflection_confidence_level="high",
        constitutional_score=1.0,
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_count=1,
        insight_count=1,
        recommendation_count=1,
        human_approval_required=True,
        formatted_reflection="Reflection complete.",
    )

    assert not hasattr(
        response,
        "execution_authorized",
    )

    assert not hasattr(
        response,
        "execute",
    )

    assert not hasattr(
        response,
        "execution_result",
    )
