"""
Understanding Evolution Analysis for SentinelAI Reflection.

This analyzer examines authoritative Understanding states across
Learning Events.

It may identify:

- stability,
- strengthening,
- weakening,
- revision,
- contradiction,
- unresolved evolution.

It may not:

- infer change from chronology alone,
- invent missing Understanding records,
- manufacture evidence relationships,
- perform Reflection,
- generate Recommendations,
- modify historical cognition.

Change must be observed before change may be characterized.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.core.cognition.models import (
    LearningEvent,
    Understanding,
)


class UnderstandingEvolutionKind(StrEnum):
    """
    Canonical longitudinal states for Understanding evolution.
    """

    STABLE = "stable"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    REVISED = "revised"
    CONTRADICTED = "contradicted"
    UNRESOLVED = "unresolved"


class UnderstandingEvolution(BaseModel):
    """
    One bounded comparison between Understanding states.
    """

    kind: UnderstandingEvolutionKind

    earlier_understanding_id: str
    later_understanding_id: str

    confidence_delta: float | None = None

    evidence_added: list[str] = Field(
        default_factory=list,
    )

    evidence_removed: list[str] = Field(
        default_factory=list,
    )

    explanation_changed: bool = False

    basis: str = Field(
        min_length=1,
    )


class UnderstandingEvolutionAnalysis(BaseModel):
    """
    Longitudinal analysis of Understanding history.
    """

    evolutions: list[UnderstandingEvolution] = Field(
        default_factory=list,
    )

    missing_understanding_ids: list[str] = Field(
        default_factory=list,
    )

    limitations: list[str] = Field(
        default_factory=list,
    )


class UnderstandingEvolutionAnalyzer:
    """
    Compare authoritative Understanding states conservatively.

    Semantic contradiction is never inferred from text alone.
    """

    @staticmethod
    def _confidence_delta(
        earlier: Understanding,
        later: Understanding,
    ) -> float | None:
        if (
            earlier.confidence is None
            or later.confidence is None
        ):
            return None

        return round(
            later.confidence
            - earlier.confidence,
            4,
        )

    @staticmethod
    def _evidence_added(
        earlier: Understanding,
        later: Understanding,
    ) -> list[str]:
        return [
            evidence_id
            for evidence_id in later.evidence_ids
            if evidence_id
            not in earlier.evidence_ids
        ]

    @staticmethod
    def _evidence_removed(
        earlier: Understanding,
        later: Understanding,
    ) -> list[str]:
        return [
            evidence_id
            for evidence_id in earlier.evidence_ids
            if evidence_id
            not in later.evidence_ids
        ]

    def compare(
        self,
        *,
        earlier: Understanding,
        later: Understanding,
        contradicted_understanding_ids: list[str] | None = None,
    ) -> UnderstandingEvolution:
        """
        Compare two authoritative Understanding states.

        Classification is conservative and structural.
        """

        contradicted_understanding_ids = (
            contradicted_understanding_ids
            or []
        )

        confidence_delta = (
            self._confidence_delta(
                earlier,
                later,
            )
        )

        evidence_added = (
            self._evidence_added(
                earlier,
                later,
            )
        )

        evidence_removed = (
            self._evidence_removed(
                earlier,
                later,
            )
        )

        explanation_changed = (
            earlier.explanation
            != later.explanation
        )

        if (
            earlier.understanding_id
            in contradicted_understanding_ids
        ):
            kind = (
                UnderstandingEvolutionKind
                .CONTRADICTED
            )

            basis = (
                "The later Understanding explicitly identifies "
                "the earlier Understanding as contradicted."
            )

        elif explanation_changed:
            kind = (
                UnderstandingEvolutionKind.REVISED
            )

            basis = (
                "The authoritative explanation changed between "
                "Understanding states."
            )

        elif confidence_delta is None:
            kind = (
                UnderstandingEvolutionKind.UNRESOLVED
            )

            basis = (
                "Confidence was unavailable for one or both "
                "Understanding states, preventing a supported "
                "strengthening or weakening judgment."
            )

        elif (
            confidence_delta > 0
            and (
                evidence_added
                or not evidence_removed
            )
        ):
            kind = (
                UnderstandingEvolutionKind
                .STRENGTHENED
            )

            basis = (
                "The Understanding retained its meaning while "
                "confidence increased with equal or expanded "
                "evidentiary support."
            )

        elif (
            confidence_delta < 0
            or evidence_removed
        ):
            kind = (
                UnderstandingEvolutionKind
                .WEAKENED
            )

            basis = (
                "The Understanding retained its meaning while "
                "confidence decreased or evidentiary support "
                "contracted."
            )

        else:
            kind = (
                UnderstandingEvolutionKind.STABLE
            )

            basis = (
                "The Understanding retained its meaning without "
                "a supported strengthening, weakening, revision, "
                "or contradiction."
            )

        return UnderstandingEvolution(
            kind=kind,
            earlier_understanding_id=(
                earlier.understanding_id
            ),
            later_understanding_id=(
                later.understanding_id
            ),
            confidence_delta=confidence_delta,
            evidence_added=evidence_added,
            evidence_removed=evidence_removed,
            explanation_changed=(
                explanation_changed
            ),
            basis=basis,
        )

    @staticmethod
    def _ordered_events(
        learning_events: list[LearningEvent],
    ) -> list[LearningEvent]:
        """
        Return stable chronological Learning Event order.
        """

        return sorted(
            learning_events,
            key=lambda event: event.learned_at,
        )

    def analyze(
        self,
        *,
        learning_events: list[LearningEvent],
        understandings: dict[
            str,
            Understanding,
        ],
    ) -> UnderstandingEvolutionAnalysis:
        """
        Examine Understanding continuity across Learning Events.
        """

        missing_ids: list[str] = []

        for event in learning_events:
            for understanding_id in (
                event.understandings_added
            ):
                if (
                    understanding_id
                    not in understandings
                    and understanding_id
                    not in missing_ids
                ):
                    missing_ids.append(
                        understanding_id
                    )

        ordered_events = (
            self._ordered_events(
                learning_events
            )
        )

        occurrences: dict[
            str,
            list[str],
        ] = {}

        for event in ordered_events:
            for understanding_id in (
                event.understandings_added
            ):
                if understanding_id in understandings:
                    occurrences.setdefault(
                        understanding_id,
                        [],
                    ).append(
                        event.learning_event_id
                    )

        evolutions: list[
            UnderstandingEvolution
        ] = []

        # Repeated reference to the same authoritative Understanding
        # constitutes stable continuity.
        for understanding_id, event_ids in (
            occurrences.items()
        ):
            if len(event_ids) < 2:
                continue

            understanding = (
                understandings[
                    understanding_id
                ]
            )

            evolutions.append(
                self.compare(
                    earlier=understanding,
                    later=understanding,
                )
            )

        limitations: list[str] = []

        if missing_ids:
            limitations.append(
                "One or more Learning Events reference "
                "Understanding records that were unavailable "
                "for longitudinal analysis."
            )

        return UnderstandingEvolutionAnalysis(
            evolutions=evolutions,
            missing_understanding_ids=(
                missing_ids
            ),
            limitations=limitations,
        )
