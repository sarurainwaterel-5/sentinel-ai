"""
Deterministic Pattern Discovery for SentinelAI Reflection.

Pattern Discovery identifies recurring structures across Learning Events.

It does not:

- determine whether history is sufficient,
- generate Insights,
- generate Recommendations,
- interpret Pattern meaning,
- modify Learning Events.

Current deterministic scope:

- recurring domains,
- recurring evidence references within supporting events.

Semantic Pattern discovery may be added later through a separate,
explicitly governed responsibility.
"""

from __future__ import annotations

from collections import defaultdict
from hashlib import sha256

from app.core.cognition.models import LearningEvent

from app.services.cognition.reflection.models import (
    ReflectionPattern,
    ReflectionPatternKind,
)


class ReflectionPatternDiscoverer:
    """
    Discover deterministic historical recurrence across Learning Events.
    """

    @staticmethod
    def _pattern_id(
        *,
        domain_id: str,
        learning_event_ids: list[str],
    ) -> str:
        """
        Produce a stable identity for one recurring historical structure.

        Identical supporting history produces the same Pattern ID.
        """

        canonical = "|".join(
            [
                "recurrence",
                domain_id,
                *sorted(learning_event_ids),
            ]
        )

        digest = sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:16]

        return f"pattern-recurrence-{digest}"

    @staticmethod
    def _recurring_evidence(
        events: list[LearningEvent],
    ) -> list[str]:
        """
        Return evidence IDs present in every supporting Learning Event.
        """

        if not events:
            return []

        shared = set(
            events[0].evidence_added
        )

        for event in events[1:]:
            shared &= set(
                event.evidence_added
            )

        return sorted(shared)

    def discover(
        self,
        learning_events: list[LearningEvent],
    ) -> list[ReflectionPattern]:
        """
        Discover recurring domains across accumulated Learning Events.

        A domain becomes a recurrence Pattern only when it appears in at
        least two distinct Learning Events.
        """

        if len(learning_events) < 2:
            return []

        events_by_domain: dict[
            str,
            list[LearningEvent],
        ] = defaultdict(list)

        for event in learning_events:
            for domain_id in set(
                event.domain_ids
            ):
                events_by_domain[
                    domain_id
                ].append(event)

        patterns: list[
            ReflectionPattern
        ] = []

        for domain_id in sorted(
            events_by_domain
        ):
            supporting_events = (
                events_by_domain[
                    domain_id
                ]
            )

            unique_events = {
                event.learning_event_id: event
                for event in supporting_events
            }

            if len(unique_events) < 2:
                continue

            ordered_events = [
                unique_events[event_id]
                for event_id in sorted(
                    unique_events
                )
            ]

            learning_event_ids = [
                event.learning_event_id
                for event in ordered_events
            ]

            evidence_ids = (
                self._recurring_evidence(
                    ordered_events
                )
            )

            patterns.append(
                ReflectionPattern(
                    pattern_id=self._pattern_id(
                        domain_id=domain_id,
                        learning_event_ids=(
                            learning_event_ids
                        ),
                    ),
                    kind=(
                        ReflectionPatternKind.RECURRENCE
                    ),
                    title=(
                        f"Recurring domain: {domain_id}"
                    ),
                    description=(
                        "The domain "
                        f"'{domain_id}' appears across "
                        f"{len(learning_event_ids)} "
                        "Learning Events."
                    ),
                    learning_event_ids=(
                        learning_event_ids
                    ),
                    evidence_ids=(
                        evidence_ids
                    ),
                    domain_ids=[
                        domain_id,
                    ],
                    metadata={
                        "supporting_event_count": (
                            len(
                                learning_event_ids
                            )
                        ),
                        "discovery_method": (
                            "deterministic_domain_recurrence"
                        ),
                    },
                )
            )

        return patterns
