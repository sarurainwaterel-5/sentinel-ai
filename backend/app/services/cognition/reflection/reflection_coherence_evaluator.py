"""
Constitutional coherence evaluation for SentinelAI Reflection.

Reflection may be structurally valid and strongly supported while still
remaining constitutionally inadmissible.

Confidence measures support.

Constitution governs admissibility.

This evaluator does not:

- generate Reflection,
- modify Reflection,
- rewrite confidence,
- repair constitutional conflicts,
- execute Recommendations,
- grant execution authority.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.services.cognition.coherence.coherence_engine import (
    CoherenceEngine,
)

from app.services.cognition.reflection.models import (
    ReflectionResult,
)


class ReflectionCoherenceResult(BaseModel):
    """
    Constitutional judgment applied to one authoritative Reflection.

    Admissibility is independent from Reflection confidence.
    """

    coherent: bool

    admissible: bool

    constitutional_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reflection_confidence: float = Field(
        ge=0.0,
        le=1.0,
    )

    articles_consulted: list[str] = Field(
        default_factory=list,
    )

    conflicts: list[str] = Field(
        default_factory=list,
    )

    recommendations: list[str] = Field(
        default_factory=list,
    )


class ReflectionCoherenceEvaluator:
    """
    Evaluate whether an authoritative Reflection is constitutionally
    admissible.

    The shared CoherenceEngine provides the constitutional judgment.

    This adapter preserves Reflection-specific authority boundaries.
    """

    def __init__(
        self,
        *,
        coherence_engine=None,
    ):
        self.coherence_engine = (
            coherence_engine
            or CoherenceEngine()
        )

    @staticmethod
    def _payload(
        result: Any,
    ) -> dict[str, Any]:
        """
        Normalize supported CoherenceEngine result representations.
        """

        if hasattr(
            result,
            "model_dump",
        ):
            return result.model_dump()

        if isinstance(
            result,
            dict,
        ):
            return result

        raise TypeError(
            "Unsupported constitutional coherence result."
        )

    @staticmethod
    def _reflection_context(
        reflection: ReflectionResult,
    ) -> str:
        """
        Produce bounded structured context for constitutional evaluation.

        This is not user-facing formatting and does not alter Reflection.
        """

        lines = [
            f"Reflection title: {reflection.title}",
            f"Reflection status: {reflection.status.value}",
            (
                "Reflection confidence: "
                f"{reflection.confidence.score}"
            ),
            f"Summary: {reflection.summary}",
        ]

        for pattern in reflection.patterns:
            lines.append(
                "Pattern: "
                f"{pattern.kind.value} | "
                f"{pattern.title} | "
                f"{pattern.description}"
            )

        for insight in reflection.insights:
            lines.append(
                "Insight: "
                f"{insight.title} | "
                f"{insight.explanation}"
            )

        for recommendation in (
            reflection.recommendations
        ):
            lines.append(
                "Recommendation: "
                f"{recommendation.kind.value} | "
                f"{recommendation.title} | "
                f"{recommendation.description} | "
                "requires_human_approval="
                f"{recommendation.requires_human_approval}"
            )

        return "\n".join(
            lines
        )

    def evaluate(
        self,
        *,
        reflection: ReflectionResult,
        constitutional_context: str,
    ) -> ReflectionCoherenceResult:
        """
        Apply constitutional evaluation to one completed Reflection.
        """

        raw_result = (
            self.coherence_engine.evaluate(
                question=reflection.title,
                identity_context=(
                    constitutional_context
                ),
                knowledge_context=(
                    self._reflection_context(
                        reflection
                    )
                ),
            )
        )

        payload = self._payload(
            raw_result
        )

        coherent = bool(
            payload.get(
                "coherent",
                False,
            )
        )

        constitutional_score = float(
            payload.get(
                "constitutional_score",
                0.0,
            )
        )

        return ReflectionCoherenceResult(
            coherent=coherent,
            admissible=coherent,
            constitutional_score=(
                constitutional_score
            ),
            reflection_confidence=(
                reflection.confidence.score
            ),
            articles_consulted=list(
                payload.get(
                    "articles_consulted",
                    [],
                )
            ),
            conflicts=list(
                payload.get(
                    "conflicts",
                    [],
                )
            ),
            recommendations=list(
                payload.get(
                    "recommendations",
                    [],
                )
            ),
        )
