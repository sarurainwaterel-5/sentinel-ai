"""
Reflection History Analyzer

History Analysis determines whether accumulated Learning Events provide
a sufficient comparable basis for reflective Pattern discovery.

It does not discover Patterns.

It does not generate Insights.

It does not generate Recommendations.

It does not modify Learning Events.

History Analysis answers:

"Is there enough comparable cognitive history to responsibly begin
Pattern discovery?"
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.cognition.models import LearningEvent


class ReflectionHistoryStatus(StrEnum):
    """
    Status of the historical basis available to Reflection.
    """

    NO_HISTORY = "no_history"

    INSUFFICIENT_HISTORY = "insufficient_history"

    INSUFFICIENT_COMPARABILITY = (
        "insufficient_comparability"
    )

    SUFFICIENT = "sufficient"


class ReflectionHistoryAssessment(BaseModel):
    """
    Deterministic assessment of accumulated Learning Events.

    This object describes the available reflective history.

    It makes no claim that a Pattern exists.
    """

    status: ReflectionHistoryStatus

    event_count: int = Field(
        ge=0,
    )

    history_sufficient: bool

    learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    domain_ids: list[str] = Field(
        default_factory=list,
    )

    shared_domain_ids: list[str] = Field(
        default_factory=list,
    )

    evidence_ids: list[str] = Field(
        default_factory=list,
    )

    evidence_count: int = Field(
        ge=0,
    )

    events_with_evidence: int = Field(
        ge=0,
    )

    evidence_coverage: float = Field(
        ge=0.0,
        le=1.0,
    )

    earliest_event_at: object | None = None

    latest_event_at: object | None = None

    temporal_span_seconds: float = Field(
        default=0.0,
        ge=0.0,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )


class ReflectionHistoryAnalyzer:
    """
    Analyze whether Learning Events form comparable reflective history.

    Current deterministic comparability rule:

    Multiple Learning Events must share at least one domain.

    This establishes only that Pattern discovery is warranted.

    It does not establish that a Pattern exists.
    """

    def analyze(
        self,
        learning_events: list[LearningEvent],
    ) -> ReflectionHistoryAssessment:
        """
        Assess the historical basis available to Reflection.
        """

        event_count = len(learning_events)

        learning_event_ids = [
            event.learning_event_id
            for event in learning_events
        ]

        domain_ids = sorted(
            {
                domain_id
                for event in learning_events
                for domain_id in event.domain_ids
            }
        )

        shared_domain_ids = (
            self._shared_domains(
                learning_events
            )
        )

        evidence_ids = sorted(
            {
                evidence_id
                for event in learning_events
                for evidence_id in event.evidence_added
            }
        )

        events_with_evidence = sum(
            1
            for event in learning_events
            if event.evidence_added
        )

        evidence_coverage = (
            events_with_evidence / event_count
            if event_count
            else 0.0
        )

        (
            earliest_event_at,
            latest_event_at,
            temporal_span_seconds,
        ) = self._temporal_context(
            learning_events
        )

        limitations: list[str] = []

        if event_count == 0:
            status = (
                ReflectionHistoryStatus.NO_HISTORY
            )

            history_sufficient = False

            limitations.append(
                "No Learning Events were available "
                "for Reflection."
            )

        elif event_count == 1:
            status = (
                ReflectionHistoryStatus
                .INSUFFICIENT_HISTORY
            )

            history_sufficient = False

            limitations.append(
                "Reflection requires multiple Learning "
                "Events for historical comparison."
            )

        elif not shared_domain_ids:
            status = (
                ReflectionHistoryStatus
                .INSUFFICIENT_COMPARABILITY
            )

            history_sufficient = False

            limitations.append(
                "The available Learning Events do not "
                "share a comparable domain."
            )

        else:
            status = (
                ReflectionHistoryStatus.SUFFICIENT
            )

            history_sufficient = True

        if (
            event_count > 0
            and events_with_evidence < event_count
        ):
            limitations.append(
                "One or more Learning Events contain "
                "no recorded evidence."
            )

        return ReflectionHistoryAssessment(
            status=status,
            event_count=event_count,
            history_sufficient=(
                history_sufficient
            ),
            learning_event_ids=(
                learning_event_ids
            ),
            domain_ids=domain_ids,
            shared_domain_ids=(
                shared_domain_ids
            ),
            evidence_ids=evidence_ids,
            evidence_count=len(
                evidence_ids
            ),
            events_with_evidence=(
                events_with_evidence
            ),
            evidence_coverage=(
                evidence_coverage
            ),
            earliest_event_at=(
                earliest_event_at
            ),
            latest_event_at=(
                latest_event_at
            ),
            temporal_span_seconds=(
                temporal_span_seconds
            ),
            limitations=limitations,
        )

    @staticmethod
    def _shared_domains(
        learning_events: list[LearningEvent],
    ) -> list[str]:
        """
        Return domains represented across at least two distinct
        Learning Events.

        A comparable historical cohort exists when a domain recurs
        across multiple events.

        Unrelated Learning Events do not invalidate an existing
        comparable cohort.
        """

        if not learning_events:
            return []

        domain_event_ids: dict[
            str,
            set[str],
        ] = {}

        for event in learning_events:
            for domain_id in set(
                event.domain_ids
            ):
                domain_event_ids.setdefault(
                    domain_id,
                    set(),
                ).add(
                    event.learning_event_id
                )

        return sorted(
            domain_id
            for domain_id, event_ids
            in domain_event_ids.items()
            if len(event_ids) >= 2
        )

    @staticmethod
    def _temporal_context(
        learning_events: list[LearningEvent],
    ) -> tuple[
        object | None,
        object | None,
        float,
    ]:
        """
        Describe the temporal span of the examined history.
        """

        if not learning_events:
            return None, None, 0.0

        timestamps = [
            event.learned_at
            for event in learning_events
        ]

        earliest = min(timestamps)
        latest = max(timestamps)

        span = (
            latest - earliest
        ).total_seconds()

        return (
            earliest,
            latest,
            max(
                0.0,
                span,
            ),
        )
