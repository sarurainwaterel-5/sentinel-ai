"""
Contract 024 — Reflection History Repository.

The Reflection History Repository provides a persistence boundary for
historical ReflectionRecords.

It must preserve:

- Reflection identity,
- mission/session/organization context,
- timestamps,
- Learning Event provenance,
- derived cognitive provenance,
- Reflection status and confidence,
- constitutional judgment,
- longitudinal provenance,
- reflective trends,
- chronological history.

Historical Reflection remains append-only.

Persistence must not become rewrite authority.
"""

from datetime import UTC, datetime

import pytest

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)

from app.services.cognition.reflection.reflection_history_repository import (
    DuplicatePersistedReflectionError,
    InMemoryReflectionHistoryRepository,
)


def make_record(
    *,
    reflection_id: str = "reflection-001",
    mission_id: str = "mission-001",
    session_id: str = "sprint-18",
    organization_id: str = "default",
    day: int = 18,
    hour: int = 12,
    status: str = "complete",
    confidence_score: float = 0.86,
    confidence_level: str = "high",
    coherent: bool = True,
    constitutional_score: float = 1.0,
    admissible: bool = True,
) -> ReflectionRecord:
    return ReflectionRecord(
        reflection_id=reflection_id,
        mission_id=mission_id,
        session_id=session_id,
        organization_id=organization_id,
        reflected_at=datetime(
            2026,
            8,
            day,
            hour,
            0,
            tzinfo=UTC,
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_ids=[
            "pattern-1",
        ],
        insight_ids=[
            "insight-1",
        ],
        recommendation_ids=[
            "recommendation-1",
        ],
        status=status,
        reflection_confidence_score=(
            confidence_score
        ),
        reflection_confidence_level=(
            confidence_level
        ),
        coherent=coherent,
        constitutional_score=(
            constitutional_score
        ),
        admissible=admissible,
        longitudinal_understanding_ids=[
            "understanding-v1",
            "understanding-v2",
        ],
        reflective_trends=[
            "revision",
            "reinforcement",
        ],
    )


def test_repository_saves_and_retrieves_record():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    record = make_record()

    repository.save(record)

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded == record


def test_repository_returns_none_for_unknown_record():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    assert repository.get(
        "reflection-missing"
    ) is None


def test_repository_rejects_duplicate_identity():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-001",
        )
    )

    with pytest.raises(
        DuplicatePersistedReflectionError,
        match="reflection-001",
    ):
        repository.save(
            make_record(
                reflection_id="reflection-001",
                mission_id="different-mission",
            )
        )


def test_repository_preserves_insufficient_evidence_record():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-001a",
            status="insufficient_evidence",
            confidence_score=0.263,
            confidence_level="low",
        )
    )

    loaded = repository.get(
        "reflection-001a"
    )

    assert loaded is not None

    assert (
        loaded.status
        == "insufficient_evidence"
    )

    assert (
        loaded.reflection_confidence_score
        == 0.263
    )

    assert (
        loaded.reflection_confidence_level
        == "low"
    )


def test_repository_preserves_complete_record():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-001b",
            status="complete",
            confidence_score=0.86,
            confidence_level="high",
        )
    )

    loaded = repository.get(
        "reflection-001b"
    )

    assert loaded is not None
    assert loaded.status == "complete"

    assert (
        loaded.reflection_confidence_score
        == 0.86
    )


def test_repository_preserves_learning_event_provenance():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record()
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None

    assert loaded.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_repository_preserves_derived_cognitive_provenance():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record()
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None

    assert loaded.pattern_ids == [
        "pattern-1",
    ]

    assert loaded.insight_ids == [
        "insight-1",
    ]

    assert loaded.recommendation_ids == [
        "recommendation-1",
    ]


def test_repository_preserves_longitudinal_provenance():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record()
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None

    assert (
        loaded.longitudinal_understanding_ids
        == [
            "understanding-v1",
            "understanding-v2",
        ]
    )

    assert loaded.reflective_trends == [
        "revision",
        "reinforcement",
    ]


def test_repository_preserves_constitutional_judgment():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            coherent=False,
            constitutional_score=0.40,
            admissible=False,
        )
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None
    assert loaded.coherent is False

    assert (
        loaded.constitutional_score
        == 0.40
    )

    assert loaded.admissible is False


def test_repository_filters_by_mission():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-001a",
            mission_id="mission-001",
            day=17,
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-001b",
            mission_id="mission-001",
            day=18,
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-002",
            mission_id="mission-002",
            day=18,
        )
    )

    results = repository.for_mission(
        "mission-001"
    )

    assert [
        record.reflection_id
        for record in results
    ] == [
        "reflection-001a",
        "reflection-001b",
    ]


def test_repository_filters_by_organization():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-default",
            organization_id="default",
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-other",
            organization_id="other",
        )
    )

    results = repository.for_organization(
        "default"
    )

    assert [
        record.reflection_id
        for record in results
    ] == [
        "reflection-default",
    ]


def test_repository_returns_stable_chronology():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-later",
            day=18,
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-earlier",
            day=16,
        )
    )

    results = repository.chronological()

    assert [
        record.reflection_id
        for record in results
    ] == [
        "reflection-earlier",
        "reflection-later",
    ]


def test_equal_timestamps_preserve_save_order():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record(
            reflection_id="reflection-b",
            day=18,
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-a",
            day=18,
        )
    )

    results = repository.chronological()

    assert [
        record.reflection_id
        for record in results
    ] == [
        "reflection-b",
        "reflection-a",
    ]


def test_mutating_original_after_save_does_not_change_repository():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    record = make_record()

    repository.save(record)

    record.status = "rewritten"
    record.learning_event_ids.append(
        "manufactured-learning"
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None
    assert loaded.status == "complete"

    assert loaded.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_mutating_loaded_record_does_not_change_repository():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record()
    )

    loaded = repository.get(
        "reflection-001"
    )

    assert loaded is not None

    loaded.status = "rewritten"

    loaded.reflective_trends.append(
        "manufactured-trend"
    )

    reread = repository.get(
        "reflection-001"
    )

    assert reread is not None
    assert reread.status == "complete"

    assert reread.reflective_trends == [
        "revision",
        "reinforcement",
    ]


def test_mutating_query_results_does_not_change_repository():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    repository.save(
        make_record()
    )

    results = repository.chronological()

    results[0].status = "rewritten"

    reread = repository.get(
        "reflection-001"
    )

    assert reread is not None
    assert reread.status == "complete"


def test_repository_count_tracks_persisted_history():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    assert repository.count == 0

    repository.save(
        make_record(
            reflection_id="reflection-001",
        )
    )

    repository.save(
        make_record(
            reflection_id="reflection-002",
        )
    )

    assert repository.count == 2


def test_repository_has_no_update_or_delete_authority():
    repository = (
        InMemoryReflectionHistoryRepository()
    )

    forbidden = [
        "update",
        "replace",
        "overwrite",
        "delete",
        "remove",
        "rewrite",
        "repair",
        "execute",
    ]

    for name in forbidden:
        assert not hasattr(
            repository,
            name,
        )
