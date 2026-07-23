"""
Reasoning Builder

The Builder organizes reasoning.

The Builder assembles constitutional reasoning objects into coherent
Reasoning Registries.

Builders organize.

Builders never reason.

Builders never validate.

Builders never render.

Builders prepare reasoning for disciplined evaluation.
"""

from collections.abc import Iterable

from app.core.reasoning.models import (
    Assumption,
    CoherenceAssessment,
    Conclusion,
    Counterargument,
    EvidenceAssessment,
    Inference,
    Premise,
    ReasoningRegistry,
    ReasoningReport,
)


def build_reasoning_registry(
    *,
    premises: Iterable[Premise] = (),
    assumptions: Iterable[Assumption] = (),
    evidence_assessments: Iterable[EvidenceAssessment] = (),
    counterarguments: Iterable[Counterargument] = (),
    inferences: Iterable[Inference] = (),
    conclusions: Iterable[Conclusion] = (),
    coherence_assessments: Iterable[CoherenceAssessment] = (),
    reports: Iterable[ReasoningReport] = (),
) -> ReasoningRegistry:
    """
    Assemble SentinelAI's reasoning state.

    Builder responsibilities:

    - Organize reasoning objects.
    - Preserve the supplied reasoning state.
    - Return one coherent Reasoning Registry.

    Builder non-responsibilities:

    - Deriving conclusions
    - Assessing evidence
    - Resolving contradictions
    - Performing coherence checks
    - Validation
    - Rendering
    - Persistence
    """

    return ReasoningRegistry(
        premises=list(premises),
        assumptions=list(assumptions),
        evidence_assessments=list(evidence_assessments),
        counterarguments=list(counterarguments),
        inferences=list(inferences),
        conclusions=list(conclusions),
        coherence_assessments=list(coherence_assessments),
        reports=list(reports),
    )


def build_empty_reasoning_registry() -> ReasoningRegistry:
    """
    Construct an empty but structurally valid Reasoning Registry.

    An empty registry means no reasoning objects have been supplied.
    It does not imply failure or incoherence.
    """

    return build_reasoning_registry()
