"""
Contract 016 — Domain-Cohort Comparability.

Reflection requires comparable cognitive history.

Comparability does not require every Learning Event to share one
universal domain.

A domain establishes a comparable historical cohort when it appears
across at least two distinct Learning Events.

This preserves conservative Reflection while allowing SentinelAI to
reflect responsibly across a diverse intellectual history.
"""

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAnalyzer,
    ReflectionHistoryStatus,
)


def make_event(
    *,
    event_id: str,
    domains: list[str],
) -> LearningEvent:
    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=domains,
        evidence_added=[
            f"evidence-{event_id}",
        ],
        summary=f"Learning recorded for {event_id}.",
    )


def test_two_events_in_same_domain_are_comparable():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus.SUFFICIENT
    )

    assert assessment.history_sufficient is True

    assert assessment.shared_domain_ids == [
        "engineering"
    ]


def test_multiple_independent_domain_cohorts_are_comparable():
    """
    This reproduces the structural condition exposed by Mission 001.
    """

    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-3",
                domains=["cognition"],
            ),
            make_event(
                event_id="learning-4",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-5",
                domains=["cognition"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus.SUFFICIENT
    )

    assert assessment.history_sufficient is True

    assert assessment.shared_domain_ids == [
        "cognition",
        "engineering",
    ]


def test_one_comparable_cohort_survives_unrelated_history():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-3",
                domains=["trading"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus.SUFFICIENT
    )

    assert assessment.shared_domain_ids == [
        "engineering"
    ]


def test_unrelated_event_cannot_destroy_existing_comparability():
    """
    Adding unrelated knowledge must not make previously comparable
    history epistemically unusable.
    """

    analyzer = ReflectionHistoryAnalyzer()

    before = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
        ]
    )

    after = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-3",
                domains=["trading"],
            ),
        ]
    )

    assert before.history_sufficient is True
    assert after.history_sufficient is True

    assert before.shared_domain_ids == [
        "engineering"
    ]

    assert after.shared_domain_ids == [
        "engineering"
    ]


def test_two_unrelated_events_are_not_comparable():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["cognition"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus
        .INSUFFICIENT_COMPARABILITY
    )

    assert assessment.history_sufficient is False

    assert assessment.shared_domain_ids == []


def test_many_unique_domains_are_not_comparable():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["cognition"],
            ),
            make_event(
                event_id="learning-3",
                domains=["trading"],
            ),
            make_event(
                event_id="learning-4",
                domains=["business"],
            ),
            make_event(
                event_id="learning-5",
                domains=["philosophy"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus
        .INSUFFICIENT_COMPARABILITY
    )

    assert assessment.history_sufficient is False
    assert assessment.shared_domain_ids == []


def test_duplicate_domain_within_one_event_does_not_create_cohort():
    """
    Recurrence requires distinct Learning Events.

    Duplicate domain tags inside one event cannot manufacture history.
    """

    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=[
                    "engineering",
                    "engineering",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=["cognition"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus
        .INSUFFICIENT_COMPARABILITY
    )

    assert assessment.shared_domain_ids == []


def test_multi_domain_events_support_each_relevant_cohort():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=[
                    "engineering",
                    "cognition",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-3",
                domains=["cognition"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus.SUFFICIENT
    )

    assert assessment.shared_domain_ids == [
        "cognition",
        "engineering",
    ]


def test_empty_history_remains_no_history():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze([])

    assert assessment.status == (
        ReflectionHistoryStatus.NO_HISTORY
    )

    assert assessment.history_sufficient is False
    assert assessment.shared_domain_ids == []


def test_single_event_remains_insufficient_history():
    analyzer = ReflectionHistoryAnalyzer()

    assessment = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
        ]
    )

    assert assessment.status == (
        ReflectionHistoryStatus
        .INSUFFICIENT_HISTORY
    )

    assert assessment.history_sufficient is False
