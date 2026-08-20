"""
Contract 019 — Understanding Lineage.

Understanding Lineage represents explicit historical relationships
between authoritative Understanding states.

It may establish:

- predecessor and successor relationships,
- revision lineage,
- strengthening lineage,
- weakening lineage,
- contradiction lineage,
- chronological lineage chains.

It may not:

- infer relationships from similar prose,
- infer relationships from shared titles,
- modify Understanding objects,
- classify evolution independently,
- perform Reflection,
- generate Recommendations.

Lineage must be declared.

Similarity is not lineage.
"""

import pytest

from app.core.cognition.models import Understanding

from app.services.cognition.reflection.understanding_lineage import (
    UnderstandingLineage,
    UnderstandingLineageEdge,
    UnderstandingLineageKind,
    UnderstandingLineageValidationError,
)


def make_understanding(
    *,
    understanding_id: str,
    title: str = "Evidence-grounded cognition",
) -> Understanding:
    return Understanding(
        understanding_id=understanding_id,
        title=title,
        explanation=(
            f"Authoritative state for {understanding_id}."
        ),
        domain_ids=["engineering"],
        evidence_ids=[
            f"evidence-{understanding_id}",
        ],
        confidence=0.80,
    )


def test_explicit_revision_edge_connects_understandings():
    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": make_understanding(
                understanding_id="understanding-v1",
            ),
            "understanding-v2": make_understanding(
                understanding_id="understanding-v2",
            ),
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
        ],
    )

    assert lineage.successors(
        "understanding-v1"
    ) == [
        "understanding-v2"
    ]

    assert lineage.predecessors(
        "understanding-v2"
    ) == [
        "understanding-v1"
    ]


def test_lineage_preserves_declared_relationship_kind():
    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": make_understanding(
                understanding_id="understanding-v1",
            ),
            "understanding-v2": make_understanding(
                understanding_id="understanding-v2",
            ),
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.STRENGTHENED,
            ),
        ],
    )

    edge = lineage.edges[0]

    assert (
        edge.kind
        == UnderstandingLineageKind.STRENGTHENED
    )


def test_lineage_builds_ordered_chain():
    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": make_understanding(
                understanding_id="understanding-v1",
            ),
            "understanding-v2": make_understanding(
                understanding_id="understanding-v2",
            ),
            "understanding-v3": make_understanding(
                understanding_id="understanding-v3",
            ),
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

    assert lineage.chain_from(
        "understanding-v1"
    ) == [
        "understanding-v1",
        "understanding-v2",
        "understanding-v3",
    ]


def test_unknown_earlier_understanding_is_rejected():
    with pytest.raises(
        UnderstandingLineageValidationError,
        match="understanding-missing",
    ):
        UnderstandingLineage(
            understandings={
                "understanding-v2": make_understanding(
                    understanding_id="understanding-v2",
                ),
            },
            edges=[
                UnderstandingLineageEdge(
                    earlier_understanding_id=(
                        "understanding-missing"
                    ),
                    later_understanding_id=(
                        "understanding-v2"
                    ),
                    kind=UnderstandingLineageKind.REVISED,
                ),
            ],
        )


def test_unknown_later_understanding_is_rejected():
    with pytest.raises(
        UnderstandingLineageValidationError,
        match="understanding-missing",
    ):
        UnderstandingLineage(
            understandings={
                "understanding-v1": make_understanding(
                    understanding_id="understanding-v1",
                ),
            },
            edges=[
                UnderstandingLineageEdge(
                    earlier_understanding_id=(
                        "understanding-v1"
                    ),
                    later_understanding_id=(
                        "understanding-missing"
                    ),
                    kind=UnderstandingLineageKind.REVISED,
                ),
            ],
        )


def test_self_referential_lineage_is_rejected():
    with pytest.raises(
        UnderstandingLineageValidationError,
        match="itself",
    ):
        UnderstandingLineage(
            understandings={
                "understanding-v1": make_understanding(
                    understanding_id="understanding-v1",
                ),
            },
            edges=[
                UnderstandingLineageEdge(
                    earlier_understanding_id=(
                        "understanding-v1"
                    ),
                    later_understanding_id=(
                        "understanding-v1"
                    ),
                    kind=UnderstandingLineageKind.REVISED,
                ),
            ],
        )


def test_duplicate_lineage_edge_is_rejected():
    edge = UnderstandingLineageEdge(
        earlier_understanding_id="understanding-v1",
        later_understanding_id="understanding-v2",
        kind=UnderstandingLineageKind.REVISED,
    )

    with pytest.raises(
        UnderstandingLineageValidationError,
        match="Duplicate",
    ):
        UnderstandingLineage(
            understandings={
                "understanding-v1": make_understanding(
                    understanding_id="understanding-v1",
                ),
                "understanding-v2": make_understanding(
                    understanding_id="understanding-v2",
                ),
            },
            edges=[
                edge,
                edge.model_copy(),
            ],
        )


def test_cycle_is_rejected():
    with pytest.raises(
        UnderstandingLineageValidationError,
        match="cycle",
    ):
        UnderstandingLineage(
            understandings={
                "understanding-v1": make_understanding(
                    understanding_id="understanding-v1",
                ),
                "understanding-v2": make_understanding(
                    understanding_id="understanding-v2",
                ),
            },
            edges=[
                UnderstandingLineageEdge(
                    earlier_understanding_id="understanding-v1",
                    later_understanding_id="understanding-v2",
                    kind=UnderstandingLineageKind.REVISED,
                ),
                UnderstandingLineageEdge(
                    earlier_understanding_id="understanding-v2",
                    later_understanding_id="understanding-v1",
                    kind=UnderstandingLineageKind.REVISED,
                ),
            ],
        )


def test_similar_titles_do_not_create_implicit_lineage():
    lineage = UnderstandingLineage(
        understandings={
            "understanding-v1": make_understanding(
                understanding_id="understanding-v1",
                title="Same title",
            ),
            "understanding-v2": make_understanding(
                understanding_id="understanding-v2",
                title="Same title",
            ),
        },
        edges=[],
    )

    assert lineage.successors(
        "understanding-v1"
    ) == []

    assert lineage.predecessors(
        "understanding-v2"
    ) == []


def test_lineage_does_not_modify_understandings():
    earlier = make_understanding(
        understanding_id="understanding-v1",
    )

    later = make_understanding(
        understanding_id="understanding-v2",
    )

    earlier_before = earlier.to_dict()
    later_before = later.to_dict()

    UnderstandingLineage(
        understandings={
            "understanding-v1": earlier,
            "understanding-v2": later,
        },
        edges=[
            UnderstandingLineageEdge(
                earlier_understanding_id="understanding-v1",
                later_understanding_id="understanding-v2",
                kind=UnderstandingLineageKind.REVISED,
            ),
        ],
    )

    assert earlier.to_dict() == earlier_before
    assert later.to_dict() == later_before


def test_lineage_has_no_reflection_or_execution_authority():
    lineage = UnderstandingLineage(
        understandings={},
        edges=[],
    )

    forbidden = [
        "reflect",
        "generate_insights",
        "generate_recommendations",
        "execute",
        "rewrite_understanding",
        "classify_evolution",
    ]

    for name in forbidden:
        assert not hasattr(
            lineage,
            name,
        )
