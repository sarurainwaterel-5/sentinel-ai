"""
Lineage-Grounded Evolution Assessment for SentinelAI Reflection.

This component compares declared Understanding lineage against
observed evolution in authoritative Understanding states.

It does not:

- rewrite lineage,
- modify Understanding objects,
- repair historical cognition,
- perform Reflection,
- generate Recommendations,
- execute actions.

Declared history is inspected.

It is not blindly trusted.
"""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionAnalyzer,
    UnderstandingEvolutionKind,
)

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineage,
    UnderstandingLineageKind,
)


class LineageEvolutionAssessment(BaseModel):
    """
    One comparison between declared and observed evolution.
    """

    earlier_understanding_id: str
    later_understanding_id: str

    declared_kind: UnderstandingLineageKind
    observed_kind: UnderstandingEvolutionKind

    supported: bool
    conflict: bool

    basis: str = Field(
        min_length=1,
    )


class LineageEvolutionAssessmentResult(BaseModel):
    """
    Complete assessment of one Understanding lineage.
    """

    assessments: list[
        LineageEvolutionAssessment
    ] = Field(
        default_factory=list,
    )

    conflict_count: int = Field(
        default=0,
        ge=0,
    )


class LineageEvolutionAssessor:
    """
    Compare declared lineage against observed cognitive evolution.

    The assessor has comparison authority only.
    """

    def __init__(
        self,
        *,
        evolution_analyzer: UnderstandingEvolutionAnalyzer,
    ) -> None:
        self.evolution_analyzer = evolution_analyzer

    def assess(
        self,
        *,
        lineage: UnderstandingLineage,
        contradiction_support: dict[
            str,
            list[str],
        ] | None = None,
    ) -> LineageEvolutionAssessmentResult:
        """
        Assess every declared lineage edge against authoritative
        Understanding states.
        """

        contradiction_support = (
            contradiction_support
            or {}
        )

        assessments: list[
            LineageEvolutionAssessment
        ] = []

        for edge in lineage.edges:
            earlier = lineage.understandings[
                edge.earlier_understanding_id
            ]

            later = lineage.understandings[
                edge.later_understanding_id
            ]

            contradicted_ids = (
                contradiction_support.get(
                    later.understanding_id,
                    [],
                )
            )

            observed = (
                self.evolution_analyzer.compare(
                    earlier=earlier,
                    later=later,
                    contradicted_understanding_ids=(
                        contradicted_ids
                    ),
                )
            )

            observed_kind = observed.kind

            supported = (
                edge.kind.value
                == observed_kind.value
            )

            conflict = not supported

            if supported:
                basis = (
                    "The declared lineage relationship is "
                    "supported by the observed evolution of "
                    "the authoritative Understanding states."
                )
            else:
                basis = (
                    "The declared lineage relationship is not "
                    "supported by the observed evolution of "
                    "the authoritative Understanding states. "
                    f"Declared '{edge.kind.value}' but observed "
                    f"'{observed_kind.value}'."
                )

            assessments.append(
                LineageEvolutionAssessment(
                    earlier_understanding_id=(
                        earlier.understanding_id
                    ),
                    later_understanding_id=(
                        later.understanding_id
                    ),
                    declared_kind=edge.kind,
                    observed_kind=observed_kind,
                    supported=supported,
                    conflict=conflict,
                    basis=basis,
                )
            )

        return LineageEvolutionAssessmentResult(
            assessments=assessments,
            conflict_count=sum(
                1
                for assessment in assessments
                if assessment.conflict
            ),
        )
