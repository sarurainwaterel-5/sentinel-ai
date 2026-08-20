"""
Contract 022 — Reflective Trend Synthesis.

Reflective Trend Synthesis converts an already-assessed longitudinal
Understanding history into bounded higher-order observations.

It may identify:

- continuity,
- reinforcement,
- revision,
- erosion,
- contradiction,
- mixed supported trends,
- unresolved history.

It may not:

- infer correctness,
- infer improvement or regression,
- invent causes,
- reinterpret conflicted transitions,
- rewrite historical cognition,
- generate Recommendations,
- execute actions.

Synthesis compresses supported history.

It does not manufacture meaning beyond the evidence.
"""

from app.services.cognition.reflection.lineage_evolution_assessor import (
    LineageEvolutionAssessment,
)

from app.services.cognition.reflection.longitudinal_understanding_analyzer import (
    LongitudinalLineageStatus,
    LongitudinalUnderstandingAnalysis,
)

from app.services.cognition.reflection.reflective_trend_synthesizer import (
    ReflectiveTrendKind,
    ReflectiveTrendSynthesizer,
)

from app.services.cognition.reflection.understanding_evolution_analyzer import (
    UnderstandingEvolutionKind,
)

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineageKind,
)


def make_assessment(
    *,
    earlier: str,
    later: str,
    declared: UnderstandingLineageKind,
    observed: UnderstandingEvolutionKind,
    supported: bool = True,
) -> LineageEvolutionAssessment:
    return LineageEvolutionAssessment(
        earlier_understanding_id=earlier,
        later_understanding_id=later,
        declared_kind=declared,
        observed_kind=observed,
        supported=supported,
        conflict=not supported,
        basis="Test transition assessment.",
    )


def make_analysis(
    *,
    assessments: list[LineageEvolutionAssessment],
    status: LongitudinalLineageStatus = (
        LongitudinalLineageStatus.SUPPORTED
    ),
) -> LongitudinalUnderstandingAnalysis:
    supported_count = sum(
        1
        for assessment in assessments
        if assessment.supported
    )

    conflicted_count = sum(
        1
        for assessment in assessments
        if assessment.conflict
    )

    ordered_ids: list[str] = []

    if assessments:
        ordered_ids.append(
            assessments[0].earlier_understanding_id
        )

        ordered_ids.extend(
            assessment.later_understanding_id
            for assessment in assessments
        )

    return LongitudinalUnderstandingAnalysis(
        root_understanding_id=(
            ordered_ids[0]
            if ordered_ids
            else None
        ),
        current_understanding_id=(
            ordered_ids[-1]
            if ordered_ids
            else None
        ),
        ordered_understanding_ids=ordered_ids,
        transition_count=len(assessments),
        transition_assessments=assessments,
        observed_evolution_sequence=[
            assessment.observed_kind
            for assessment in assessments
        ],
        supported_transition_count=supported_count,
        conflicted_transition_count=conflicted_count,
        status=status,
    )


def test_stable_transition_synthesizes_continuity():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STABLE,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.CONTINUITY
    )

    assert result.trends == [
        ReflectiveTrendKind.CONTINUITY
    ]


def test_strengthening_synthesizes_reinforcement():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.REINFORCEMENT
    )


def test_revision_synthesizes_revision():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.REVISED,
                observed=UnderstandingEvolutionKind.REVISED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.REVISION
    )


def test_weakening_synthesizes_erosion():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.WEAKENED,
                observed=UnderstandingEvolutionKind.WEAKENED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.EROSION
    )


def test_supported_contradiction_synthesizes_contradiction():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.CONTRADICTED,
                observed=UnderstandingEvolutionKind.CONTRADICTED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.CONTRADICTION
    )


def test_multiple_different_supported_trends_are_mixed():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.REVISED,
                observed=UnderstandingEvolutionKind.REVISED,
            ),
            make_assessment(
                earlier="understanding-v2",
                later="understanding-v3",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.MIXED
    )

    assert result.trends == [
        ReflectiveTrendKind.REVISION,
        ReflectiveTrendKind.REINFORCEMENT,
    ]


