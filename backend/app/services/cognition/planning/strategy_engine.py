"""
Deterministic strategy generation for SentinelAI planning.

The strategy engine converts a PlanningContext into inspectable candidate
strategies without using an LLM.

Sprint 15 begins conservatively:

- strategies remain close to the supplied objective and reasoning,
- reasoning insufficiency produces no strategy,
- constraints and uncertainty influence strategy selection,
- candidate suitability is calculated deterministically,
- rejected alternatives remain visible,
- no steps are generated,
- no actions are executed.

This service does not produce the final PlanningResult.
"""

from __future__ import annotations

import re

from app.services.cognition.planning.models import (
    PlanningContext,
    PlanningStrategy,
)


class StrategyEngine:
    """
    Produce and rank conservative strategies from a planning context.

    The engine is intentionally domain-neutral and deterministic.
    Domain-specific strategy policies may be added later without changing
    the PlanningStrategy contract.
    """

    def __init__(
        self,
        *,
        maximum_strategies: int = 3,
    ):
        self.maximum_strategies = maximum_strategies

    @staticmethod
    def _normalize_whitespace(
        value: str,
    ) -> str:
        """
        Collapse repeated whitespace without changing meaning.
        """

        return re.sub(
            r"\s+",
            " ",
            value,
        ).strip()

    @classmethod
    def _bounded_text(
        cls,
        value: str,
        *,
        limit: int = 420,
    ) -> str:
        """
        Return bounded text without introducing new factual claims.
        """

        cleaned = cls._normalize_whitespace(value)

        if len(cleaned) <= limit:
            return cleaned

        shortened = cleaned[:limit].rsplit(
            " ",
            1,
        )[0]

        return f"{shortened}…"

    @staticmethod
    def _reasoning_is_sufficient(
        context: PlanningContext,
    ) -> bool:
        """
        Determine whether planning has an authoritative reasoning basis.

        Planning must not invent a strategy when reasoning produced no
        supported conclusion.
        """

        reasoning = context.reasoning_result

        if reasoning.status != "complete":
            return False

        if reasoning.conclusion is None:
            return False

        if not reasoning.conclusion.statement.strip():
            return False

        return True

    @staticmethod
    def _reasoning_confidence(
        context: PlanningContext,
    ) -> float:
        """
        Return the authoritative reasoning-confidence score.
        """

        conclusion = context.reasoning_result.conclusion

        if conclusion is None:
            return 0.0

        return conclusion.confidence.score

    @staticmethod
    def _uncertainty_items(
        context: PlanningContext,
    ) -> list[str]:
        """
        Collect visible reasoning uncertainty without altering it.
        """

        conclusion = context.reasoning_result.conclusion

        if conclusion is None:
            return []

        uncertainty = [
            *conclusion.limitations,
            *conclusion.missing_information,
            *conclusion.confidence.uncertainty,
        ]

        unique_items: list[str] = []

        for item in uncertainty:
            normalized = item.strip()

            if normalized and normalized not in unique_items:
                unique_items.append(normalized)

        return unique_items

    @staticmethod
    def _normalized_pressure(
        count: int,
        *,
        saturation: int,
    ) -> float:
        """
        Convert an item count into a bounded pressure score.
        """

        if saturation <= 0:
            return 0.0

        return min(
            count / saturation,
            1.0,
        )

    @classmethod
    def _uncertainty_pressure(
        cls,
        context: PlanningContext,
    ) -> float:
        return cls._normalized_pressure(
            len(cls._uncertainty_items(context)),
            saturation=5,
        )

    @classmethod
    def _constraint_pressure(
        cls,
        context: PlanningContext,
    ) -> float:
        return cls._normalized_pressure(
            len(context.constraints),
            saturation=4,
        )

    @classmethod
    def _assumption_pressure(
        cls,
        context: PlanningContext,
    ) -> float:
        return cls._normalized_pressure(
            len(context.supplied_assumptions),
            saturation=4,
        )

    @staticmethod
    def _supported_by_reasoning(
        context: PlanningContext,
    ) -> list[str]:
        """
        Preserve the reasoning statements that support strategy selection.
        """

        conclusion = context.reasoning_result.conclusion

        if conclusion is None:
            return []

        support = [
            conclusion.statement,
        ]

        if conclusion.evidence_summary:
            support.append(
                conclusion.evidence_summary
            )

        return support

    @staticmethod
    def _clamp_score(
        score: float,
    ) -> float:
        """
        Keep strategy suitability inside the public score boundary.
        """

        return round(
            max(
                0.0,
                min(score, 1.0),
            ),
            3,
        )

    def _direct_strategy(
        self,
        context: PlanningContext,
    ) -> PlanningStrategy:
        """
        Build a direct sequential strategy candidate.

        This candidate becomes more suitable when reasoning confidence is
        strong and uncertainty, assumptions, and constraints are limited.
        """

        confidence = self._reasoning_confidence(
            context
        )

        uncertainty = self._uncertainty_pressure(
            context
        )

        constraints = self._constraint_pressure(
            context
        )

        assumptions = self._assumption_pressure(
            context
        )

        suitability = (
            confidence * 0.55
            + (1.0 - uncertainty) * 0.20
            + (1.0 - constraints) * 0.15
            + (1.0 - assumptions) * 0.10
        )

        return PlanningStrategy(
            name="Direct sequential strategy",
            description=(
                "Advance toward the objective through a clear ordered "
                "sequence with verification at defined completion points."
            ),
            rationale=(
                "This approach is suitable when the reasoning conclusion "
                "is sufficiently supported and the plan is not heavily "
                "constrained by unresolved uncertainty or assumptions."
            ),
            supported_by_reasoning=(
                self._supported_by_reasoning(
                    context
                )
            ),
            rejected_alternatives=[],
            suitability_score=(
                self._clamp_score(
                    suitability
                )
            ),
        )

    def _phased_strategy(
        self,
        context: PlanningContext,
    ) -> PlanningStrategy:
        """
        Build a phased and verification-led strategy candidate.

        This candidate becomes more suitable as uncertainty, constraints,
        and operational assumptions increase.
        """

        confidence = self._reasoning_confidence(
            context
        )

        uncertainty = self._uncertainty_pressure(
            context
        )

        constraints = self._constraint_pressure(
            context
        )

        assumptions = self._assumption_pressure(
            context
        )

        suitability = (
            confidence * 0.35
            + uncertainty * 0.25
            + constraints * 0.20
            + assumptions * 0.10
            + 0.10
        )

        return PlanningStrategy(
            name="Phased verification-led strategy",
            description=(
                "Advance through bounded phases, validating required "
                "conditions and outcomes before moving to the next phase."
            ),
            rationale=(
                "A phased approach limits exposure when the objective "
                "contains meaningful constraints, assumptions, or "
                "reasoning uncertainty."
            ),
            supported_by_reasoning=(
                self._supported_by_reasoning(
                    context
                )
            ),
            rejected_alternatives=[],
            suitability_score=(
                self._clamp_score(
                    suitability
                )
            ),
        )

    def _clarification_strategy(
        self,
        context: PlanningContext,
    ) -> PlanningStrategy:
        """
        Build a clarification-first strategy candidate.

        This candidate does not replace insufficient reasoning. It applies
        only when a supported conclusion exists but important planning
        uncertainty remains unresolved.
        """

        confidence = self._reasoning_confidence(
            context
        )

        uncertainty = self._uncertainty_pressure(
            context
        )

        constraints = self._constraint_pressure(
            context
        )

        assumptions = self._assumption_pressure(
            context
        )

        suitability = (
            (1.0 - confidence) * 0.20
            + uncertainty * 0.40
            + assumptions * 0.25
            + constraints * 0.10
            + 0.05
        )

        return PlanningStrategy(
            name="Clarification-first strategy",
            description=(
                "Resolve the highest-impact unknowns and assumptions "
                "before committing to detailed implementation steps."
            ),
            rationale=(
                "The reasoning supports a direction, but unresolved "
                "planning uncertainty could materially change the safest "
                "or most effective course of action."
            ),
            supported_by_reasoning=(
                self._supported_by_reasoning(
                    context
                )
            ),
            rejected_alternatives=[],
            suitability_score=(
                self._clamp_score(
                    suitability
                )
            ),
        )

    def _generate_candidates(
        self,
        context: PlanningContext,
    ) -> list[PlanningStrategy]:
        """
        Generate bounded strategy candidates.

        Candidate generation remains deterministic and domain-neutral.
        """

        return [
            self._direct_strategy(context),
            self._phased_strategy(context),
            self._clarification_strategy(
                context
            ),
        ]

    @staticmethod
    def _rank_candidates(
        candidates: list[PlanningStrategy],
    ) -> list[PlanningStrategy]:
        """
        Rank candidates by suitability with a stable name tie-breaker.
        """

        return sorted(
            candidates,
            key=lambda candidate: (
                candidate.suitability_score,
                candidate.name,
            ),
            reverse=True,
        )

    @staticmethod
    def _attach_rejected_alternatives(
        candidates: list[PlanningStrategy],
    ) -> list[PlanningStrategy]:
        """
        Preserve alternatives rejected during deterministic ranking.
        """

        candidate_names = [
            candidate.name
            for candidate in candidates
        ]

        enriched: list[PlanningStrategy] = []

        for candidate in candidates:
            rejected = [
                name
                for name in candidate_names
                if name != candidate.name
            ]

            enriched.append(
                candidate.model_copy(
                    update={
                        "rejected_alternatives": (
                            rejected
                        ),
                    }
                )
            )

        return enriched

    def generate(
        self,
        context: PlanningContext,
    ) -> list[PlanningStrategy]:
        """
        Generate ranked candidate strategies from a PlanningContext.

        Insufficient reasoning produces no strategy candidates rather than
        an unsupported plan.
        """

        if not self._reasoning_is_sufficient(
            context
        ):
            return []

        candidates = self._generate_candidates(
            context
        )

        ranked = self._rank_candidates(
            candidates
        )

        enriched = (
            self._attach_rejected_alternatives(
                ranked
            )
        )

        return enriched[
            : self.maximum_strategies
        ]

    def select(
        self,
        context: PlanningContext,
    ) -> PlanningStrategy | None:
        """
        Return the strongest supported strategy candidate.

        The full ranked candidate list remains available through
        generate() for inspection and future decision layers.
        """

        candidates = self.generate(context)

        if not candidates:
            return None

        return candidates[0]
