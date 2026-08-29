"""
Premise relationship assessment for SentinelAI reasoning.

This component evaluates the relationship between two
evidence-grounded Premises.

Relationship assessment does not:

- synthesize new propositions,
- form conclusions,
- calculate conclusion confidence,
- invent semantic relationships,
- or resolve unsupported ambiguity.

When a supported relationship cannot be established, the
assessor returns UNRESOLVED.
"""

from __future__ import annotations

from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)


class PremiseRelationshipAssessor:
    """
    Assess the bounded relationship between two Premises.

    Unsupported semantic relationships remain unresolved.
    """

    def __init__(
        self,
        *,
        semantic_evaluator=None,
        semantic_policy=None,
    ):
        self.semantic_evaluator = (
            semantic_evaluator
        )
        self.semantic_policy = (
            semantic_policy
        )

    def assess(
        self,
        *,
        source: Premise,
        target: Premise,
    ) -> PremiseRelationship:
        """
        Assess one directional premise relationship.

        Relationships are asserted only when an explicit
        supported rule establishes them.
        """

        source_domains = set(
            source.domain_ids
        )

        target_domains = set(
            target.domain_ids
        )

        if (
            source_domains
            and target_domains
            and source_domains.isdisjoint(
                target_domains
            )
        ):
            return PremiseRelationship(
                source_premise_id=(
                    source.premise_id
                ),
                target_premise_id=(
                    target.premise_id
                ),
                kind=(
                    PremiseRelationshipKind.INDEPENDENT
                ),
                basis=(
                    "The premises are grounded in "
                    "distinct known domains with no "
                    "shared domain identifier."
                ),
                confidence=0.8,
            )
        
        if (
            self.semantic_evaluator
            is not None
            and self.semantic_policy
            is not None
        ):
            assessment = (
                self.semantic_evaluator.evaluate(
                    source=source,
                    target=target,
                )
            )

            return self.semantic_policy.promote(
                source=source,
                target=target,
                assessment=assessment,
            )


        return PremiseRelationship(
            source_premise_id=(
                source.premise_id
            ),
            target_premise_id=(
                target.premise_id
            ),
            kind=(
                PremiseRelationshipKind.UNRESOLVED
            ),
            basis=(
                "The available premises do not provide "
                "enough supported information to establish "
                "a semantic relationship."
            ),
            confidence=0.0,
        )
