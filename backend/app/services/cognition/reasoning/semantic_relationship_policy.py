"""
Semantic relationship promotion policy for SentinelAI reasoning.

This component governs whether a semantic relationship assessment
may become an authoritative PremiseRelationship.

Generative interpretation is not automatically authoritative
cognition.
"""

from __future__ import annotations

from app.services.cognition.reasoning.models import (
    Premise,
    PremiseRelationship,
    PremiseRelationshipKind,
)

from app.services.cognition.reasoning.semantic_relationship_evaluator import (
    SemanticRelationshipAssessment,
)


class SemanticRelationshipPolicy:
    """
    Govern promotion of semantic relationship assessments.

    Assessments that do not satisfy the policy remain unresolved.
    """

    def __init__(
        self,
        *,
        minimum_confidence: float = 0.75,
    ):
        if not 0.0 <= minimum_confidence <= 1.0:
            raise ValueError(
                "minimum_confidence must be between "
                "0.0 and 1.0."
            )

        self.minimum_confidence = (
            minimum_confidence
        )

    def promote(
        self,
        *,
        source: Premise,
        target: Premise,
        assessment: SemanticRelationshipAssessment,
    ) -> PremiseRelationship:
        """
        Promote one admissible semantic assessment.

        Low-confidence assessments are explicitly reduced to
        UNRESOLVED rather than treated as authoritative.
        """

        if (
            assessment.confidence
            < self.minimum_confidence
        ):
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
                    "The semantic relationship assessment "
                    "did not meet the required classification "
                    "confidence threshold."
                ),
                confidence=0.0,
            )

        relationship_kind = (
            PremiseRelationshipKind(
                assessment.relationship
            )
        )

        return PremiseRelationship(
            source_premise_id=(
                source.premise_id
            ),
            target_premise_id=(
                target.premise_id
            ),
            kind=relationship_kind,
            basis=assessment.basis,
            confidence=assessment.confidence,
        )
