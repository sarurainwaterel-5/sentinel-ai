"""
Reflective Trend Synthesis for SentinelAI.

This component converts already-assessed longitudinal Understanding
history into bounded higher-order reflective trends.

It may identify:

- continuity,
- reinforcement,
- revision,
- erosion,
- contradiction,
- mixed supported trends,
- unresolved history.

It may not:

- infer correctness,
- infer improvement or regression,
- invent causes,
- reinterpret conflicted transitions,
- rewrite historical cognition,
- generate Recommendations,
- execute actions.

Synthesis compresses supported history.

It does not manufacture meaning beyond the evidence.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.services.cognition.reflection.longitudinal_understanding_analyzer import (
    LongitudinalLineageStatus,
    LongitudinalUnderstandingAnalysis,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionKind,
)


class ReflectiveTrendKind(StrEnum):
    """
    Canonical higher-order trends derived from supported longitudinal
    evolution.
    """

    CONTINUITY = "continuity"
    REINFORCEMENT = "reinforcement"
    REVISION = "revision"
    EROSION = "erosion"
    CONTRADICTION = "contradiction"
    MIXED = "mixed"
    UNRESOLVED = "unresolved"


class ReflectiveTrendSynthesis(BaseModel):
    """
    Bounded synthesis of one longitudinal Understanding history.
    """

    primary_trend: ReflectiveTrendKind

    trends: list[ReflectiveTrendKind] = Field(
        default_factory=list,
    )

    supporting_transition_count: int = Field(
        default=0,
        ge=0,
    )

    conflicted_transition_count: int = Field(
        default=0,
        ge=0,
    )

    has_conflict: bool = False

    limitations: list[str] = Field(
        default_factory=list,
    )


class ReflectiveTrendSynthesizer:
    """
    Synthesize supported longitudinal evolution into bounded trends.

    Unsupported or conflicted transitions are never promoted into
    authoritative reflective trends.
    """

    @staticmethod
    def _trend_for_observed_kind(
        observed_kind: UnderstandingEvolutionKind,
    ) -> ReflectiveTrendKind | None:
        mapping = {
            UnderstandingEvolutionKind.STABLE: (
                ReflectiveTrendKind.CONTINUITY
            ),
            UnderstandingEvolutionKind.STRENGTHENED: (
                ReflectiveTrendKind.REINFORCEMENT
            ),
            UnderstandingEvolutionKind.REVISED: (
                ReflectiveTrendKind.REVISION
            ),
            UnderstandingEvolutionKind.WEAKENED: (
                ReflectiveTrendKind.EROSION
            ),
            UnderstandingEvolutionKind.CONTRADICTED: (
                ReflectiveTrendKind.CONTRADICTION
            ),
        }

        return mapping.get(
            observed_kind
        )

    @staticmethod
    def _unique_preserving_order(
        values: list[ReflectiveTrendKind],
    ) -> list[ReflectiveTrendKind]:
        return list(
            dict.fromkeys(
                values
            )
        )

    def synthesize(
        self,
        *,
        analysis: LongitudinalUnderstandingAnalysis,
    ) -> ReflectiveTrendSynthesis:
        """
        Produce one bounded reflective trend synthesis.
        """

        limitations = list(
            analysis.limitations
        )

        if (
            analysis.status
            == LongitudinalLineageStatus.EMPTY
        ):
            limitations.append(
                "No longitudinal Understanding history "
                "was available for trend synthesis."
            )

            return ReflectiveTrendSynthesis(
                primary_trend=(
                    ReflectiveTrendKind.UNRESOLVED
                ),
                trends=[],
                limitations=list(
                    dict.fromkeys(
                        limitations
                    )
                ),
            )

        if (
            analysis.status
            == LongitudinalLineageStatus.AMBIGUOUS
        ):
            limitations.append(
                "The Understanding lineage is ambiguous "
                "and cannot support one authoritative trend."
            )

            return ReflectiveTrendSynthesis(
                primary_trend=(
                    ReflectiveTrendKind.UNRESOLVED
                ),
                trends=[],
                supporting_transition_count=(
                    analysis.supported_transition_count
                ),
                conflicted_transition_count=(
                    analysis.conflicted_transition_count
                ),
                has_conflict=(
                    analysis.conflicted_transition_count
                    > 0
                ),
                limitations=list(
                    dict.fromkeys(
                        limitations
                    )
                ),
            )

        if (
            analysis.status
            == LongitudinalLineageStatus.STABLE_SINGLE_STATE
        ):
            return ReflectiveTrendSynthesis(
                primary_trend=(
                    ReflectiveTrendKind.CONTINUITY
                ),
                trends=[
                    ReflectiveTrendKind.CONTINUITY,
                ],
                supporting_transition_count=0,
                conflicted_transition_count=0,
                has_conflict=False,
                limitations=limitations,
            )

        supported_trends: list[
            ReflectiveTrendKind
        ] = []

        for assessment in (
            analysis.transition_assessments
        ):
            if not assessment.supported:
                continue

            trend = self._trend_for_observed_kind(
                assessment.observed_kind
            )

            if trend is not None:
                supported_trends.append(
                    trend
                )

        supported_trends = (
            self._unique_preserving_order(
                supported_trends
            )
        )

        has_conflict = (
            analysis.conflicted_transition_count
            > 0
        )

        if has_conflict:
            limitations.append(
                "One or more longitudinal transitions "
                "remain conflicted and were excluded from "
                "authoritative trend synthesis."
            )

        if not supported_trends:
            limitations.append(
                "No supported longitudinal transition "
                "was available for authoritative trend synthesis."
            )

            return ReflectiveTrendSynthesis(
                primary_trend=(
                    ReflectiveTrendKind.UNRESOLVED
                ),
                trends=[],
                supporting_transition_count=(
                    analysis.supported_transition_count
                ),
                conflicted_transition_count=(
                    analysis.conflicted_transition_count
                ),
                has_conflict=has_conflict,
                limitations=list(
                    dict.fromkeys(
                        limitations
                    )
                ),
            )

        if len(supported_trends) == 1:
            primary_trend = (
                supported_trends[0]
            )
        else:
            primary_trend = (
                ReflectiveTrendKind.MIXED
            )

        return ReflectiveTrendSynthesis(
            primary_trend=primary_trend,
            trends=supported_trends,
            supporting_transition_count=(
                analysis.supported_transition_count
            ),
            conflicted_transition_count=(
                analysis.conflicted_transition_count
            ),
            has_conflict=has_conflict,
            limitations=list(
                dict.fromkeys(
                    limitations
                )
            ),
        )
