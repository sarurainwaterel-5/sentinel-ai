"""
Contract tests for SentinelAI's Reflection History Analyzer.

History Analysis determines whether accumulated Learning Events provide
a sufficient comparable basis for reflective Pattern discovery.

It does not discover Patterns.
It does not generate Insights.
It does not generate Recommendations.
It does not modify Learning Events.
"""

from copy import deepcopy
from datetime import UTC, datetime, timedelta

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAnalyzer,
    ReflectionHistoryStatus,
)


def make_event(
    *,
    event_id: str,
    domains: list[str],
    evidence: list[str] | None = None,
    days_ago: int = 0,
) -> LearningEvent:
    """
    Construct one historical Learning Event.
    """

    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=domains,
        evidence_added=evidence or [],
        summary=f"Learning recorded for {event_id}.",
        learned_at=(
            datetime.now(UTC)
            - timedelta(days=days_ago)
        ),
    )


def test_no_learning_events_produce_no_history():
    """
    No Learning Events means there is no reflective history.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze([])

    assert result.status == ReflectionHistoryStatus.NO_HISTORY
    assert result.event_count == 0
    assert result.history_sufficient is False
    assert result.shared_domain_ids == []
    assert result.evidence_count == 0
    assert result.limitations


def test_single_event_is_insufficient_history():
    """
    One Learning Event cannot establish a historical comparison.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                evidence=["evidence-1"],
            ),
        ]
    )

    assert (
        result.status
        == ReflectionHistoryStatus.INSUFFICIENT_HISTORY
    )

    assert result.event_count == 1
    assert result.history_sufficient is False

    assert "engineering" in result.domain_ids
    assert result.shared_domain_ids == []


def test_unrelated_events_are_not_comparable_history():
    """
    Multiple events do not automatically constitute reflective history.

    Events without a shared domain do not provide a comparable basis
    for recurrence or stability analysis.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                evidence=["evidence-1"],
                days_ago=5,
            ),
            make_event(
                event_id="learning-2",
                domains=["trading"],
                evidence=["evidence-2"],
            ),
        ]
    )

    assert (
        result.status
        == ReflectionHistoryStatus.INSUFFICIENT_COMPARABILITY
    )

    assert result.event_count == 2
    assert result.history_sufficient is False
    assert result.shared_domain_ids == []
    assert result.limitations


def test_related_events_create_sufficient_reflective_history():
    """
    Multiple Learning Events sharing a domain provide a sufficient
    historical basis for Pattern discovery to begin.

    This does not mean that a Pattern exists.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=[
                    "engineering",
                    "reasoning",
                ],
                evidence=["evidence-1"],
                days_ago=10,
            ),
            make_event(
                event_id="learning-2",
                domains=[
                    "engineering",
                    "verification",
                ],
                evidence=["evidence-2"],
            ),
        ]
    )

    assert (
        result.status
        == ReflectionHistoryStatus.SUFFICIENT
    )

    assert result.history_sufficient is True

    assert result.shared_domain_ids == [
        "engineering",
    ]

    assert set(result.domain_ids) == {
        "engineering",
        "reasoning",
        "verification",
    }


def test_history_analysis_reports_evidence_coverage():
    """
    History Analysis reports evidence availability without deciding
    what the evidence means.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                evidence=[
                    "evidence-1",
                    "evidence-2",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
                evidence=[
                    "evidence-2",
                    "evidence-3",
                ],
            ),
        ]
    )

    assert result.evidence_count == 3

    assert set(result.evidence_ids) == {
        "evidence-1",
        "evidence-2",
        "evidence-3",
    }

    assert result.events_with_evidence == 2
    assert result.evidence_coverage == 1.0


def test_history_analysis_reports_partial_evidence_coverage():
    """
    Missing evidence is exposed as a limitation rather than hidden.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                evidence=["evidence-1"],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
                evidence=[],
            ),
        ]
    )

    assert result.events_with_evidence == 1
    assert result.evidence_coverage == 0.5
    assert result.limitations


def test_history_analysis_reports_temporal_span():
    """
    Reflection history preserves its temporal dimension.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                days_ago=12,
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
                days_ago=2,
            ),
        ]
    )

    assert result.earliest_event_at is not None
    assert result.latest_event_at is not None

    assert (
        result.latest_event_at
        >= result.earliest_event_at
    )

    assert result.temporal_span_seconds > 0


def test_history_analysis_does_not_modify_learning_events():
    """
    Reflection examines history.

    It never edits the past.
    """

    events = [
        make_event(
            event_id="learning-1",
            domains=["engineering"],
            evidence=["evidence-1"],
        ),
        make_event(
            event_id="learning-2",
            domains=["engineering"],
            evidence=["evidence-2"],
        ),
    ]

    original = deepcopy(events)

    analyzer = ReflectionHistoryAnalyzer()

    analyzer.analyze(events)

    assert events == original


def test_history_analysis_does_not_claim_patterns():
    """
    History Analysis decides whether Pattern discovery is warranted.

    Pattern discovery remains another authority.
    """

    analyzer = ReflectionHistoryAnalyzer()

    result = analyzer.analyze(
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

    assert not hasattr(result, "patterns")
    assert not hasattr(result, "insights")
    assert not hasattr(result, "recommendations")
