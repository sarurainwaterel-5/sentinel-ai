from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    EvidenceDisposition,
    EvidenceItem,
    EvidenceSource,
)

from app.services.cognition.reasoning.premise_extractor import (
    PremiseExtractor,
)


def _evidence(
    *,
    evidence_id: str,
    text: str,
    document_id: str,
    chunk_index: int,
) -> EvidenceItem:
    source = EvidenceSource(
        document_id=document_id,
        filename=f"{document_id}.md",
        chunk_index=chunk_index,
        score=0.90,
        text=text,
        metadata={
            "evidence_id": evidence_id,
        },
    )

    return EvidenceItem(
        statement=text,
        disposition=EvidenceDisposition.CONTEXTUAL,
        source=source,
        relevance_score=0.90,
        rationale="Relevant retrieved evidence.",
    )


def test_extracts_traceable_premises_from_evidence():
    evidence_one = _evidence(
        evidence_id="evidence-1",
        text=(
            "SentinelAI preserves retrieved source provenance "
            "before downstream reasoning occurs."
        ),
        document_id="doc-1",
        chunk_index=1,
    )

    evidence_two = _evidence(
        evidence_id="evidence-2",
        text=(
            "Reasoning conclusions remain inspectable through "
            "explicit evidence references."
        ),
        document_id="doc-2",
        chunk_index=2,
    )

    bundle = EvidenceBundle(
        question=(
            "How does SentinelAI preserve accountable reasoning?"
        ),
        contextual=[
            evidence_one,
            evidence_two,
        ],
        source_count=2,
        document_count=2,
        domain_count=1,
    )

    extractor = PremiseExtractor()

    premises = extractor.extract(bundle)

    assert len(premises) == 2

    assert premises[0].statement == (
        "SentinelAI preserves retrieved source provenance "
        "before downstream reasoning occurs."
    )
    assert premises[0].evidence_ids == [
        "evidence-1",
    ]

    assert premises[1].statement == (
        "Reasoning conclusions remain inspectable through "
        "explicit evidence references."
    )
    assert premises[1].evidence_ids == [
        "evidence-2",
    ]

    assert premises[0].premise_id != premises[1].premise_id


def test_unknown_evidence_does_not_become_premise():
    bundle = EvidenceBundle(
        question=(
            "Can unusable evidence support a reasoning premise?"
        ),
        supporting=[],
        conflicting=[],
        contextual=[],
        unknown=[
            EvidenceItem(
                statement="Unusable retrieved content.",
                disposition=EvidenceDisposition.UNKNOWN,
                source=EvidenceSource(
                    document_id="doc-unknown",
                    filename="unknown.pdf",
                    chunk_index=7,
                    text="",
                    score=0.0,
                    metadata={
                        "evidence_id": "evidence-unknown",
                    },
                ),
            ),
        ],
        gaps=[],
        source_count=1,
        document_count=1,
        domain_count=0,
    )

    extractor = PremiseExtractor()

    premises = extractor.extract(bundle)

    assert premises == []

def test_equivalent_evidence_does_not_create_duplicate_premises():
    evidence_one = _evidence(
        evidence_id="evidence-1",
        text=(
            "SentinelAI preserves evidence provenance "
            "throughout reasoning."
        ),
        document_id="doc-1",
        chunk_index=1,
    )

    evidence_two = _evidence(
        evidence_id="evidence-2",
        text=(
            "SentinelAI preserves evidence provenance "
            "throughout reasoning."
        ),
        document_id="doc-2",
        chunk_index=3,
    )

    bundle = EvidenceBundle(
        question=(
            "How does SentinelAI preserve accountable reasoning?"
        ),
        contextual=[
            evidence_one,
            evidence_two,
        ],
        source_count=2,
        document_count=2,
        domain_count=1,
    )

    extractor = PremiseExtractor()

    premises = extractor.extract(bundle)

    assert len(premises) == 1

    assert premises[0].statement == (
        "SentinelAI preserves evidence provenance "
        "throughout reasoning."
    )

    assert premises[0].evidence_ids == [
        "evidence-1",
        "evidence-2",
    ]
