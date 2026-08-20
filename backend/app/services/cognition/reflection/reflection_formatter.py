"""
Deterministic Reflection Formatter for SentinelAI.

The Formatter communicates governed Reflection.

It does not:

- perform Reflection,
- discover Patterns,
- generate Insights,
- generate Recommendations,
- calculate confidence,
- determine constitutional coherence,
- alter admissibility,
- execute Recommendations,
- manufacture unsupported cognition.

Cognition determines content.

Governance determines admissibility.

Formatting determines presentation.
"""

from __future__ import annotations

from app.services.cognition.reflection.reflection_orchestrator import (
    GovernedReflectionResult,
)


class ReflectionFormatter:
    """
    Render one governed Reflection as deterministic human-readable text.

    The Formatter has presentation authority only.
    """

    def format(
        self,
        governed: GovernedReflectionResult,
    ) -> str:
        """
        Format a governed Reflection without altering its cognition.
        """

        reflection = governed.reflection
        coherence = governed.coherence

        lines: list[str] = []

        # Reflection identity
        lines.append(
            f"REFLECTION: {reflection.title}"
        )
        lines.append("")

        lines.append(
            f"STATUS: {reflection.status.value}"
        )

        lines.append(
            f"SUMMARY: {reflection.summary}"
        )

        lines.append("")

        # Patterns
        lines.append("PATTERNS:")

        if reflection.patterns:
            for pattern in reflection.patterns:
                lines.append(
                    f"- {pattern.title}: "
                    f"{pattern.description}"
                )
        else:
            lines.append(
                "- None established."
            )

        lines.append("")

        # Insights
        lines.append("INSIGHTS:")

        if reflection.insights:
            for insight in reflection.insights:
                lines.append(
                    f"- {insight.title}: "
                    f"{insight.explanation}"
                )
        else:
            lines.append(
                "- None established."
            )

        lines.append("")

        # Recommendations
        lines.append("RECOMMENDATIONS:")

        if reflection.recommendations:
            for recommendation in (
                reflection.recommendations
            ):
                lines.append(
                    f"- {recommendation.title}: "
                    f"{recommendation.description}"
                )

                if (
                    recommendation
                    .requires_human_approval
                ):
                    lines.append(
                        "  Human approval required."
                    )
        else:
            lines.append(
                "- None established."
            )

        lines.append("")

        # Reflection confidence
        lines.append("REFLECTION CONFIDENCE:")

        lines.append(
            f"- Score: {reflection.confidence.score}"
        )

        lines.append(
            "- Level: "
            f"{reflection.confidence.level.value}"
        )

        lines.append(
            "- Basis: "
            f"{reflection.confidence.basis}"
        )

        if reflection.confidence.uncertainty:
            lines.append(
                "- Uncertainty:"
            )

            for uncertainty in (
                reflection.confidence.uncertainty
            ):
                lines.append(
                    f"  - {uncertainty}"
                )

        lines.append("")

        # Constitutional judgment
        lines.append(
            "CONSTITUTIONAL COHERENCE:"
        )

        lines.append(
            "- Coherent: "
            f"{coherence.coherent}"
        )

        lines.append(
            "- Constitutional score: "
            f"{coherence.constitutional_score}"
        )

        if governed.admissible:
            lines.append(
                "- Admissibility: ADMISSIBLE"
            )
        else:
            lines.append(
                "- Admissibility: INADMISSIBLE"
            )

        if coherence.articles_consulted:
            lines.append(
                "- Articles consulted:"
            )

            for article in (
                coherence.articles_consulted
            ):
                lines.append(
                    f"  - {article}"
                )

        if coherence.conflicts:
            lines.append(
                "- Constitutional conflicts:"
            )

            for conflict in coherence.conflicts:
                lines.append(
                    f"  - {conflict}"
                )

        if coherence.recommendations:
            lines.append(
                "- Constitutional recommendations:"
            )

            for recommendation in (
                coherence.recommendations
            ):
                lines.append(
                    f"  - {recommendation}"
                )

        lines.append("")

        # Authority boundary
        lines.append(
            "AUTHORITY:"
        )

        if reflection.recommendations:
            if any(
                recommendation.requires_human_approval
                for recommendation
                in reflection.recommendations
            ):
                lines.append(
                    "- Recommendations remain subject "
                    "to human approval."
                )

        lines.append(
            "- Constitutional admissibility does not "
            "grant execution authority."
        )

        return "\n".join(lines)
