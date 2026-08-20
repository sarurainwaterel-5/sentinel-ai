"""
Deterministic Insight Generation for SentinelAI Reflection.

Insight Generation interprets authoritative Reflection Patterns.

It does not:

- discover Patterns,
- invent Learning Event provenance,
- invent Evidence provenance,
- generate Recommendations,
- execute actions,
- determine constitutional authority.

Interpretation may compress evidence.

Interpretation may never exceed evidence.
"""

from __future__ import annotations

from hashlib import sha256

from app.services.cognition.reflection.models import (
    ReflectionInsight,
    ReflectionPattern,
)


class ReflectionInsightGenerator:
    """
    Generate deterministic Insights from authoritative Reflection Patterns.

    Current deterministic scope:

    - one Insight per Pattern,
    - inherited Learning Event provenance,
    - inherited Evidence provenance,
    - bounded structural confidence,
    - deterministic Insight identity.

    Richer semantic interpretation may be introduced later through a
    separate governed implementation while preserving this contract.
    """

    @staticmethod
    def _insight_id(
        pattern: ReflectionPattern,
    ) -> str:
        """
        Produce a stable Insight ID from authoritative Pattern identity.
        """

        canonical = "|".join(
            [
                "insight",
                pattern.pattern_id,
                pattern.kind.value,
                *sorted(pattern.learning_event_ids),
            ]
        )

        digest = sha256(
            canonical.encode("utf-8")
        ).hexdigest()[:16]

        return f"insight-{digest}"

    @staticmethod
    def _confidence(
        pattern: ReflectionPattern,
    ) -> float:
        """
        Calculate deterministic structural Insight confidence.

        Confidence reflects breadth of historical Pattern support.

        It does not represent constitutional coherence.
        """

        support_count = len(
            set(pattern.learning_event_ids)
        )

        base = 0.55

        support_bonus = min(
            0.30,
            max(
                0,
                support_count - 2,
            )
            * 0.10,
        )

        evidence_bonus = (
            0.10
            if pattern.evidence_ids
            else 0.0
        )

        return min(
            1.0,
            round(
                base
                + support_bonus
                + evidence_bonus,
                3,
            ),
        )

    @staticmethod
    def _title(
        pattern: ReflectionPattern,
    ) -> str:
        """
        Produce deterministic Insight language from Pattern structure.
        """

        if pattern.domain_ids:
            domain = pattern.domain_ids[0]

            return (
                f"Recurring learning area: {domain}"
            )

        return (
            f"Historical {pattern.kind.value} identified"
        )

    @staticmethod
    def _explanation(
        pattern: ReflectionPattern,
    ) -> str:
        """
        Explain only what the authoritative Pattern already establishes.
        """

        event_count = len(
            set(pattern.learning_event_ids)
        )

        if pattern.domain_ids:
            domain = pattern.domain_ids[0]

            return (
                f"The examined learning history shows that "
                f"'{domain}' recurs across {event_count} "
                "Learning Events. This indicates that the domain "
                "is a repeated area within the accumulated "
                "learning history."
            )

        return (
            "The examined learning history contains an "
            f"authoritative {pattern.kind.value} Pattern supported "
            f"by {event_count} Learning Events."
        )

    def generate(
        self,
        patterns: list[ReflectionPattern],
    ) -> list[ReflectionInsight]:
        """
        Generate deterministic Insights from authoritative Patterns.

        Pattern order does not affect authoritative Insight output.
        """

        if not patterns:
            return []

        ordered_patterns = sorted(
            patterns,
            key=lambda pattern: (
                pattern.pattern_id
            ),
        )

        insights: list[
            ReflectionInsight
        ] = []

        for pattern in ordered_patterns:
            insights.append(
                ReflectionInsight(
                    insight_id=(
                        self._insight_id(
                            pattern
                        )
                    ),
                    title=self._title(
                        pattern
                    ),
                    explanation=(
                        self._explanation(
                            pattern
                        )
                    ),
                    pattern_ids=[
                        pattern.pattern_id,
                    ],
                    learning_event_ids=list(
                        dict.fromkeys(
                            pattern.learning_event_ids
                        )
                    ),
                    evidence_ids=list(
                        dict.fromkeys(
                            pattern.evidence_ids
                        )
                    ),
                    domain_ids=list(
                        dict.fromkeys(
                            pattern.domain_ids
                        )
                    ),
                    confidence=(
                        self._confidence(
                            pattern
                        )
                    ),
                    metadata={
                        "generation_method": (
                            "deterministic_pattern_interpretation"
                        ),
                        "supporting_pattern_count": 1,
                        "supporting_event_count": len(
                            set(
                                pattern.learning_event_ids
                            )
                        ),
                    },
                )
            )

        return insights
