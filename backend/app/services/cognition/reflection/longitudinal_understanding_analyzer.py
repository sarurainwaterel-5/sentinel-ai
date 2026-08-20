"""
Longitudinal Understanding Analysis for SentinelAI Reflection.

This analyzer summarizes an entire explicit Understanding lineage from
already-assessed transitions.

It may establish:

- lineage root,
- terminal/current state,
- ordered Understanding states,
- transition count,
- observed evolution sequence,
- supported transition count,
- conflicted transition count,
- overall lineage assessment.

It may not:

- infer motives,
- invent causal explanations,
- rewrite lineage,
- reinterpret edge assessments,
- perform Reflection,
- generate Recommendations,
- narrate improvement or regression.

The analyzer summarizes assessed history.

It does not manufacture a story.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field

from app.services.cognition.reflection.lineage_evolution_assessor import (
    LineageEvolutionAssessment,
    LineageEvolutionAssessor,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionKind,
)

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineage,
)


class LongitudinalLineageStatus(StrEnum):
    """
    Structural state of one assessed Understanding lineage.
    """

    EMPTY = "empty"
    STABLE_SINGLE_STATE = "stable_single_state"
    SUPPORTED = "supported"
    PARTIALLY_CONFLICTED = "partially_conflicted"
    CONFLICTED = "conflicted"
    AMBIGUOUS = "ambiguous"


class LongitudinalUnderstandingAnalysis(BaseModel):
    """
    Structural summary of one complete Understanding lineage.
    """

    root_understanding_id: str | None = None
    current_understanding_id: str | None = None

    ordered_understanding_ids: list[str] = Field(
        default_factory=list,
    )

    transition_count: int = Field(
        default=0,
        ge=0,
    )

    transition_assessments: list[
        LineageEvolutionAssessment
    ] = Field(
        default_factory=list,
    )

    observed_evolution_sequence: list[
        UnderstandingEvolutionKind
    ] = Field(
        default_factory=list,
    )

    supported_transition_count: int = Field(
        default=0,
        ge=0,
    )

    conflicted_transition_count: int = Field(
        default=0,
        ge=0,
    )

    status: LongitudinalLineageStatus

    limitations: list[str] = Field(
        default_factory=list,
    )


class LongitudinalUnderstandingAnalyzer:
    """
    Summarize a complete assessed Understanding lineage.

    The analyzer owns lifecycle structure only.
    """

    def __init__(
        self,
        *,
        lineage_assessor: LineageEvolutionAssessor,
    ) -> None:
        self.lineage_assessor = lineage_assessor

    @staticmethod
    def _roots(
        lineage: UnderstandingLineage,
    ) -> list[str]:
        """
        Return Understanding IDs with no declared predecessor.
        """

        later_ids = {
            edge.later_understanding_id
            for edge in lineage.edges
        }

        return [
            understanding_id
            for understanding_id
            in lineage.understandings
            if understanding_id not in later_ids
        ]

    @staticmethod
    def _terminals(
        lineage: UnderstandingLineage,
    ) -> list[str]:
        """
        Return Understanding IDs with no declared successor.
        """

        earlier_ids = {
            edge.earlier_understanding_id
            for edge in lineage.edges
        }

        return [
            understanding_id
            for understanding_id
            in lineage.understandings
            if understanding_id not in earlier_ids
        ]

    @staticmethod
    def _has_branching(
        lineage: UnderstandingLineage,
    ) -> bool:
        """
        Return True when any Understanding has multiple successors.
        """

        successor_counts: dict[str, int] = {}

        for edge in lineage.edges:
            predecessor = (
                edge.earlier_understanding_id
            )

            successor_counts[
                predecessor
            ] = (
                successor_counts.get(
                    predecessor,
                    0,
                )
                + 1
            )

        return any(
            count > 1
            for count in successor_counts.values()
        )

    def analyze(
        self,
        *,
        lineage: UnderstandingLineage,
    ) -> LongitudinalUnderstandingAnalysis:
        """
        Produce one structural summary of an assessed lineage.
        """

        if not lineage.understandings:
            return LongitudinalUnderstandingAnalysis(
                status=(
                    LongitudinalLineageStatus.EMPTY
                )
            )

        roots = self._roots(
            lineage
        )

        terminals = self._terminals(
            lineage
        )

        limitations: list[str] = []

        if (
            len(lineage.understandings) == 1
            and not lineage.edges
        ):
            only_id = next(
                iter(
                    lineage.understandings
                )
            )

            return LongitudinalUnderstandingAnalysis(
                root_understanding_id=only_id,
                current_understanding_id=only_id,
                ordered_understanding_ids=[
                    only_id,
                ],
                transition_count=0,
                status=(
                    LongitudinalLineageStatus
                    .STABLE_SINGLE_STATE
                ),
            )

        if (
            len(roots) != 1
            or len(terminals) != 1
            or self._has_branching(
                lineage
            )
        ):
            if len(roots) != 1:
                limitations.append(
                    "The lineage does not contain exactly "
                    "one unambiguous root Understanding."
                )

            if len(terminals) != 1:
                limitations.append(
                    "The lineage does not contain exactly "
                    "one unambiguous terminal Understanding."
                )

            if self._has_branching(
                lineage
            ):
                limitations.append(
                    "The lineage branches and cannot be "
                    "represented as one unambiguous lifecycle."
                )

            return LongitudinalUnderstandingAnalysis(
                transition_count=len(
                    lineage.edges
                ),
                status=(
                    LongitudinalLineageStatus.AMBIGUOUS
                ),
                limitations=limitations,
            )

        root_id = roots[0]
        current_id = terminals[0]

        ordered_ids = lineage.chain_from(
            root_id
        )

        assessment_result = (
            self.lineage_assessor.assess(
                lineage=lineage
            )
        )

        assessments = (
            assessment_result.assessments
        )

        supported_count = sum(
            1
            for assessment in assessments
            if assessment.supported
        )

        conflicted_count = sum(
            1
            for assessment in assessments
            if assessment.conflict
        )

        if conflicted_count == 0:
            status = (
                LongitudinalLineageStatus
                .SUPPORTED
            )

        elif supported_count == 0:
            status = (
                LongitudinalLineageStatus
                .CONFLICTED
            )

        else:
            status = (
                LongitudinalLineageStatus
                .PARTIALLY_CONFLICTED
            )

        return LongitudinalUnderstandingAnalysis(
            root_understanding_id=root_id,
            current_understanding_id=current_id,
            ordered_understanding_ids=(
                ordered_ids
            ),
            transition_count=len(
                assessments
            ),
            transition_assessments=(
                assessments
            ),
            observed_evolution_sequence=[
                assessment.observed_kind
                for assessment in assessments
            ],
            supported_transition_count=(
                supported_count
            ),
            conflicted_transition_count=(
                conflicted_count
            ),
            status=status,
            limitations=limitations,
        )
