"""
Deterministic Recommendation Generation for SentinelAI Reflection.

Recommendation Generation proposes responsible directions for future
learning from authoritative Reflection Insights.

It does not:

- discover Patterns,
- generate Insights,
- modify Learning Events,
- rewrite Memory,
- execute recommendations,
- alter the Constitution,
- grant authority to itself.

Recommendation proposes.

Recommendation does not execute.
"""

from __future__ import annotations

from hashlib import sha256

from app.services.cognition.reflection.models import (
    ReflectionInsight,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
)


class ReflectionRecommendationGenerator:
    """
    Generate deterministic Recommendations from authoritative Insights.

    Current deterministic scope:

    - one Recommendation per Insight,
    - inherited Pattern provenance,
    - inherited domain scope,
    - deterministic priority,
    - deterministic identity,
    - mandatory human approval.

    Richer recommendation strategies may later be introduced behind
    the same authoritative contract.
    """

    @staticmethod
    def _recommendation_id(
        insight: ReflectionInsight,
    ) -> str:
        """
        Produce stable Recommendation identity from Insight provenance.
        """

        canonical = "|".join(
            [
                "recommendation",
                insight.insight_id,
                *sorted(
                    insight.pattern_ids
                ),
            ]
        )

        digest = sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:16]

        return (
            f"recommendation-{digest}"
        )

    @staticmethod
    def _priority(
        insight: ReflectionInsight,
    ) -> int:
        """
        Convert bounded Insight confidence into deterministic priority.

        Lower numeric values represent greater attention priority.

        Priority does not grant execution authority.
        """

        confidence = (
            insight.confidence
            if insight.confidence is not None
            else 0.0
        )

        if confidence >= 0.80:
            return 1

        if confidence >= 0.50:
            return 2

        return 3

    @staticmethod
    def _kind(
        insight: ReflectionInsight,
    ) -> ReflectionRecommendationKind:
        """
        Select a conservative recommendation kind.

        Stronger structural support may justify strengthening future
        learning around the established Insight.

        Weaker support should direct future evidence gathering instead
        of stronger claims.
        """

        confidence = (
            insight.confidence
            if insight.confidence is not None
            else 0.0
        )

        if confidence >= 0.50:
            return (
                ReflectionRecommendationKind.STRENGTHEN
            )

        return (
            ReflectionRecommendationKind.GATHER_EVIDENCE
        )

    @staticmethod
    def _title(
        insight: ReflectionInsight,
    ) -> str:
        """
        Produce bounded future-learning language.
        """

        if insight.domain_ids:
            domain = insight.domain_ids[0]

            return (
                f"Continue examining {domain}"
            )

        return (
            "Continue examining the reflected learning area"
        )

    @staticmethod
    def _description(
        insight: ReflectionInsight,
    ) -> str:
        """
        Recommend future attention without claiming execution authority.
        """

        if insight.domain_ids:
            domain = insight.domain_ids[0]

            return (
                "Future learning should continue examining "
                f"'{domain}' in light of the established "
                "reflective Insight while preserving evidence "
                "traceability and openness to revision."
            )

        return (
            "Future learning should continue examining the "
            "established reflective Insight while preserving "
            "evidence traceability and openness to revision."
        )

    def generate(
        self,
        insights: list[ReflectionInsight],
    ) -> list[ReflectionRecommendation]:
        """
        Generate deterministic Recommendations from Insights.

        Input ordering does not affect authoritative output ordering.
        """

        if not insights:
            return []

        ordered_insights = sorted(
            insights,
            key=lambda insight: (
                insight.insight_id
            ),
        )

        recommendations: list[
            ReflectionRecommendation
        ] = []

        for insight in ordered_insights:
            recommendations.append(
                ReflectionRecommendation(
                    recommendation_id=(
                        self._recommendation_id(
                            insight
                        )
                    ),
                    kind=self._kind(
                        insight
                    ),
                    title=self._title(
                        insight
                    ),
                    description=(
                        self._description(
                            insight
                        )
                    ),
                    insight_ids=[
                        insight.insight_id,
                    ],
                    pattern_ids=list(
                        dict.fromkeys(
                            insight.pattern_ids
                        )
                    ),
                    domain_ids=list(
                        dict.fromkeys(
                            insight.domain_ids
                        )
                    ),
                    priority=self._priority(
                        insight
                    ),
                    requires_human_approval=True,
                    metadata={
                        "generation_method": (
                            "deterministic_insight_recommendation"
                        ),
                        "supporting_insight_count": 1,
                        "execution_authority": False,
                    },
                )
            )

        return recommendations
