"""
Deterministic coverage aggregation for SentinelAI verification.

This engine answers one question:

What portion of the requested verification operation was actually
completed?

It aggregates specialist VerificationInspection objects into one
VerificationCoverage result.

It does not:

- perform verification checks,
- interpret findings,
- calculate verification confidence,
- determine verification status,
- modify the verified subject.
"""

from __future__ import annotations

from app.services.cognition.verification.models import (
    VerificationCategory,
    VerificationCoverage,
    VerificationInspection,
    VerificationOutcome,
)


class VerificationCoverageEngine:
    """
    Aggregate completed specialist inspections into verification coverage.
    """

    @staticmethod
    def _deduplicate_categories(
        categories: list[VerificationCategory],
    ) -> list[VerificationCategory]:
        """
        Preserve category order while removing duplicates.
        """

        return list(
            dict.fromkeys(categories)
        )

    @staticmethod
    def _coverage_score(
        *,
        requested_count: int,
        completed_count: int,
    ) -> float:
        """
        Calculate the proportion of requested categories completed.
        """

        if requested_count == 0:
            return 0.0

        return round(
            min(
                completed_count / requested_count,
                1.0,
            ),
            3,
        )

    def assess(
        self,
        *,
        requested_categories: list[
            VerificationCategory
        ],
        inspections: list[
            VerificationInspection
        ],
    ) -> VerificationCoverage:
        """
        Produce one deterministic verification-coverage assessment.
        """

        requested = self._deduplicate_categories(
            requested_categories
        )

        completed = self._deduplicate_categories(
            [
                inspection.category
                for inspection in inspections
                if inspection.completed
                and inspection.category in requested
            ]
        )

        skipped = [
            category
            for category in requested
            if category not in completed
        ]

        checks = [
            check
            for inspection in inspections
            if inspection.completed
            for check in inspection.checks
        ]

        passed_count = sum(
            1
            for check in checks
            if check.outcome
            == VerificationOutcome.PASSED
        )

        conditional_count = sum(
            1
            for check in checks
            if check.outcome
            == VerificationOutcome.PASSED_WITH_CONDITIONS
        )

        failed_count = sum(
            1
            for check in checks
            if check.outcome
            == VerificationOutcome.FAILED
        )

        unverifiable_count = sum(
            1
            for check in checks
            if check.outcome
            == VerificationOutcome.NOT_VERIFIABLE
        )

        not_applicable_count = sum(
            1
            for check in checks
            if check.outcome
            == VerificationOutcome.NOT_APPLICABLE
        )

        return VerificationCoverage(
            requested_categories=requested,
            completed_categories=completed,
            skipped_categories=skipped,
            check_count=len(checks),
            passed_count=passed_count,
            conditional_count=conditional_count,
            failed_count=failed_count,
            unverifiable_count=unverifiable_count,
            not_applicable_count=not_applicable_count,
            coverage_score=self._coverage_score(
                requested_count=len(requested),
                completed_count=len(completed),
            ),
        )
