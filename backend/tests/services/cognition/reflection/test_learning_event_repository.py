"""
Contract 012 — Durable Cognitive History.

The Learning Event Repository preserves SentinelAI's intellectual
history.

It does not:

- discover Patterns,
- generate Insights,
- perform Reflection,
- modify Learning Events,
- rewrite cognitive history,
- interpret meaning,
- execute recommendations.

Learning records change.

The repository preserves that record.
"""

from copy import deepcopy

import pytest

from app.core.cognition.models import LearningEvent

from app.repositories.learning_event_repository import (
    LearningEventNotFoundError,
    LearningEventRepository,
)


def make_event(
    *,
    event_id: str,
    source: str | None = None,
    domains: list[str] | None = None,
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=(
            source
            or f"source-{event_id}"
        ),
        domain_ids=(
            domains
            or ["engineering"]
        ),
        evidence_added=[
            f"evidence-{event_id}"
        ],
        summary=(
            f"Learning recorded for {event_id}."
        ),
    )


def test_repository_saves_and_retrieves_learning_event(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    event = make_event(
        event_id="learning-1",
    )

    repository.save(event)

    restored = repository.get(
        "learning-1"
    )

    assert restored == event


def test_repository_preserves_learning_event_identity(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    event = make_event(
        event_id="learning-42",
    )

    repository.save(event)

    restored = repository.get(
        "learning-42"
    )

    assert (
        restored.learning_event_id
        == "learning-42"
    )


def test_repository_missing_event_fails_visibly(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    with pytest.raises(
        LearningEventNotFoundError,
        match="learning-missing",
    ):
        repository.get(
            "learning-missing"
        )


def test_get_many_preserves_requested_order(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    for event_id in [
        "learning-1",
        "learning-2",
        "learning-3",
    ]:
        repository.save(
            make_event(
                event_id=event_id,
            )
        )

    events = repository.get_many(
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


def test_get_many_deduplicates_requested_ids(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    repository.save(
        make_event(
            event_id="learning-1",
        )
    )

    repository.save(
        make_event(
            event_id="learning-2",
        )
    )

    events = repository.get_many(
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


def test_get_many_fails_if_any_requested_event_is_missing(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    repository.save(
        make_event(
            event_id="learning-1",
        )
    )

    with pytest.raises(
        LearningEventNotFoundError,
        match="learning-99",
    ):
        repository.get_many(
            [
                "learning-1",
                "learning-99",
            ]
        )


def test_repository_does_not_modify_event_on_save(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    event = make_event(
        event_id="learning-1",
    )

    before = deepcopy(event)

    repository.save(event)

    assert event == before


def test_retrieved_event_is_independent_copy(tmp_path):
    """
    Mutating a retrieved object must not rewrite durable history.
    """

    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    repository.save(
        make_event(
            event_id="learning-1",
        )
    )

    first = repository.get(
        "learning-1"
    )

    first.summary = (
        "Caller attempted to rewrite history."
    )

    second = repository.get(
        "learning-1"
    )

    assert (
        second.summary
        == "Learning recorded for learning-1."
    )


def test_existing_learning_event_cannot_be_silently_overwritten(tmp_path):
    """
    Historical cognition is immutable by default.
    """

    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    original = make_event(
        event_id="learning-1",
        source="original-source",
    )

    replacement = make_event(
        event_id="learning-1",
        source="replacement-source",
    )

    repository.save(
        original
    )

    with pytest.raises(
        ValueError,
        match="already exists",
    ):
        repository.save(
            replacement
        )

    restored = repository.get(
        "learning-1"
    )

    assert restored.source == (
        "original-source"
    )


def test_repository_persists_across_instances(tmp_path):
    """
    Cognitive history must outlive one repository object or process
    boundary.
    """

    database_path = (
        tmp_path / "learning-events.sqlite3"
    )

    first_repository = (
        LearningEventRepository(
            database_path=database_path
        )
    )

    first_repository.save(
        make_event(
            event_id="learning-1",
        )
    )

    second_repository = (
        LearningEventRepository(
            database_path=database_path
        )
    )

    restored = second_repository.get(
        "learning-1"
    )

    assert (
        restored.learning_event_id
        == "learning-1"
    )


def test_repository_has_no_reflection_authority(tmp_path):
    repository = LearningEventRepository(
        database_path=(
            tmp_path / "learning-events.sqlite3"
        )
    )

    assert not hasattr(
        repository,
        "reflect",
    )

    assert not hasattr(
        repository,
        "discover_patterns",
    )

    assert not hasattr(
        repository,
        "generate_insights",
    )
