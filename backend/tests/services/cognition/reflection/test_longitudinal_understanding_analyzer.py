"""
Contract 021 — Longitudinal Understanding Analysis.

This analyzer summarizes an entire explicit Understanding lineage from
already-assessed transitions.

It may establish:

- lineage root,
- terminal/current state,
- ordered Understanding states,
- transition count,
- observed evolution sequence,
- supported transition count,
- conflicted transition count,
- overall lineage assessment.

It may not:

- infer motives,
- invent causal explanations,
- rewrite lineage,
- reinterpret edge assessments,
- perform Reflection,
- generate Recommendations,
- narrate improvement or regression.

The analyzer summarizes assessed history.

It does not manufacture a story.
"""

from app.core.cognition.models import Understanding

from app.services.cognition.reflection.lineage_evolution_assessor import (
    LineageEvolutionAssessor,
)

from app.services.cognition.reflection.longitudinal_understanding_analyzer import (
    LongitudinalLineageStatus,
    LongitudinalUnderstandingAnalyzer,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionAnalyzer,
    UnderstandingEvolutionKind,
)

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineage,
    UnderstandingLineageEdge,
    UnderstandingLineageKind,
)


def make_understanding(
    *,
    understanding_id: str,
    explanation: str,
    evidence_ids: list[str],
    confidence: float,
) -> Understanding:
    return Understanding(
        understanding_id=understanding_id,
        title="Reflection comparability doctrine",
        explanation=explanation,
        domain_ids=["cognition"],
        evidence_ids=evidence_ids,
        confidence=confidence,
    )


def make_analyzer() -> LongitudinalUnderstandingAnalyzer:
    return LongitudinalUnderstandingAnalyzer(
        lineage_assessor=LineageEvolutionAssessor(
            evolution_analyzer=UnderstandingEvolutionAnalyzer()
        )
    )


def test_single_chain_produces_ordered_longitudinal_summary():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-1", "evidence-2"],
        confidence=0.85,
    )

    v3 = make_understanding(
        understanding_id="understanding-v3",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
            "evidence-3",
        ],
        confidence=0.95,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
            "understanding-v3": v3,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v2",
                later_understanding_id="understanding-v3",
                kind=UnderstandingLineageKind.STRENGTHENED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.root_understanding_id == (
        "understanding-v1"
    )

    assert result.current_understanding_id == (
        "understanding-v3"
    )

    assert result.ordered_understanding_ids == [
        "understanding-v1",
        "understanding-v2",
        "understanding-v3",
    ]

    assert result.transition_count == 2


