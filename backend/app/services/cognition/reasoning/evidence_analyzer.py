"""
Evidence analysis for SentinelAI's reasoning layer.

The analyzer transforms retrieval results into stable, inspectable
reasoning contracts without drawing a final conclusion.

Sprint 14 begins conservatively:

- retrieved chunks become EvidenceSource records,
- source provenance is preserved,
- corpus-level counts are calculated,
- evidence is initially classified as contextual,
- malformed or empty retrieval results become unknown evidence.

Later reasoning slices can enrich disposition classification with
claim extraction, agreement detection, and contradiction analysis.
"""

from __future__ import annotations

from typing import Any

from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    EvidenceDisposition,
    EvidenceItem,
    EvidenceSource,
)


class EvidenceAnalyzer:
    """
    Convert raw retrieval results into an inspectable EvidenceBundle.

    This boundary prevents downstream reasoning services from depending
    directly on Qdrant client models.
    """

    @staticmethod
    def _normalize_score(value: Any) -> float:
        try:
            score = float(value)
        except (TypeError, ValueError):
            return 0.0

        return round(max(0.0, min(score, 1.0)), 4)

    @staticmethod
    def _clean_optional_text(value: Any) -> str | None:
        if value is None:
            return None

        cleaned = str(value).strip()

        if not cleaned:
            return None

        if cleaned.casefold() == "string":
            return None

        return cleaned

    @classmethod
    def _build_source(cls, point) -> EvidenceSource:
        payload = point.payload or {}

        promoted_fields = {
            "document_id",
            "filename",
            "file_hash",
            "module",
            "topic",
            "collection",
            "organization_id",
            "chunk_index",
            "text",
            "status",
            "description",
            "embedding_model",
        }

        metadata = {
            key: value
            for key, value in payload.items()
            if key not in promoted_fields
        }

        if payload.get("embedding_model") is not None:
            metadata["embedding_model"] = payload.get(
                "embedding_model"
            )

        return EvidenceSource(
            document_id=cls._clean_optional_text(
                payload.get("document_id")
            ),
            filename=cls._clean_optional_text(
                payload.get("filename")
            ),
            file_hash=cls._clean_optional_text(
                payload.get("file_hash")
            ),
            module=cls._clean_optional_text(
                payload.get("module")
            ),
            topic=cls._clean_optional_text(
                payload.get("topic")
            ),
            collection=cls._clean_optional_text(
                payload.get("collection")
            ),
            organization_id=cls._clean_optional_text(
                payload.get("organization_id")
            ),
            chunk_index=payload.get("chunk_index"),
            score=cls._normalize_score(
                getattr(point, "score", 0.0)
            ),
            text=str(payload.get("text") or "").strip(),
            status=cls._clean_optional_text(
                payload.get("status")
            ),
            description=cls._clean_optional_text(
                payload.get("description")
            ),
            metadata=metadata,
        )

    @staticmethod
    def _source_identity(
        source: EvidenceSource,
        index: int,
    ) -> str:
        document_identity = (
            source.document_id
            or source.file_hash
            or source.filename
            or "unknown-document"
        )

        chunk_identity = (
            source.chunk_index
            if source.chunk_index is not None
            else index
        )

        return f"{document_identity}:{chunk_identity}"

    @staticmethod
    def _source_statement(
        source: EvidenceSource,
    ) -> str:
        if not source.text:
            return (
                "The retrieved source did not contain "
                "extractable evidence text."
            )

        return source.text

    @staticmethod
    def _initial_disposition(
        source: EvidenceSource,
    ) -> EvidenceDisposition:
        if not source.text:
            return EvidenceDisposition.UNKNOWN

        return EvidenceDisposition.CONTEXTUAL

    @classmethod
    def _build_item(
        cls,
        point,
        index: int,
    ) -> EvidenceItem:
        source = cls._build_source(point)
        disposition = cls._initial_disposition(source)

        if disposition == EvidenceDisposition.UNKNOWN:
            rationale = (
                "The retrieval result preserved provenance but did not "
                "contain usable evidence text."
            )
        else:
            rationale = (
                "The source is relevant retrieval context. Its role as "
                "supporting or conflicting evidence has not yet been "
                "established."
            )

        item = EvidenceItem(
            statement=cls._source_statement(source),
            disposition=disposition,
            source=source,
            relevance_score=source.score,
            rationale=rationale,
        )

        item.source.metadata["evidence_id"] = cls._source_identity(
            source,
            index,
        )

        return item

    @staticmethod
    def _document_count(
        items: list[EvidenceItem],
    ) -> int:
        identities = {
            (
                item.source.document_id
                or item.source.file_hash
                or item.source.filename
            )
            for item in items
            if (
                item.source.document_id
                or item.source.file_hash
                or item.source.filename
            )
        }

        return len(identities)

    @staticmethod
    def _domain_count(
        items: list[EvidenceItem],
    ) -> int:
        domains = {
            item.source.module.casefold()
            for item in items
            if item.source.module
        }

        return len(domains)

    @staticmethod
    def _score_summary(
        items: list[EvidenceItem],
    ) -> dict[str, float]:
        scores = [
            item.relevance_score
            for item in items
        ]

        if not scores:
            return {
                "minimum_score": 0.0,
                "maximum_score": 0.0,
                "average_score": 0.0,
            }

        return {
            "minimum_score": round(min(scores), 4),
            "maximum_score": round(max(scores), 4),
            "average_score": round(
                sum(scores) / len(scores),
                4,
            ),
        }

    def analyze(
        self,
        *,
        question: str,
        chunks: list,
        metadata: dict[str, Any] | None = None,
    ) -> EvidenceBundle:
        """
        Analyze retrieved chunks without producing a conclusion.

        All usable evidence begins as contextual. Supporting and
        conflicting classifications belong to later analysis stages
        because those labels require an explicit claim or hypothesis.
        """

        items = [
            self._build_item(point, index)
            for index, point in enumerate(
                chunks,
                start=1,
            )
        ]

        contextual = [
            item
            for item in items
            if (
                item.disposition
                == EvidenceDisposition.CONTEXTUAL
            )
        ]

        unknown = [
            item
            for item in items
            if (
                item.disposition
                == EvidenceDisposition.UNKNOWN
            )
        ]

        bundle_metadata = dict(metadata or {})
        bundle_metadata.update(
            self._score_summary(items)
        )
        bundle_metadata["analysis_stage"] = (
            "retrieval_normalization"
        )

        return EvidenceBundle(
            question=question,
            contextual=contextual,
            unknown=unknown,
            source_count=len(items),
            document_count=self._document_count(items),
            domain_count=self._domain_count(items),
            metadata=bundle_metadata,
        )

