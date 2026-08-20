"""
Modern Reflection Engine for SentinelAI.

The Reflection Engine coordinates one complete reflective operation.

It does not:

- analyze history directly,
- discover Patterns directly,
- generate Insights directly,
- generate Recommendations directly,
- determine constitutional coherence,
- format user communication,
- execute recommendations,
- modify Learning Events.

The Engine coordinates cognition.

Specialists own cognition.
"""

from __future__ import annotations

from app.core.cognition.models import (
    LearningEvent,
)

from app.services.cognition.reflection.history_analyzer import (
    ReflectionHistoryAnalyzer,
    ReflectionHistoryStatus,
)

from app.services.cognition.reflection.insight_generator import (
    ReflectionInsightGenerator,
)

from app.services.cognition.reflection.models import (
    ReflectionResult,
    ReflectionStatus,
)

from app.services.cognition.reflection.pattern_discoverer import (
    ReflectionPatternDiscoverer,
)

from app.services.cognition.reflection.recommendation_generator import (
    ReflectionRecommendationGenerator,
)

from app.services.cognition.reflection.reflection_confidence_engine import (
    ReflectionConfidenceEngine,
)


class ReflectionEngine:
    """
    Coordinate SentinelAI's deterministic Reflection Faculty.

    Epistemic prerequisites are enforced before downstream cognition
    is invoked.
    """

    def __init__(
        self,
        *,
        history_analyzer=None,
        pattern_discoverer=None,
        insight_generator=None,
        recommendation_generator=None,
        confidence_engine=None,
    ):
        self.history_analyzer = (
            history_analyzer
            or ReflectionHistoryAnalyzer()
        )

        self.pattern_discoverer = (
            pattern_discoverer
            or ReflectionPatternDiscoverer()
        )

        self.insight_generator = (
            insight_generator
            or ReflectionInsightGenerator()
        )

        self.recommendation_generator = (
            recommendation_generator
            or ReflectionRecommendationGenerator()
        )

        self.confidence_engine = (
            confidence_engine
            or ReflectionConfidenceEngine()
        )

    @staticmethod
    def _summary(
        *,
        status: ReflectionStatus,
        pattern_count: int,
        insight_count: int,
        recommendation_count: int,
    ) -> str:
        """
        Produce deterministic structured-summary language.

        This is part of the authoritative ReflectionResult metadata,
        not user-facing formatting.
        """

        if (
            status
            == ReflectionStatus.INSUFFICIENT_EVIDENCE
        ):
            return (
                "The available learning history is insufficient "
                "for responsible Reflection."
            )

        if status == ReflectionStatus.LIMITED:
            return (
                "Reflection was limited because the examined history "
                "did not support a complete reflective chain."
            )

        return (
            "Reflection completed with "
            f"{pattern_count} Pattern(s), "
            f"{insight_count} Insight(s), and "
            f"{recommendation_count} Recommendation(s)."
        )

    def reflect(
        self,
        *,
        learning_events: list[LearningEvent],
        title: str,
    ) -> ReflectionResult:
        """
        Execute one complete deterministic reflective cycle.
        """

        trace: list[str] = []

        history = self.history_analyzer.analyze(
            learning_events
        )

        trace.append(
            "Examined accumulated Learning Events."
        )

        if (
            history.status
            != ReflectionHistoryStatus.SUFFICIENT
        ):
            confidence = self.confidence_engine.evaluate(
                history=history,
                patterns=[],
                insights=[],
                recommendations=[],
            )

            trace.append(
                "Historical prerequisites were insufficient "
                "for Pattern discovery."
            )

            return ReflectionResult(
                title=title,
                summary=self._summary(
                    status=(
                        ReflectionStatus.INSUFFICIENT_EVIDENCE
                    ),
                    pattern_count=0,
                    insight_count=0,
                    recommendation_count=0,
                ),
                learning_event_ids=[
                    event.learning_event_id
                    for event in learning_events
                ],
                patterns=[],
                insights=[],
                recommendations=[],
                confidence=confidence,
                reflection_trace=trace,
                status=(
                    ReflectionStatus.INSUFFICIENT_EVIDENCE
                ),
                metadata={
                    "history_status": (
                        history.status.value
                    ),
                    "history_sufficient": False,
                },
            )

        patterns = (
            self.pattern_discoverer.discover(
                learning_events
            )
        )

        trace.append(
            "Discovered historical Patterns."
        )

        if not patterns:
            confidence = self.confidence_engine.evaluate(
                history=history,
                patterns=[],
                insights=[],
                recommendations=[],
            )

            trace.append(
                "No authoritative Pattern was established."
            )

            return ReflectionResult(
                title=title,
                summary=self._summary(
                    status=ReflectionStatus.LIMITED,
                    pattern_count=0,
                    insight_count=0,
                    recommendation_count=0,
                ),
                learning_event_ids=[
                    event.learning_event_id
                    for event in learning_events
                ],
                patterns=[],
                insights=[],
                recommendations=[],
                confidence=confidence,
                reflection_trace=trace,
                status=ReflectionStatus.LIMITED,
                metadata={
                    "history_status": (
                        history.status.value
                    ),
                    "history_sufficient": True,
                },
            )

        insights = self.insight_generator.generate(
            patterns
        )

        trace.append(
            "Generated Pattern-grounded Insights."
        )

        if not insights:
            confidence = self.confidence_engine.evaluate(
                history=history,
                patterns=patterns,
                insights=[],
                recommendations=[],
            )

            trace.append(
                "Patterns were established, but no authoritative "
                "Insight was produced."
            )

            return ReflectionResult(
                title=title,
                summary=self._summary(
                    status=ReflectionStatus.LIMITED,
                    pattern_count=len(patterns),
                    insight_count=0,
                    recommendation_count=0,
                ),
                learning_event_ids=[
                    event.learning_event_id
                    for event in learning_events
                ],
                patterns=patterns,
                insights=[],
                recommendations=[],
                confidence=confidence,
                reflection_trace=trace,
                status=ReflectionStatus.LIMITED,
                metadata={
                    "history_status": (
                        history.status.value
                    ),
                    "history_sufficient": True,
                },
            )

        recommendations = (
            self.recommendation_generator.generate(
                insights
            )
        )

        trace.append(
            "Generated bounded Recommendations for future learning."
        )

        confidence = self.confidence_engine.evaluate(
            history=history,
            patterns=patterns,
            insights=insights,
            recommendations=recommendations,
        )

        trace.append(
            "Evaluated Reflection confidence."
        )

        status = (
            ReflectionStatus.COMPLETE
            if recommendations
            else ReflectionStatus.LIMITED
        )

        return ReflectionResult(
            title=title,
            summary=self._summary(
                status=status,
                pattern_count=len(patterns),
                insight_count=len(insights),
                recommendation_count=len(
                    recommendations
                ),
            ),
            learning_event_ids=[
                event.learning_event_id
                for event in learning_events
            ],
            patterns=patterns,
            insights=insights,
            recommendations=recommendations,
            confidence=confidence,
            reflection_trace=trace,
            status=status,
            metadata={
                "history_status": (
                    history.status.value
                ),
                "history_sufficient": True,
            },
        )
