"""
Contract tests for constitutional evaluation of SentinelAI Reflection.

Constitutional coherence determines whether an already-produced
Reflection is admissible under SentinelAI's governing principles.

It does not:

- generate Reflection,
- alter Reflection confidence,
- repair Reflection,
- rewrite Patterns,
- rewrite Insights,
- rewrite Recommendations,
- execute Recommendations.

Confidence measures support.

Constitution governs admissibility.
"""

from copy import deepcopy

from app.services.cognition.reflection.models import (
    ReflectionConfidence,
    ReflectionConfidenceLevel,
    ReflectionInsight,
    ReflectionPattern,
    ReflectionPatternKind,
    ReflectionRecommendation,
    ReflectionRecommendationKind,
    ReflectionResult,
    ReflectionStatus,
)

from app.services.cognition.reflection.reflection_coherence_evaluator import (
    ReflectionCoherenceEvaluator,
)


def make_reflection(
    *,
    confidence_score: float = 0.90,
) -> ReflectionResult:
    pattern = ReflectionPattern(
        pattern_id="pattern-1",
        kind=ReflectionPatternKind.RECURRENCE,
        title="Recurring engineering learning",
        description=(
            "Engineering recurs across accumulated learning."
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
    )

    insight = ReflectionInsight(
        insight_id="insight-1",
        title="Engineering remains recurrent",
        explanation=(
            "The established Pattern shows recurring "
            "engineering learning."
        ),
        pattern_ids=[
            "pattern-1",
        ],
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        evidence_ids=[
            "evidence-1",
        ],
        domain_ids=[
            "engineering",
        ],
        confidence=confidence_score,
    )

    recommendation = ReflectionRecommendation(
        recommendation_id="recommendation-1",
        kind=ReflectionRecommendationKind.STRENGTHEN,
        title="Continue engineering learning",
        description=(
            "Continue examining the established learning area."
        ),
        insight_ids=[
            "insight-1",
        ],
        pattern_ids=[
            "pattern-1",
        ],
        domain_ids=[
            "engineering",
        ],
        priority=1,
        requires_human_approval=True,
    )

    return ReflectionResult(
        title="Engineering reflection",
        summary="Reflection completed.",
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        patterns=[
            pattern,
        ],
        insights=[
            insight,
        ],
        recommendations=[
            recommendation,
        ],
        confidence=ReflectionConfidence(
            score=confidence_score,
            level=(
                ReflectionConfidenceLevel.HIGH
                if confidence_score >= 0.75
                else ReflectionConfidenceLevel.LOW
            ),
            basis="Reflective support was assessed.",
            factors=[],
            uncertainty=[],
        ),
        reflection_trace=[
            "History analyzed.",
            "Patterns discovered.",
            "Insights generated.",
            "Recommendations generated.",
        ],
        status=ReflectionStatus.COMPLETE,
    )


class StubCoherenceEngine:
    """
    Controlled constitutional authority for contract testing.
    """

    def __init__(
        self,
        *,
        coherent: bool,
        constitutional_score: float,
        conflicts: list[str] | None = None,
    ):
        self.coherent = coherent
        self.constitutional_score = constitutional_score
        self.conflicts = conflicts or []
        self.calls = 0

    def evaluate(
        self,
        question,
        identity_context,
        knowledge_context=None,
    ):
        self.calls += 1

        return {
            "coherent": self.coherent,
            "constitutional_score": self.constitutional_score,
            "articles_consulted": [],
            "conflicts": self.conflicts,
            "recommendations": [],
        }


def test_coherent_reflection_is_admissible():
    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=True,
            constitutional_score=1.0,
        )
    )

    result = evaluator.evaluate(
        reflection=make_reflection(),
        constitutional_context=(
            "Reflection remains accountable to reality."
        ),
    )

    assert result.coherent is True
    assert result.admissible is True
    assert result.constitutional_score == 1.0


def test_incoherent_reflection_is_inadmissible():
    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=False,
            constitutional_score=0.20,
            conflicts=[
                "Reflection exceeds constitutional authority.",
            ],
        )
    )

    result = evaluator.evaluate(
        reflection=make_reflection(),
        constitutional_context=(
            "Reflection possesses no execution authority."
        ),
    )

    assert result.coherent is False
    assert result.admissible is False
    assert result.conflicts


def test_high_confidence_cannot_override_incoherence():
    """
    Confidence and constitutional admissibility are not averaged.
    """

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=False,
            constitutional_score=0.10,
            conflicts=[
                "Constitutional conflict detected.",
            ],
        )
    )

    result = evaluator.evaluate(
        reflection=make_reflection(
            confidence_score=0.99,
        ),
        constitutional_context=(
            "Constitution governs admissibility."
        ),
    )

    assert result.reflection_confidence == 0.99
    assert result.coherent is False
    assert result.admissible is False


def test_low_confidence_does_not_make_coherent_reflection_incoherent():
    """
    Weak support and constitutional incoherence are different judgments.
    """

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=True,
            constitutional_score=1.0,
        )
    )

    result = evaluator.evaluate(
        reflection=make_reflection(
            confidence_score=0.30,
        ),
        constitutional_context=(
            "Reflection remains revisable."
        ),
    )

    assert result.reflection_confidence == 0.30
    assert result.coherent is True
    assert result.admissible is True


def test_constitutional_evaluation_does_not_modify_reflection():
    reflection = make_reflection()
    before = deepcopy(reflection)

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=False,
            constitutional_score=0.25,
            conflicts=[
                "Conflict detected.",
            ],
        )
    )

    evaluator.evaluate(
        reflection=reflection,
        constitutional_context=(
            "Historical cognition remains immutable."
        ),
    )

    assert reflection == before


def test_coherence_does_not_rewrite_confidence():
    reflection = make_reflection(
        confidence_score=0.91,
    )

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=False,
            constitutional_score=0.15,
        )
    )

    result = evaluator.evaluate(
        reflection=reflection,
        constitutional_context=(
            "Constitutional evaluation is independent."
        ),
    )

    assert reflection.confidence.score == 0.91
    assert result.reflection_confidence == 0.91


def test_admissibility_does_not_grant_execution_authority():
    reflection = make_reflection()

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=True,
            constitutional_score=1.0,
        )
    )

    result = evaluator.evaluate(
        reflection=reflection,
        constitutional_context=(
            "Recommendations require human approval."
        ),
    )

    assert result.admissible is True

    assert (
        reflection.recommendations[0]
        .requires_human_approval
        is True
    )

    assert not hasattr(
        result,
        "execution_authorized",
    )


def test_constitutional_result_preserves_conflicts():
    conflicts = [
        "Recommendation exceeds reflective authority.",
        "Historical provenance is contradicted.",
    ]

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=StubCoherenceEngine(
            coherent=False,
            constitutional_score=0.20,
            conflicts=conflicts,
        )
    )

    result = evaluator.evaluate(
        reflection=make_reflection(),
        constitutional_context=(
            "Reflection must preserve disciplined authority."
        ),
    )

    assert result.conflicts == conflicts


def test_evaluator_invokes_constitutional_authority_once():
    authority = StubCoherenceEngine(
        coherent=True,
        constitutional_score=1.0,
    )

    evaluator = ReflectionCoherenceEvaluator(
        coherence_engine=authority
    )

    evaluator.evaluate(
        reflection=make_reflection(),
        constitutional_context=(
            "Reflection remains constitutionally governed."
        ),
    )

    assert authority.calls == 1
