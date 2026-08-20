"""
Temporal Learning Analysis for SentinelAI Reflection.

Temporal Learning Analysis examines the chronology of authoritative
Learning Events.

It may establish:

- chronological order,
- earliest and latest learning,
- temporal span,
- recurring domains across time,
- gaps between consecutive Learning Events.

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

from __future__ import annotations

from collections import defaultdict
from datetime import datetime

from pydantic import BaseModel, Field

from app.core.cognition.models import (
    LearningEvent,
)


class TemporalLearningGap(BaseModel):
    """
    One chronological gap between consecutive Learning Events.
    """

    earlier_learning_event_id: str
    later_learning_event_id: str

    gap_seconds: float = Field(
        ge=0.0,
    )


class TemporalLearningAnalysis(BaseModel):
    """
    Deterministic chronology of examined Learning Events.
    """

    event_count: int = Field(
        ge=0,
    )

    ordered_learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    earliest_learning_event_id: str | None = None
    latest_learning_event_id: str | None = None

    started_at: datetime | None = None
    ended_at: datetime | None = None

    span_seconds: float = Field(
        default=0.0,
        ge=0.0,
    )

    recurring_domain_ids: list[str] = Field(
        default_factory=list,
    )

    gaps: list[TemporalLearningGap] = Field(
        default_factory=list,
    )


class TemporalLearningAnalyzer:
    """
    Analyze chronology without interpreting cognitive meaning.
    """

    @staticmethod
    def _ordered_events(
        learning_events: list[LearningEvent],
    ) -> list[LearningEvent]:
        """
        Return Learning Events in stable chronological order.

        Python's sort is stable, so equal timestamps preserve the
        caller-provided order.
        """

        return sorted(
            learning_events,
            key=lambda event: event.learned_at,
        )

    @staticmethod
    def _recurring_domains(
        learning_events: list[LearningEvent],
    ) -> list[str]:
        """
        Return domains represented across at least two distinct events.
        """

        domain_event_ids: dict[
            str,
            set[str],
        ] = defaultdict(set)

        for event in learning_events:
            for domain_id in set(
                event.domain_ids
            ):
                domain_event_ids[
                    domain_id
                ].add(
                    event.learning_event_id
                )

        return sorted(
            domain_id
            for domain_id, event_ids
            in domain_event_ids.items()
            if len(event_ids) >= 2
        )

    @staticmethod
    def _gaps(
        ordered_events: list[LearningEvent],
    ) -> list[TemporalLearningGap]:
        """
        Describe chronological gaps between consecutive events.
        """

        gaps: list[
            TemporalLearningGap
        ] = []

        for earlier, later in zip(
            ordered_events,
            ordered_events[1:],
        ):
            gap_seconds = (
                later.learned_at
                - earlier.learned_at
            ).total_seconds()

            gaps.append(
                TemporalLearningGap(
                    earlier_learning_event_id=(
                        earlier.learning_event_id
                    ),
                    later_learning_event_id=(
                        later.learning_event_id
                    ),
                    gap_seconds=max(
                        0.0,
                        gap_seconds,
                    ),
                )
            )

        return gaps

    def analyze(
        self,
        learning_events: list[LearningEvent],
    ) -> TemporalLearningAnalysis:
        """
        Produce one deterministic temporal analysis.
        """

        if not learning_events:
            return TemporalLearningAnalysis(
                event_count=0,
            )

        ordered_events = (
            self._ordered_events(
                learning_events
            )
        )

        earliest = ordered_events[0]
        latest = ordered_events[-1]

        span_seconds = (
            latest.learned_at
            - earliest.learned_at
        ).total_seconds()

        return TemporalLearningAnalysis(
            event_count=len(
                learning_events
            ),
            ordered_learning_event_ids=[
                event.learning_event_id
                for event in ordered_events
            ],
            earliest_learning_event_id=(
                earliest.learning_event_id
            ),
            latest_learning_event_id=(
                latest.learning_event_id
            ),
            started_at=earliest.learned_at,
            ended_at=latest.learned_at,
            span_seconds=max(
                0.0,
                span_seconds,
            ),
            recurring_domain_ids=(
                self._recurring_domains(
                    ordered_events
                )
            ),
            gaps=self._gaps(
                ordered_events
            ),
        )
