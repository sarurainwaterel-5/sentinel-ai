"""
Contract 023 — Durable Reflection History.

A ReflectionRecord preserves the result of Reflection at a particular
moment in SentinelAI's cognitive history.

Reflection history must preserve:

- identity,
- mission/session/organization context,
- time,
- source Learning Event provenance,
- Reflection status,
- confidence,
- constitutional judgment,
- derived cognitive provenance,
- longitudinal Understanding provenance,
- reflective trends.

Completed, insufficient, conflicted, and otherwise admissible historical
Reflection outcomes remain part of history.

Historical Reflection is append-only.

Future cognition may examine it.

Future cognition may not rewrite it.
"""

from datetime import UTC, datetime

import pytest

from app.services.cognition.reflection.reflection_history import (
    DuplicateReflectionRecordError,
    ReflectionHistory,
    ReflectionRecord,
)


def reflected_at(
    day: int,
) -> datetime:
    return datetime(
        2026,
        8,
        day,
        12,
        0,
        tzinfo=UTC,
    )


def make_record(
    *,
    reflection_id: str = "reflection-001",
    mission_id: str = "mission-001",
    status: str = "complete",
    confidence_score: float = 0.86,
    confidence_level: str = "high",
    admissible: bool = True,
    coherent: bool = True,
    constitutional_score: float = 1.0,
    day: int = 18,
) -> ReflectionRecord:
    return ReflectionRecord(
        reflection_id=reflection_id,
        mission_id=mission_id,
        session_id="sprint-18",
        organization_id="default",
        reflected_at=reflected_at(day),
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


def test_history_appends_reflection_record():
    history = ReflectionHistory()

    record = make_record()

    history.append(record)

    assert history.count == 1

    assert history.get(
        "reflection-001"
    ) == record


def test_history_preserves_append_order():
    history = ReflectionHistory()

    first = make_record(
        reflection_id="reflection-001",
        mission_id="mission-001",
        day=17,
    )

    second = make_record(
        reflection_id="reflection-002",
        mission_id="mission-002",
        day=18,
    )

    history.append(first)
    history.append(second)

    assert [
        record.reflection_id
        for record in history.records()
    ] == [
        "reflection-001",
        "reflection-002",
    ]


def test_duplicate_reflection_id_is_rejected():
    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-001",
        )
    )

    with pytest.raises(
        DuplicateReflectionRecordError,
        match="reflection-001",
    ):
        history.append(
            make_record(
                reflection_id="reflection-001",
                mission_id="different-mission",
            )
        )


def test_complete_reflection_is_preserved():
    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-complete",
            status="complete",
            confidence_score=0.86,
            confidence_level="high",
        )
    )

    record = history.get(
        "reflection-complete"
    )

    assert record is not None
    assert record.status == "complete"
    assert (
        record.reflection_confidence_score
        == 0.86
    )


def test_insufficient_reflection_is_also_preserved():
    """
    Reflection history must not contain survivorship bias.
    """

    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-insufficient",
            status="insufficient_evidence",
            confidence_score=0.263,
            confidence_level="low",
        )
    )

    record = history.get(
        "reflection-insufficient"
    )

    assert record is not None

    assert (
        record.status
        == "insufficient_evidence"
    )

    assert (
        record.reflection_confidence_score
        == 0.263
    )


def test_record_preserves_learning_event_provenance():
    record = make_record()

    assert record.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_record_preserves_derived_cognitive_provenance():
    record = make_record()

    assert record.pattern_ids == [
        "pattern-1"
    ]

    assert record.insight_ids == [
        "insight-1"
    ]

    assert record.recommendation_ids == [
        "recommendation-1"
    ]


def test_record_preserves_longitudinal_provenance():
    record = make_record()

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


def test_record_preserves_constitutional_judgment():
    record = make_record(
        admissible=False,
        coherent=False,
        constitutional_score=0.40,
    )

    assert record.admissible is False
    assert record.coherent is False
    assert record.constitutional_score == 0.40


def test_get_unknown_reflection_returns_none():
    history = ReflectionHistory()

    assert history.get(
        "reflection-missing"
    ) is None


def test_records_returns_snapshot_not_internal_collection():
    history = ReflectionHistory()

    history.append(
        make_record()
    )

    snapshot = history.records()

    snapshot.clear()

    assert history.count == 1

    assert history.get(
        "reflection-001"
    ) is not None


def test_mutating_original_record_does_not_rewrite_history():
    """
    Once appended, later mutation of the caller-owned object must not
    alter the historical Reflection snapshot.
    """

    history = ReflectionHistory()

    record = make_record()

    history.append(record)

    record.status = "rewritten"
    record.learning_event_ids.append(
        "manufactured-learning"
    )

    historical = history.get(
        "reflection-001"
    )

    assert historical is not None

    assert historical.status == "complete"

    assert historical.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]


def test_mutating_retrieved_record_does_not_rewrite_history():
    """
    Reads must not expose mutable internal historical state.
    """

    history = ReflectionHistory()

    history.append(
        make_record()
    )

    retrieved = history.get(
        "reflection-001"
    )

    assert retrieved is not None

    retrieved.status = "rewritten"

    reread = history.get(
        "reflection-001"
    )

    assert reread is not None
    assert reread.status == "complete"


def test_mutating_records_snapshot_does_not_rewrite_history():
    history = ReflectionHistory()

    history.append(
        make_record()
    )

    snapshot = history.records()

    snapshot[0].reflective_trends.append(
        "manufactured-trend"
    )

    reread = history.get(
        "reflection-001"
    )

    assert reread is not None

    assert reread.reflective_trends == [
        "revision",
        "reinforcement",
    ]


def test_history_can_filter_by_mission():
    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-001a",
            mission_id="mission-001",
            day=17,
        )
    )

    history.append(
        make_record(
            reflection_id="reflection-001b",
            mission_id="mission-001",
            day=18,
        )
    )

    history.append(
        make_record(
            reflection_id="reflection-002",
            mission_id="mission-002",
            day=18,
        )
    )

    results = history.for_mission(
        "mission-001"
    )

    assert [
        record.reflection_id
        for record in results
    ] == [
        "reflection-001a",
        "reflection-001b",
    ]


def test_history_can_return_chronological_records():
    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-later",
            day=18,
        )
    )

    history.append(
        make_record(
            reflection_id="reflection-earlier",
            day=16,
        )
    )

    ordered = history.chronological()

    assert [
        record.reflection_id
        for record in ordered
    ] == [
        "reflection-earlier",
        "reflection-later",
    ]


def test_equal_timestamps_preserve_append_order():
    """
    Equal timestamps provide no basis for historical reordering.
    """

    history = ReflectionHistory()

    history.append(
        make_record(
            reflection_id="reflection-b",
            day=18,
        )
    )

    history.append(
        make_record(
            reflection_id="reflection-a",
            day=18,
        )
    )

    ordered = history.chronological()

    assert [
        record.reflection_id
        for record in ordered
    ] == [
        "reflection-b",
        "reflection-a",
    ]


def test_reflection_history_has_no_rewrite_authority():
    history = ReflectionHistory()

    forbidden = [
        "update",
        "replace",
        "rewrite",
        "delete",
        "remove",
        "correct",
        "repair",
        "execute",
    ]

    for name in forbidden:
        assert not hasattr(
            history,
            name,
        )
