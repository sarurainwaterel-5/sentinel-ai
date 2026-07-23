"""
Reasoning Language

Reasoning is the disciplined process of deriving justified conclusions
from earned understanding while remaining accountable to reality.

This module defines the canonical vocabulary governing SentinelAI's
Reasoning subsystem.
"""

from typing import Final, Literal


ConclusionStatus = Literal[
    "supported",
    "provisional",
    "unsupported",
    "inconclusive",
]

EvidencePosition = Literal[
    "supports",
    "contradicts",
    "neutral",
    "insufficient",
]

CoherenceStatus = Literal[
    "coherent",
    "partially_coherent",
    "incoherent",
    "unresolved",
]


REASONING_DEFINITION: Final[str] = (
    "Reasoning is the disciplined process of deriving the most responsible "
    "conclusion from available understanding while remaining accountable "
    "to reality."
)

REASONING_LAW: Final[str] = (
    "Reasoning supports judgment. Reasoning does not replace judgment."
)

COHERENCE_DEFINITION: Final[str] = (
    "Coherence is the degree to which evidence, principles, assumptions, "
    "understandings, and conclusions remain mutually consistent."
)

COHERENCE_CHECK_DEFINITION: Final[str] = (
    "A Coherence Check examines whether current cognitive objects can remain "
    "simultaneously consistent without concealing contradiction."
)

PREMISE_DEFINITION: Final[str] = (
    "A Premise is an explicit proposition used as a foundation for reasoning."
)

ASSUMPTION_DEFINITION: Final[str] = (
    "An Assumption is a proposition accepted provisionally when direct "
    "support is incomplete or unavailable."
)

INFERENCE_DEFINITION: Final[str] = (
    "An Inference is a structured connection showing how a conclusion follows "
    "from premises, evidence, and applicable principles."
)

EVIDENCE_ASSESSMENT_DEFINITION: Final[str] = (
    "An Evidence Assessment evaluates whether evidence supports, contradicts, "
    "remains neutral toward, or is insufficient for a proposition."
)

COUNTERARGUMENT_DEFINITION: Final[str] = (
    "A Counterargument presents a reasonable challenge to a proposed "
    "conclusion using evidence, principles, assumptions, or alternative "
    "interpretations."
)

JUSTIFICATION_DEFINITION: Final[str] = (
    "A Justification explains why a conclusion responsibly follows from the "
    "available premises, evidence, principles, and coherence assessment."
)

CONCLUSION_DEFINITION: Final[str] = (
    "A Conclusion is a revisable judgment derived from available "
    "understanding rather than a declaration of absolute fact."
)

REASONING_REPORT_DEFINITION: Final[str] = (
    "A Reasoning Report communicates premises, assumptions, evidence "
    "assessments, counterarguments, coherence, uncertainty, and conclusion."
)

UNCERTAINTY_DEFINITION: Final[str] = (
    "Uncertainty represents the limits of what available evidence and "
    "understanding can responsibly support."
)

CONFIDENCE_DEFINITION: Final[str] = (
    "Confidence expresses the strength of support for a conclusion without "
    "converting probability into certainty."
)


CANONICAL_REASONING_TERMS: Final[dict[str, str]] = {
    "reasoning": REASONING_DEFINITION,
    "premise": PREMISE_DEFINITION,
    "assumption": ASSUMPTION_DEFINITION,
    "inference": INFERENCE_DEFINITION,
    "evidence_assessment": EVIDENCE_ASSESSMENT_DEFINITION,
    "counterargument": COUNTERARGUMENT_DEFINITION,
    "justification": JUSTIFICATION_DEFINITION,
    "conclusion": CONCLUSION_DEFINITION,
    "reasoning_report": REASONING_REPORT_DEFINITION,
    "coherence": COHERENCE_DEFINITION,
    "coherence_check": COHERENCE_CHECK_DEFINITION,
    "uncertainty": UNCERTAINTY_DEFINITION,
    "confidence": CONFIDENCE_DEFINITION,
}