def test_repeated_same_trend_does_not_become_mixed():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
            make_assessment(
                earlier="understanding-v2",
                later="understanding-v3",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.REINFORCEMENT
    )

    assert result.trends == [
        ReflectiveTrendKind.REINFORCEMENT
    ]


def test_conflicted_transition_is_not_promoted_to_trend():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.WEAKENED,
                supported=False,
            ),
        ],
        status=(
            LongitudinalLineageStatus.CONFLICTED
        ),
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.UNRESOLVED
    )

    assert result.trends == []
    assert result.has_conflict is True
    assert result.limitations


def test_supported_history_survives_isolated_conflict():
    """
    A conflicted transition must not erase independently supported
    longitudinal evidence.
    """

    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.REVISED,
                observed=UnderstandingEvolutionKind.REVISED,
            ),
            make_assessment(
                earlier="understanding-v2",
                later="understanding-v3",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.WEAKENED,
                supported=False,
            ),
        ],
        status=(
            LongitudinalLineageStatus.PARTIALLY_CONFLICTED
        ),
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.REVISION
    )

    assert result.trends == [
        ReflectiveTrendKind.REVISION
    ]

    assert result.has_conflict is True
    assert result.limitations


def test_unresolved_observation_is_not_promoted_to_supported_trend():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.UNRESOLVED,
                supported=False,
            ),
        ],
        status=(
            LongitudinalLineageStatus.CONFLICTED
        ),
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.UNRESOLVED
    )

    assert result.trends == []


def test_empty_longitudinal_history_is_unresolved():
    analysis = LongitudinalUnderstandingAnalysis(
        status=LongitudinalLineageStatus.EMPTY
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.UNRESOLVED
    )

    assert result.trends == []
    assert result.limitations


def test_single_state_is_continuity_without_inventing_transition():
    analysis = LongitudinalUnderstandingAnalysis(
        root_understanding_id="understanding-v1",
        current_understanding_id="understanding-v1",
        ordered_understanding_ids=[
            "understanding-v1",
        ],
        transition_count=0,
        status=(
            LongitudinalLineageStatus.STABLE_SINGLE_STATE
        ),
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.CONTINUITY
    )

    assert result.trends == [
        ReflectiveTrendKind.CONTINUITY
    ]

    assert result.supporting_transition_count == 0


def test_ambiguous_lineage_is_unresolved():
    analysis = LongitudinalUnderstandingAnalysis(
        transition_count=2,
        status=LongitudinalLineageStatus.AMBIGUOUS,
        limitations=[
            "The lineage branches."
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.primary_trend == (
        ReflectiveTrendKind.UNRESOLVED
    )

    assert result.trends == []
    assert result.limitations


def test_synthesis_reports_supporting_transition_count():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
            make_assessment(
                earlier="understanding-v2",
                later="understanding-v3",
                declared=UnderstandingLineageKind.STRENGTHENED,
                observed=UnderstandingEvolutionKind.STRENGTHENED,
            ),
        ],
    )

    result = ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert result.supporting_transition_count == 2
    assert result.conflicted_transition_count == 0


def test_synthesizer_preserves_longitudinal_analysis():
    analysis = make_analysis(
        assessments=[
            make_assessment(
                earlier="understanding-v1",
                later="understanding-v2",
                declared=UnderstandingLineageKind.REVISED,
                observed=UnderstandingEvolutionKind.REVISED,
            ),
        ],
    )

    before = analysis.model_dump()

    ReflectiveTrendSynthesizer().synthesize(
        analysis=analysis
    )

    assert analysis.model_dump() == before


def test_synthesizer_has_no_causal_narrative_or_execution_authority():
    synthesizer = ReflectiveTrendSynthesizer()

    forbidden = [
        "determine_correctness",
        "determine_improvement",
        "determine_regression",
        "explain_cause",
        "generate_narrative",
        "rewrite_history",
        "generate_recommendations",
        "execute",
    ]

    for name in forbidden:
        assert not hasattr(
            synthesizer,
            name,
        )
