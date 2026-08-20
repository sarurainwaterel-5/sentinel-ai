"""
Contract 017 — Temporal Learning Analysis.

Temporal Learning Analysis examines the chronology of authoritative
Learning Events.

It may establish:

- chronological order,
- earliest and latest learning,
- temporal span,
- recurring domains across time,
- continuity,
- gaps between learning events.

It may not establish:

- improvement,
- decline,
- correctness,
- incorrectness,
- strengthening,
- weakening,
- revision,
- contradiction.

Time establishes sequence.

Time does not establish meaning.
"""

from datetime import UTC, datetime

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.temporal_learning_analyzer import (
    TemporalLearningAnalyzer,
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
    domains: list[str],
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=domains,
        evidence_added=[
            f"evidence-{event_id}",
        ],
        summary=(
            f"Learning recorded for {event_id}."
        ),
        learned_at=learned_at,
    )


def test_analyzer_orders_learning_events_chronologically():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-3",
                learned_at=dt(2026, 3, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 2, 1),
                domains=["engineering"],
            ),
        ]
    )

    assert result.ordered_learning_event_ids == [
        "learning-1",
        "learning-2",
        "learning-3",
    ]


def test_analyzer_identifies_temporal_boundaries():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 4, 15),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 10),
                domains=["engineering"],
            ),
        ]
    )

    assert result.earliest_learning_event_id == (
        "learning-1"
    )

    assert result.latest_learning_event_id == (
        "learning-2"
    )

    assert result.started_at == dt(
        2026,
        1,
        10,
    )

    assert result.ended_at == dt(
        2026,
        4,
        15,
    )


def test_analyzer_calculates_temporal_span():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 1, 11),
                domains=["engineering"],
            ),
        ]
    )

    assert result.span_seconds == (
        10 * 24 * 60 * 60
    )


def test_analyzer_identifies_recurring_domains_across_time():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 2, 1),
                domains=["cognition"],
            ),
            make_event(
                event_id="learning-3",
                learned_at=dt(2026, 3, 1),
                domains=["engineering"],
            ),
        ]
    )

    assert result.recurring_domain_ids == [
        "engineering"
    ]


def test_single_domain_occurrence_is_not_temporal_recurrence():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 2, 1),
                domains=["cognition"],
            ),
        ]
    )

    assert result.recurring_domain_ids == []


def test_duplicate_domain_inside_one_event_does_not_create_recurrence():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=[
                    "engineering",
                    "engineering",
                ],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 2, 1),
                domains=["cognition"],
            ),
        ]
    )

    assert result.recurring_domain_ids == []


def test_analyzer_preserves_equal_timestamp_input_order():
    """
    Equal timestamps contain no temporal evidence for reordering.

    Stable input order must therefore be preserved.
    """

    timestamp = dt(
        2026,
        1,
        1,
    )

    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-b",
                learned_at=timestamp,
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-a",
                learned_at=timestamp,
                domains=["engineering"],
            ),
        ]
    )

    assert result.ordered_learning_event_ids == [
        "learning-b",
        "learning-a",
    ]


def test_analyzer_records_gaps_between_consecutive_events():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                learned_at=dt(2026, 1, 4),
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-3",
                learned_at=dt(2026, 1, 10),
                domains=["engineering"],
            ),
        ]
    )

    assert len(result.gaps) == 2

    assert (
        result.gaps[0].earlier_learning_event_id
        == "learning-1"
    )

    assert (
        result.gaps[0].later_learning_event_id
        == "learning-2"
    )

    assert result.gaps[0].gap_seconds == (
        3 * 24 * 60 * 60
    )

    assert result.gaps[1].gap_seconds == (
        6 * 24 * 60 * 60
    )


def test_empty_history_produces_empty_temporal_analysis():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze([])

    assert result.event_count == 0
    assert result.ordered_learning_event_ids == []
    assert result.earliest_learning_event_id is None
    assert result.latest_learning_event_id is None
    assert result.started_at is None
    assert result.ended_at is None
    assert result.span_seconds == 0
    assert result.recurring_domain_ids == []
    assert result.gaps == []


def test_single_event_has_zero_span_and_no_gaps():
    analyzer = TemporalLearningAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                learned_at=dt(2026, 1, 1),
                domains=["engineering"],
            ),
        ]
    )

    assert result.event_count == 1

    assert result.ordered_learning_event_ids == [
        "learning-1"
    ]

    assert result.span_seconds == 0
    assert result.gaps == []


def test_temporal_analysis_does_not_modify_learning_events():
    event = make_event(
        event_id="learning-1",
        learned_at=dt(2026, 1, 1),
        domains=["engineering"],
    )

    original_domains = list(
        event.domain_ids
    )

    original_timestamp = (
        event.learned_at
    )

    analyzer = TemporalLearningAnalyzer()

    analyzer.analyze(
        [
            event,
        ]
    )

    assert event.domain_ids == original_domains
    assert event.learned_at == original_timestamp


def test_temporal_analyzer_has_no_interpretive_authority():
    analyzer = TemporalLearningAnalyzer()

    forbidden_authorities = [
        "determine_improvement",
        "determine_decline",
        "determine_correctness",
        "determine_revision",
        "determine_contradiction",
        "strengthen_understanding",
        "weaken_understanding",
        "generate_insights",
        "generate_recommendations",
        "reflect",
    ]

    for authority in forbidden_authorities:
        assert not hasattr(
            analyzer,
            authority,
        )
