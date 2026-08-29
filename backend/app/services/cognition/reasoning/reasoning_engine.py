"""
SentinelAI Evidence-Grounded Reasoning Engine.

The reasoning engine coordinates Sentinel's cognitive pipeline.

It does not retrieve evidence.
It does not call an LLM.
It does not invent conclusions.

Instead it orchestrates:

Evidence
↓

Premises
↓

Premise Relationships
↓

Synthesized Propositions
↓

Inference
↓

Confidence
↓

Structured Conclusion
"""

from __future__ import annotations

from app.services.cognition.reasoning.models import (
    ReasoningConclusion,
    ReasoningResult,
)

from app.services.cognition.reasoning.evidence_analyzer import (
    EvidenceAnalyzer,
)

from app.services.cognition.reasoning.inference_engine import (
    InferenceEngine,
)

from app.services.cognition.reasoning.confidence_engine import (
    ConfidenceEngine,
)

from app.services.cognition.reasoning.premise_extractor import (
    PremiseExtractor,
)

from app.services.cognition.reasoning.premise_relationship_assessor import (
    PremiseRelationshipAssessor,
)

from app.services.cognition.reasoning.proposition_synthesizer import (
    PropositionSynthesizer,
)


class ReasoningEngine:
    """
    Sentinel's cognitive orchestrator.

    This class coordinates reasoning but delegates every specialized
    cognitive task to dedicated reasoning services.
    """

    def __init__(self):
        self.evidence = EvidenceAnalyzer()
        self.premises = PremiseExtractor()
        self.relationships = PremiseRelationshipAssessor()
        self.propositions = None
        self.inference = InferenceEngine()
        self.confidence = ConfidenceEngine()

    @staticmethod
    def _missing_information(
        *,
        strongest,
        evidence_bundle,
    ) -> list[str]:
        """
        Identify evidence that is absent but would materially
        improve the current judgment.

        Missing information is distinct from:

        - inference limitations, which constrain the current
          conclusion;
        - confidence uncertainty, which explains why confidence
          remains bounded.
        """

        missing: list[str] = [
            gap.description
            for gap in evidence_bundle.gaps
            if gap.description
        ]

        if (
            not missing
            and len(
                strongest.supporting_evidence_ids
            ) <= 1
        ):
            missing.append(
                "Additional independent corroborating evidence "
                "is needed to strengthen the current conclusion."
            )

        if (
            evidence_bundle.unknown
            and not any(
                "usable evidence" in item.casefold()
                for item in missing
            )
        ):
            missing.append(
                "Usable evidence is needed from sources that "
                "could not be evaluated."
            )

        return list(
            dict.fromkeys(missing)
        )

    def reason(
        self,
        *,
        question: str,
        chunks: list,
        metadata: dict | None = None,
    ) -> ReasoningResult:
        """
        Produce one complete reasoning operation.

        The resulting object is fully inspectable and contains no hidden
        reasoning process.
        """

        trace = []

        trace.append(
            "Retrieved relevant evidence."
        )

        evidence_bundle = self.evidence.analyze(
            question=question,
            chunks=chunks,
            metadata=metadata,
        )

        trace.append(
            "Organized evidence."
        )

        premises = self.premises.extract(
            evidence_bundle
        )

        trace.append(
            "Extracted reasoning premises."
        )

        premise_relationships = []

        for index, source in enumerate(premises):
            for target in premises[index + 1:]:
                relationship = self.relationships.assess(
                    source=source,
                    target=target,
                )

                if relationship is not None:
                    premise_relationships.append(
                        relationship
                    )

        trace.append(
            "Assessed premise relationships."
        )

        synthesized_propositions = []

        if self.propositions is not None:
            synthesized_propositions = (
                self.propositions.synthesize(
                    premises=premises,
                    relationships=premise_relationships,
                )
            )

            trace.append(
                "Synthesized propositions."
            )

        candidate_inferences = (
            self.inference.infer(
                evidence_bundle
            )
        )

        trace.append(
            "Generated candidate inferences."
        )

        if not candidate_inferences:
            trace.append(
                "No supported inference could be produced."
            )

            return ReasoningResult(
                question=question,
                evidence=evidence_bundle,
                premises=premises,
                premise_relationships=premise_relationships,
                synthesized_propositions=synthesized_propositions,
                inferences=[],
                conclusion=None,
                reasoning_trace=trace,
                status="insufficient_evidence",
            )

        strongest = candidate_inferences[0]

        confidence = self.confidence.assess(
            inference=strongest,
            evidence=evidence_bundle,
        )

        trace.append(
            "Calculated confidence."
        )

        conclusion = ReasoningConclusion(
            statement=strongest.statement,
            evidence_summary=(
                f"{len(strongest.supporting_evidence_ids)} "
                "supporting evidence item(s)."
            ),
            inference_summary=(
                "Conclusion selected from the "
                "highest-supported candidate inference."
            ),
            confidence=confidence,
            limitations=strongest.limitations,
            alternatives=[],
            missing_information=(
                self._missing_information(
                    strongest=strongest,
                    evidence_bundle=evidence_bundle,
                )
            ),
            recommended_next_step=(
                "Collect additional corroborating "
                "evidence if higher confidence is "
                "required."
            ),
        )

        trace.append(
            "Produced structured conclusion."
        )

        return ReasoningResult(
            question=question,
            evidence=evidence_bundle,
            premises=premises,
            premise_relationships=premise_relationships,
            synthesized_propositions=synthesized_propositions,
            inferences=candidate_inferences,
            conclusion=conclusion,
            reasoning_trace=trace,
            status="complete",
        )
