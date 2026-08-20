"""
Contract 013 — Learning Event Resolver.

The Resolver translates requested Learning Event identities into
authoritative cognitive history.

It does not:

- create Learning Events,
- reconstruct history from caller payloads,
- modify stored Learning Events,
- discover Patterns,
- generate Insights,
- perform Reflection,
- interpret meaning.

The Repository owns history.

The Resolver locates history.
"""

from copy import deepcopy

import pytest

from app.core.cognition.models import LearningEvent

from app.repositories.learning_event_repository import (
    LearningEventNotFoundError,
)

from app.services.cognition.reflection.learning_event_resolver import (
    LearningEventResolver,
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


class StubLearningEventRepository:
    """
    Controlled history authority for resolver contract testing.
    """

    def __init__(
        self,
        events: list[LearningEvent],
    ):
        self.events = {
            event.learning_event_id: event
            for event in events
        }

        self.calls: list[list[str]] = []

    def get_many(
        self,
        learning_event_ids: list[str],
    ) -> list[LearningEvent]:
        self.calls.append(
            list(learning_event_ids)
        )

        unique_ids = list(
            dict.fromkeys(
                learning_event_ids
            )
        )

        resolved: list[LearningEvent] = []

        for event_id in unique_ids:
            if event_id not in self.events:
                raise LearningEventNotFoundError(
                    f"Learning Event '{event_id}' was not found."
                )

            resolved.append(
                deepcopy(
                    self.events[event_id]
                )
            )

        return resolved


def test_resolver_returns_authoritative_learning_events():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    events = resolver.resolve(
        [
            "learning-1",
            "learning-2",
        ]
    )

    assert [
        event.learning_event_id
        for event in events
    ] == [
        "learning-1",
        "learning-2",
    ]


def test_resolver_preserves_requested_order():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
            make_event(
                event_id="learning-3",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    events = resolver.resolve(
        [
            "learning-3",
            "learning-1",
            "learning-2",
        ]
    )

    assert [
        event.learning_event_id
        for event in events
    ] == [
        "learning-3",
        "learning-1",
        "learning-2",
    ]


def test_resolver_deduplicates_requested_ids():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    events = resolver.resolve(
        [
            "learning-1",
            "learning-1",
            "learning-2",
        ]
    )

    assert [
        event.learning_event_id
        for event in events
    ] == [
        "learning-1",
        "learning-2",
    ]


def test_resolver_delegates_to_repository_once():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    requested = [
        "learning-2",
        "learning-1",
    ]

    resolver.resolve(
        requested
    )

    assert repository.calls == [
        requested
    ]


def test_missing_learning_event_fails_visibly():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    with pytest.raises(
        LearningEventNotFoundError,
        match="learning-99",
    ):
        resolver.resolve(
            [
                "learning-1",
                "learning-99",
            ]
        )


def test_resolver_does_not_modify_requested_ids():
    repository = StubLearningEventRepository(
        [
            make_event(
                event_id="learning-1",
            ),
            make_event(
                event_id="learning-2",
            ),
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    requested = [
        "learning-2",
        "learning-1",
    ]

    before = list(
        requested
    )

    resolver.resolve(
        requested
    )

    assert requested == before


def test_resolver_does_not_modify_resolved_history():
    original = make_event(
        event_id="learning-1",
    )

    repository = StubLearningEventRepository(
        [
            original,
        ]
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    before = deepcopy(
        original
    )

    resolver.resolve(
        [
            "learning-1",
        ]
    )

    assert original == before


def test_resolver_returns_no_history_for_empty_request():
    repository = StubLearningEventRepository(
        []
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    events = resolver.resolve(
        []
    )

    assert events == []


def test_resolver_has_no_reflection_authority():
    repository = StubLearningEventRepository(
        []
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    assert not hasattr(
        resolver,
        "reflect",
    )

    assert not hasattr(
        resolver,
        "discover_patterns",
    )

    assert not hasattr(
        resolver,
        "generate_insights",
    )


def test_resolver_has_no_history_creation_authority():
    repository = StubLearningEventRepository(
        []
    )

    resolver = LearningEventResolver(
        repository=repository
    )

    assert not hasattr(
        resolver,
        "save",
    )

    assert not hasattr(
        resolver,
        "record_learning",
    )

    assert not hasattr(
        resolver,
        "create_learning_event",
    )
