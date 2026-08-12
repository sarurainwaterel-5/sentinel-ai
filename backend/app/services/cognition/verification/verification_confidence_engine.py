"""
Explainable confidence assessment for SentinelAI verification.

Verification confidence evaluates the reliability and completeness of
the verification operation itself.

It does not evaluate the quality of the underlying PlanningResult.

A verification operation may therefore have high confidence while
correctly identifying serious defects in the verified subject.
"""

from __future__ import annotations

from statistics import mean

from app.services.cognition.verification.models import (
    VerificationConfidence,
    VerificationConfidenceFactor,
    VerificationConfidenceLevel,
    VerificationCoverage,
    VerificationInspection,
    VerificationOutcome,
)


class VerificationConfidenceEngine:
    """
    Calculate transparent confidence in one verification operation.

    Every factor produces:

    - a bounded contribution,
    - a human-readable explanation,
    - an inspectable effect on the final score.
    """

    @staticmethod
    def _clamp(
        value: float,
        minimum: float = 0.0,
        maximum: float = 1.0,
    ) -> float:
        return max(
            minimum,
            min(value, maximum),
        )

    @staticmethod
    def _confidence_level(
        score: float,
    ) -> VerificationConfidenceLevel:
        if score >= 0.80:
            return VerificationConfidenceLevel.HIGH

        if score >= 0.60:
            return VerificationConfidenceLevel.MODERATE

        return VerificationConfidenceLevel.LOW

    @classmethod
    def _category_coverage_factor(
        cls,
        coverage: VerificationCoverage,
    ) -> VerificationConfidenceFactor:
        contribution = (
            cls._clamp(coverage.coverage_score)
            * 0.35
        )

        return VerificationConfidenceFactor(
            name="category_coverage",
            contribution=round(
                contribution,
                4,
            ),
            explanation=(
                f"{len(coverage.completed_categories)} of "
                f"{len(coverage.requested_categories)} requested "
                "verification categories were completed."
            ),
        )

    @classmethod
    def _inspection_completion_factor(
        cls,
        inspections: list[VerificationInspection],
    ) -> VerificationConfidenceFactor:
        if not inspections:
            completion_ratio = 0.0
        else:
            completion_ratio = mean(
                1.0 if inspection.completed else 0.0
                for inspection in inspections
            )

        contribution = (
            cls._clamp(completion_ratio)
            * 0.20
        )

        return VerificationConfidenceFactor(
            name="inspection_completion",
            contribution=round(
                contribution,
                4,
            ),
            explanation=(
                f"{completion_ratio:.0%} of supplied specialist "
                "inspections are marked complete."
            ),
        )

    @classmethod
    def _standard_coverage_factor(
        cls,
        inspections: list[VerificationInspection],
    ) -> VerificationConfidenceFactor:
        completed = [
            inspection
            for inspection in inspections
            if inspection.completed
        ]

        if not completed:
            coverage_ratio = 0.0
        else:
            coverage_ratio = mean(
                1.0 if inspection.standards else 0.0
                for inspection in completed
            )

        contribution = (
            cls._clamp(coverage_ratio)
            * 0.15
        )

        return VerificationConfidenceFactor(
            name="standard_coverage",
            contribution=round(
                contribution,
                4,
            ),
            explanation=(
                f"{coverage_ratio:.0%} of completed inspections "
                "applied explicit verification standards."
            ),
        )

    @classmethod
    def _check_coverage_factor(
        cls,
        inspections: list[VerificationInspection],
    ) -> VerificationConfidenceFactor:
        completed = [
            inspection
            for inspection in inspections
            if inspection.completed
        ]

        if not completed:
            coverage_ratio = 0.0
        else:
            coverage_ratio = mean(
                1.0 if inspection.checks else 0.0
                for inspection in completed
            )

        contribution = (
            cls._clamp(coverage_ratio)
            * 0.15
        )

        return VerificationConfidenceFactor(
            name="check_coverage",
            contribution=round(
                contribution,
                4,
            ),
            explanation=(
                f"{coverage_ratio:.0%} of completed inspections "
                "produced explicit verification checks."
            ),
        )

    @classmethod
    def _trace_quality_factor(
        cls,
        inspections: list[VerificationInspection],
    ) -> VerificationConfidenceFactor:
        completed = [
            inspection
            for inspection in inspections
            if inspection.completed
        ]

        if not completed:
            trace_ratio = 0.0
        else:
            trace_ratio = mean(
                1.0 if inspection.inspection_trace else 0.0
                for inspection in completed
            )

        contribution = (
            cls._clamp(trace_ratio)
            * 0.15
        )

        return VerificationConfidenceFactor(
            name="inspection_trace_quality",
            contribution=round(
                contribution,
                4,
            ),
            explanation=(
                f"{trace_ratio:.0%} of completed inspections "
                "preserve a user-safe inspection trace."
            ),
        )

    @staticmethod
    def _unverifiable_factor(
        coverage: VerificationCoverage,
    ) -> VerificationConfidenceFactor:
        if coverage.check_count == 0:
            burden = 0.0
        else:
            burden = (
                coverage.unverifiable_count
                / coverage.check_count
            )

        penalty = min(
            burden * 0.35,
            0.35,
        )

        return VerificationConfidenceFactor(
            name="unverifiable_burden",
            contribution=round(
                -penalty,
                4,
            ),
            explanation=(
                f"{coverage.unverifiable_count} of "
                f"{coverage.check_count} verification checks "
                "were not verifiable."
            ),
        )

    @staticmethod
    def _uncertainty(
        *,
        coverage: VerificationCoverage,
        inspections: list[VerificationInspection],
    ) -> list[str]:
        uncertainty: list[str] = []

        if coverage.skipped_categories:
            skipped = ", ".join(
                category.value
                for category in coverage.skipped_categories
            )

            uncertainty.append(
                "Requested verification categories were skipped: "
                f"{skipped}."
            )

        for inspection in inspections:
            if not inspection.completed:
                uncertainty.append(
                    "The "
                    f"{inspection.category.value} inspection "
                    "was not completed."
                )

            for check in inspection.checks:
                if (
                    check.outcome
                    == VerificationOutcome.NOT_VERIFIABLE
                ):
                    uncertainty.extend(
                        check.uncertainty
                        or [
                            (
                                f"Check '{check.check_id}' could "
                                "not be verified."
                            )
                        ]
                    )

        deduplicated: list[str] = []
        seen: set[str] = set()

        for statement in uncertainty:
            cleaned = str(statement).strip()

            if not cleaned:
                continue

            identity = cleaned.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            deduplicated.append(cleaned)

        return deduplicated

    @staticmethod
    def _basis(
        *,
        score: float,
        coverage: VerificationCoverage,
        inspections: list[VerificationInspection],
    ) -> str:
        completed_count = sum(
            1
            for inspection in inspections
            if inspection.completed
        )

        return (
            "Verification confidence is based on "
            f"{completed_count} completed specialist inspection"
            f"{'' if completed_count == 1 else 's'}, "
            f"{len(coverage.completed_categories)} completed categor"
            f"{'y' if len(coverage.completed_categories) == 1 else 'ies'}, "
            f"{coverage.check_count} verification check"
            f"{'' if coverage.check_count == 1 else 's'}, "
            f"{coverage.unverifiable_count} unverifiable check"
            f"{'' if coverage.unverifiable_count == 1 else 's'}, and "
            f"a category coverage score of "
            f"{coverage.coverage_score:.3f}. "
            f"The resulting verification-confidence score is "
            f"{score:.3f}."
        )

    def assess(
        self,
        *,
        coverage: VerificationCoverage,
        inspections: list[VerificationInspection],
    ) -> VerificationConfidence:
        """
        Produce one explainable verification-confidence assessment.

        Scores are derived entirely from structured coverage and
        specialist-inspection contracts.
        """

        factors = [
            self._category_coverage_factor(
                coverage
            ),
            self._inspection_completion_factor(
                inspections
            ),
            self._standard_coverage_factor(
                inspections
            ),
            self._check_coverage_factor(
                inspections
            ),
            self._trace_quality_factor(
                inspections
            ),
            self._unverifiable_factor(
                coverage
            ),
        ]

        score = round(
            self._clamp(
                sum(
                    factor.contribution
                    for factor in factors
                )
            ),
            3,
        )

        return VerificationConfidence(
            score=score,
            level=self._confidence_level(
                score
            ),
            basis=self._basis(
                score=score,
                coverage=coverage,
                inspections=inspections,
            ),
            factors=factors,
            uncertainty=self._uncertainty(
                coverage=coverage,
                inspections=inspections,
            ),
        )
