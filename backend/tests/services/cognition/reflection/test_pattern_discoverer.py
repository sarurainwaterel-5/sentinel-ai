"""
Contract tests for SentinelAI's Reflection Pattern Discoverer.

Pattern Discovery identifies recurring structures across accumulated
Learning Events.

It does not:

- determine whether history is sufficient,
- generate Insights,
- generate Recommendations,
- interpret the meaning of a Pattern,
- modify Learning Events,
- manufacture recurrence from isolated evidence.
"""

from copy import deepcopy

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.models import (
    ReflectionPatternKind,
)

from app.services.cognition.reflection.pattern_discoverer import (
    ReflectionPatternDiscoverer,
)


def make_event(
    *,
    event_id: str,
    domains: list[str],
    evidence: list[str] | None = None,
) -> LearningEvent:
    """
    Construct one deterministic Learning Event.
    """

    return LearningEvent(
        learning_event_id=event_id,
        source=f"source-{event_id}",
        domain_ids=domains,
        evidence_added=evidence or [],
        summary=f"Learning recorded for {event_id}.",
    )


def test_shared_domain_produces_recurrence_pattern():
    """
    A domain recurring across multiple Learning Events may be
    represented as a historical recurrence Pattern.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=[
                    "engineering",
                    "reasoning",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=[
                    "engineering",
                    "verification",
                ],
            ),
        ]
    )

    assert len(patterns) == 1

    pattern = patterns[0]

    assert (
        pattern.kind
        == ReflectionPatternKind.RECURRENCE
    )

    assert pattern.learning_event_ids == [
        "learning-1",
        "learning-2",
    ]

    assert pattern.domain_ids == [
        "engineering",
    ]


def test_nonrecurring_domains_do_not_produce_pattern():
    """
    Presence is not recurrence.

    A domain appearing in only one Learning Event cannot become a
    historical Pattern.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["trading"],
            ),
        ]
    )

    assert patterns == []


def test_single_event_cannot_produce_pattern():
    """
    One isolated Learning Event cannot establish recurrence.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
        ]
    )

    assert patterns == []


def test_pattern_references_only_supporting_events():
    """
    Pattern provenance contains only Learning Events that actually
    support the discovered recurrence.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
            ),
            make_event(
                event_id="learning-2",
                domains=["trading"],
            ),
            make_event(
                event_id="learning-3",
                domains=["engineering"],
            ),
        ]
    )

    assert len(patterns) == 1

    assert patterns[0].learning_event_ids == [
        "learning-1",
        "learning-3",
    ]


def test_multiple_recurring_domains_produce_distinct_patterns():
    """
    Independent recurring structures remain independent Patterns.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=[
                    "engineering",
                    "reasoning",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=[
                    "engineering",
                    "reasoning",
                ],
            ),
        ]
    )

    assert len(patterns) == 2

    discovered_domains = {
        pattern.domain_ids[0]
        for pattern in patterns
    }

    assert discovered_domains == {
        "engineering",
        "reasoning",
    }


def test_recurring_evidence_is_preserved_in_pattern_provenance():
    """
    Evidence recurring across supporting Learning Events is preserved
    as Pattern provenance.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
            make_event(
                event_id="learning-1",
                domains=["engineering"],
                evidence=[
                    "evidence-shared",
                    "evidence-1",
                ],
            ),
            make_event(
                event_id="learning-2",
                domains=["engineering"],
                evidence=[
                    "evidence-shared",
                    "evidence-2",
                ],
            ),
        ]
    )

    assert len(patterns) == 1

    assert patterns[0].evidence_ids == [
        "evidence-shared",
    ]


def test_nonrecurring_evidence_is_not_claimed_as_pattern_support():
    """
    Evidence that does not recur across supporting events must not be
    represented as recurring Pattern evidence.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
        [
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
    )

    assert len(patterns) == 1
    assert patterns[0].evidence_ids == []


def test_pattern_ids_are_deterministic():
    """
    Identical historical input must produce identical Pattern IDs.

    Reflection provenance should not change merely because the same
    history was examined again.
    """

    events = [
        make_event(
            event_id="learning-1",
            domains=["engineering"],
        ),
        make_event(
            event_id="learning-2",
            domains=["engineering"],
        ),
    ]

    discoverer = ReflectionPatternDiscoverer()

    first = discoverer.discover(events)
    second = discoverer.discover(events)

    assert first[0].pattern_id == second[0].pattern_id


def test_pattern_discovery_is_order_independent():
    """
    Reordering the same Learning Events must not change the discovered
    historical structure.
    """

    event_1 = make_event(
        event_id="learning-1",
        domains=["engineering"],
    )

    event_2 = make_event(
        event_id="learning-2",
        domains=["engineering"],
    )

    discoverer = ReflectionPatternDiscoverer()

    forward = discoverer.discover(
        [
            event_1,
            event_2,
        ]
    )

    reverse = discoverer.discover(
        [
            event_2,
            event_1,
        ]
    )

    assert forward == reverse


def test_pattern_discovery_does_not_modify_learning_events():
    """
    Reflection never edits the past.
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
            evidence=["evidence-1"],
        ),
    ]

    original = deepcopy(events)

    discoverer = ReflectionPatternDiscoverer()

    discoverer.discover(events)

    assert events == original


def test_pattern_discoverer_has_no_interpretive_output():
    """
    Pattern Discovery reports historical structure.

    Interpretation belongs to Insight generation.
    """

    discoverer = ReflectionPatternDiscoverer()

    patterns = discoverer.discover(
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

    pattern = patterns[0]

    assert not hasattr(
        pattern,
        "insight",
    )

    assert not hasattr(
        pattern,
        "recommendation",
    )

    assert not hasattr(
        pattern,
        "action",
    )
