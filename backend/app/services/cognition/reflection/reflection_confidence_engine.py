"""
Deterministic Reflection Confidence Engine for SentinelAI.

Reflection Confidence measures how strongly the complete reflective
record supports the reflective judgment.

It does not:

- determine constitutional coherence,
- determine objective truth,
- grant execution authority,
- replace Pattern or Insight confidence,
- modify reflective artifacts,
- manufacture missing support.

Confidence must remain bounded, explainable, and accountable to the
reflective record.
"""

from __future__ import annotations

from statistics import mean

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAssessment,
    ReflectionHistoryStatus,
)

from app.services.cognition.reflection.models import (
    ReflectionConfidence,
    ReflectionConfidenceFactor,
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionRecommendation,
)


class ReflectionConfidenceEngine:
    """
    Evaluate confidence in one complete reflective judgment.

    Current deterministic factors:

    - historical sufficiency,
    - Pattern support,
    - evidence coverage,
    - Insight confidence,
    - provenance traceability.

    Constitutional coherence remains a separate authority.
    """

    HISTORY_WEIGHT = 0.25
    PATTERN_WEIGHT = 0.20
    EVIDENCE_WEIGHT = 0.20
    INSIGHT_WEIGHT = 0.20
    TRACEABILITY_WEIGHT = 0.15

    @staticmethod
    def _historical_sufficiency(
        history: ReflectionHistoryAssessment,
    ) -> float:
        """
        Score whether Reflection has an adequate historical basis.
        """

        if (
            history.status
            == ReflectionHistoryStatus.SUFFICIENT
        ):
            return 1.0

        if (
            history.status
            == ReflectionHistoryStatus.INSUFFICIENT_COMPARABILITY
        ):
            return 0.25

        if (
            history.status
            == ReflectionHistoryStatus.INSUFFICIENT_HISTORY
        ):
            return 0.10

        return 0.0

    @staticmethod
    def _pattern_support(
        patterns: list[ReflectionPattern],
    ) -> float:
        """
        Measure breadth of historical support beneath Patterns.

        Two supporting events establish minimum recurrence.
        Broader support increases confidence conservatively.
        """

        if not patterns:
            return 0.0

        support_counts = [
            len(
                set(
                    pattern.learning_event_ids
                )
            )
            for pattern in patterns
        ]

        average_support = mean(
            support_counts
        )

        if average_support >= 5:
            return 1.0

        if average_support >= 4:
            return 0.90

        if average_support >= 3:
            return 0.80

        if average_support >= 2:
            return 0.70

        return 0.0

    @staticmethod
    def _insight_confidence(
        insights: list[ReflectionInsight],
    ) -> float:
        """
        Aggregate bounded confidence from authoritative Insights.
        """

        if not insights:
            return 0.0

        values = [
            (
                insight.confidence
                if insight.confidence is not None
                else 0.0
            )
            for insight in insights
        ]

        return max(
            0.0,
            min(
                1.0,
                mean(values),
            ),
        )

    @staticmethod
    def _traceability(
        *,
        patterns: list[ReflectionPattern],
        insights: list[ReflectionInsight],
        recommendations: list[
            ReflectionRecommendation
        ],
    ) -> float:
        """
        Measure whether the reflective provenance chain resolves.

        Pattern -> Learning Event provenance is structurally required
        by the Pattern contract.

        This factor checks downstream references:

        Recommendation -> Insight -> Pattern
        """

        if not patterns or not insights:
            return 0.0

        pattern_ids = {
            pattern.pattern_id
            for pattern in patterns
        }

        insight_ids = {
            insight.insight_id
            for insight in insights
        }

        checks: list[bool] = []

        for insight in insights:
            checks.append(
                bool(insight.pattern_ids)
                and set(
                    insight.pattern_ids
                ).issubset(
                    pattern_ids
                )
            )

        for recommendation in recommendations:
            checks.append(
                bool(
                    recommendation.insight_ids
                )
                and set(
                    recommendation.insight_ids
                ).issubset(
                    insight_ids
                )
            )

            checks.append(
                set(
                    recommendation.pattern_ids
                ).issubset(
                    pattern_ids
                )
            )

        if not checks:
            return 0.0

        return (
            sum(checks)
            / len(checks)
        )

    @staticmethod
    def _level(
        score: float,
    ) -> ReflectionConfidenceLevel:
        """
        Translate bounded score into a human-readable confidence band.
        """

        if score >= 0.75:
            return ReflectionConfidenceLevel.HIGH

        if score >= 0.50:
            return ReflectionConfidenceLevel.MODERATE

        return ReflectionConfidenceLevel.LOW

    def evaluate(
        self,
        *,
        history: ReflectionHistoryAssessment,
        patterns: list[ReflectionPattern],
        insights: list[ReflectionInsight],
        recommendations: list[
            ReflectionRecommendation
        ],
    ) -> ReflectionConfidence:
        """
        Evaluate one complete reflective record.
        """

        historical_score = (
            self._historical_sufficiency(
                history
            )
        )

        pattern_score = (
            self._pattern_support(
                patterns
            )
        )

        evidence_score = max(
            0.0,
            min(
                1.0,
                history.evidence_coverage,
            ),
        )

        insight_score = (
            self._insight_confidence(
                insights
            )
        )

        traceability_score = (
            self._traceability(
                patterns=patterns,
                insights=insights,
                recommendations=recommendations,
            )
        )

        score = (
            historical_score
            * self.HISTORY_WEIGHT
            + pattern_score
            * self.PATTERN_WEIGHT
            + evidence_score
            * self.EVIDENCE_WEIGHT
            + insight_score
            * self.INSIGHT_WEIGHT
            + traceability_score
            * self.TRACEABILITY_WEIGHT
        )

        score = round(
            max(
                0.0,
                min(
                    1.0,
                    score,
                ),
            ),
            3,
        )

        level = self._level(
            score
        )

        factors = [
            ReflectionConfidenceFactor(
                name="historical_sufficiency",
                contribution=round(
                    historical_score
                    * self.HISTORY_WEIGHT,
                    3,
                ),
                explanation=(
                    "Measures whether accumulated Learning "
                    "Events provide a sufficient comparable "
                    "basis for Reflection."
                ),
            ),
            ReflectionConfidenceFactor(
                name="pattern_support",
                contribution=round(
                    pattern_score
                    * self.PATTERN_WEIGHT,
                    3,
                ),
                explanation=(
                    "Measures the breadth of Learning Event "
                    "support beneath discovered Patterns."
                ),
            ),
            ReflectionConfidenceFactor(
                name="evidence_coverage",
                contribution=round(
                    evidence_score
                    * self.EVIDENCE_WEIGHT,
                    3,
                ),
                explanation=(
                    "Measures how much of the examined "
                    "learning history contains recorded "
                    "Evidence."
                ),
            ),
            ReflectionConfidenceFactor(
                name="insight_confidence",
                contribution=round(
                    insight_score
                    * self.INSIGHT_WEIGHT,
                    3,
                ),
                explanation=(
                    "Measures the aggregate structural "
                    "confidence of generated Insights."
                ),
            ),
            ReflectionConfidenceFactor(
                name="traceability",
                contribution=round(
                    traceability_score
                    * self.TRACEABILITY_WEIGHT,
                    3,
                ),
                explanation=(
                    "Measures whether downstream reflective "
                    "claims remain traceable to authoritative "
                    "upstream artifacts."
                ),
            ),
        ]

        uncertainty = list(
            dict.fromkeys(
                history.limitations
            )
        )

        if not patterns:
            uncertainty.append(
                "No authoritative Patterns were available."
            )

        if not insights:
            uncertainty.append(
                "No authoritative Insights were available."
            )

        if traceability_score < 1.0:
            uncertainty.append(
                "The reflective provenance chain is incomplete."
            )

        uncertainty = list(
            dict.fromkeys(
                uncertainty
            )
        )

        if level == ReflectionConfidenceLevel.HIGH:
            basis = (
                "The reflective judgment has strong historical, "
                "evidentiary, interpretive, and traceability support."
            )

        elif level == ReflectionConfidenceLevel.MODERATE:
            basis = (
                "The reflective judgment has meaningful support, "
                "but one or more confidence factors remain limited."
            )

        else:
            basis = (
                "The reflective judgment has limited support and "
                "should remain subject to further learning or evidence."
            )

        return ReflectionConfidence(
            score=score,
            level=level,
            basis=basis,
            factors=factors,
            uncertainty=uncertainty,
        )
