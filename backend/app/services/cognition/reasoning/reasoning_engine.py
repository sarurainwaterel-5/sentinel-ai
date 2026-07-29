"""
SentinelAI Evidence-Grounded Reasoning Engine.

The reasoning engine coordinates Sentinel's cognitive pipeline.

It does not retrieve evidence.
It does not call an LLM.
It does not invent conclusions.

Instead it orchestrates:

Evidence
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


class ReasoningEngine:
    """
    Sentinel's cognitive orchestrator.

    This class coordinates reasoning but delegates every specialized
    cognitive task to dedicated reasoning services.
    """

    def __init__(self):
        self.evidence = EvidenceAnalyzer()
        self.inference = InferenceEngine()
        self.confidence = ConfidenceEngine()

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
                inferences=[],
                conclusion=None,
                reasoning_trace=trace,
                status="insufficient_evidence",
            )

        strongest = candidate_inferences[0]

        confidence = (
            self.confidence.assess(
                inference=strongest,
                evidence=evidence_bundle,
            )
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
                confidence.uncertainty
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

            inferences=candidate_inferences,

            conclusion=conclusion,

            reasoning_trace=trace,

            status="complete",
        )