def test_observed_evolution_sequence_is_preserved():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-1", "evidence-2"],
        confidence=0.85,
    )

    v3 = make_understanding(
        understanding_id="understanding-v3",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=[
            "evidence-1",
            "evidence-2",
            "evidence-3",
        ],
        confidence=0.95,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
            "understanding-v3": v3,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v2",
                later_understanding_id="understanding-v3",
                kind=UnderstandingLineageKind.STRENGTHENED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.observed_evolution_sequence == [
        UnderstandingEvolutionKind.REVISED,
        UnderstandingEvolutionKind.STRENGTHENED,
    ]


def test_fully_supported_lineage_is_supported():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-1", "evidence-2"],
        confidence=0.85,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.supported_transition_count == 1
    assert result.conflicted_transition_count == 0

    assert (
        result.status
        == LongitudinalLineageStatus.SUPPORTED
    )


def test_partially_conflicted_lineage_preserves_supported_transitions():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Universal comparability is required.",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-1", "evidence-2"],
        confidence=0.85,
    )

    v3 = make_understanding(
        understanding_id="understanding-v3",
        explanation="Cohort comparability is sufficient.",
        evidence_ids=["evidence-1"],
        confidence=0.50,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
            "understanding-v3": v3,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v2",
                later_understanding_id="understanding-v3",
                kind=UnderstandingLineageKind.STRENGTHENED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.supported_transition_count == 1
    assert result.conflicted_transition_count == 1

    assert (
        result.status
        == LongitudinalLineageStatus.PARTIALLY_CONFLICTED
    )

    assert result.transition_assessments[0].supported is True
    assert result.transition_assessments[1].supported is False


def test_one_conflict_does_not_invalidate_whole_lineage():
    """
    A conflicted transition remains isolated to that transition.
    """

    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Meaning A",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Meaning B",
        evidence_ids=["evidence-2"],
        confidence=0.80,
    )

    v3 = make_understanding(
        understanding_id="understanding-v3",
        explanation="Meaning B",
        evidence_ids=["evidence-2", "evidence-3"],
        confidence=0.90,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
            "understanding-v3": v3,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v2",
                later_understanding_id="understanding-v3",
                kind=UnderstandingLineageKind.WEAKENED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.transition_count == 2
    assert result.supported_transition_count == 1
    assert result.conflicted_transition_count == 1

    assert (
        result.status
        == LongitudinalLineageStatus.PARTIALLY_CONFLICTED
    )


def test_empty_lineage_produces_empty_summary():
    lineage = UnderstandingLineage(
        understandings={},
        edges=[],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.root_understanding_id is None
    assert result.current_understanding_id is None
    assert result.ordered_understanding_ids == []
    assert result.transition_count == 0
    assert result.transition_assessments == []

    assert (
        result.status
        == LongitudinalLineageStatus.EMPTY
    )


def test_single_understanding_lineage_has_no_transitions():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Stable understanding.",
        evidence_ids=["evidence-1"],
        confidence=0.80,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
        },
        edges=[],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.root_understanding_id == (
        "understanding-v1"
    )

    assert result.current_understanding_id == (
        "understanding-v1"
    )

    assert result.ordered_understanding_ids == [
        "understanding-v1"
    ]

    assert result.transition_count == 0

    assert (
        result.status
        == LongitudinalLineageStatus.STABLE_SINGLE_STATE
    )


def test_branching_lineage_is_not_silently_flattened():
    """
    A branching lineage does not provide one unambiguous lifecycle.
    """

    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Root",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2a = make_understanding(
        understanding_id="understanding-v2a",
        explanation="Branch A",
        evidence_ids=["evidence-2a"],
        confidence=0.80,
    )

    v2b = make_understanding(
        understanding_id="understanding-v2b",
        explanation="Branch B",
        evidence_ids=["evidence-2b"],
        confidence=0.80,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2a": v2a,
            "understanding-v2b": v2b,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2a",
                kind=UnderstandingLineageKind.REVISED,
            ),
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2b",
                kind=UnderstandingLineageKind.REVISED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert result.ordered_understanding_ids == []

    assert (
        result.status
        == LongitudinalLineageStatus.AMBIGUOUS
    )

    assert result.limitations


def test_multiple_roots_are_ambiguous():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Root one",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Root two",
        evidence_ids=["evidence-2"],
        confidence=0.80,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
        },
        edges=[],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assert (
        result.status
        == LongitudinalLineageStatus.AMBIGUOUS
    )

    assert result.limitations


def test_analyzer_preserves_transition_assessments():
    v1 = make_understanding(
        understanding_id="understanding-v1",
        explanation="Meaning A",
        evidence_ids=["evidence-1"],
        confidence=0.70,
    )

    v2 = make_understanding(
        understanding_id="understanding-v2",
        explanation="Meaning B",
        evidence_ids=["evidence-2"],
        confidence=0.80,
    )

    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": v1,
            "understanding-v2": v2,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
        ],
    )

    result = make_analyzer().analyze(
        lineage=lineage
    )

    assessment = result.transition_assessments[0]

    assert assessment.earlier_understanding_id == (
        "understanding-v1"
    )

    assert assessment.later_understanding_id == (
        "understanding-v2"
    )

    assert (
        assessment.declared_kind
        == UnderstandingLineageKind.REVISED
    )

    assert (
        assessment.observed_kind
        == UnderstandingEvolutionKind.REVISED
    )


def test_longitudinal_analyzer_has_no_narrative_or_execution_authority():
    analyzer = make_analyzer()

    forbidden = [
        "explain_why",
        "tell_story",
        "generate_narrative",
        "reflect",
        "generate_recommendations",
        "execute",
        "rewrite_lineage",
    ]

    for name in forbidden:
        assert not hasattr(
            analyzer,
            name,
        )
