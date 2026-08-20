"""
Contract 015 — Public Reflection HTTP Boundary.

The route exposes the Reflection Application Service.

It does not:

- resolve Learning Events,
- perform Reflection,
- calculate confidence,
- determine constitutional coherence,
- format Reflection,
- execute Recommendations.

HTTP owns transport.

The Application Service owns workflow.
"""

from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_reflection_route_is_registered_in_openapi():
    schema = app.openapi()

    assert "/reflection" in schema["paths"]

    assert (
        "post"
        in schema["paths"]["/reflection"]
    )


def test_reflection_route_resolves():
    """
    An invalid payload should reach the Reflection route and fail
    validation rather than returning 404.
    """

    response = client.post(
        "/reflection",
        json={},
    )

    assert response.status_code == 422


def test_reflection_route_requires_public_contract():
    response = client.post(
        "/reflection",
        json={
            "title": "Engineering reflection",
        },
    )

    assert response.status_code == 422


def test_reflection_route_rejects_blank_title():
    response = client.post(
        "/reflection",
        json={
            "title": "   ",
            "learning_event_ids": [
                "learning-1",
                "learning-2",
            ],
            "constitutional_context": (
                "Reflection remains accountable to reality."
            ),
        },
    )

    assert response.status_code == 422


def test_reflection_route_rejects_missing_learning_history():
    response = client.post(
        "/reflection",
        json={
            "title": "Engineering reflection",
            "constitutional_context": (
                "Reflection remains accountable to reality."
            ),
        },
    )

    assert response.status_code == 422


def test_reflection_route_exposes_no_execution_endpoint():
    schema = app.openapi()

    paths = schema["paths"]

    forbidden_paths = {
        "/reflection/execute",
        "/reflection/apply",
        "/reflection/repair",
    }

    assert forbidden_paths.isdisjoint(
        paths.keys()
    )
