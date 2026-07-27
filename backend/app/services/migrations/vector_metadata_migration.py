"""
Vector Metadata Migration

Reconciles canonical Postgres document metadata with SentinelAI's
Qdrant semantic memory.

Postgres remains the source of truth.

The migration:

- matches vectors by document_id first,
- falls back to file_hash,
- falls back to a unique filename for legacy payloads,
- patches payload metadata without removing existing fields,
- supports dry-run mode,
- remains safe to run repeatedly.
"""

from collections import Counter
from typing import Any

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)
from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.qdrant_service import (
    COLLECTION_NAME,
    client,
)


class VectorMetadataMigration:
    """Unify legacy Qdrant payloads with canonical document metadata."""

    def __init__(self, db: Session):
        self.repository = DocumentRepository(db)

    @staticmethod
    def _canonical_metadata(document) -> dict[str, Any]:
        return {
            "document_id": document.id,
            "filename": document.filename,
            "file_hash": document.file_hash,
            "module": document.module or "engineering",
            "topic": document.topic or "general",
            "collection": document.collection or "general",
            "organization_id": (
                document.organization_id or "default"
            ),
            "description": document.description,
            "embedding_model": document.embedding_model,
            "status": document.status or "indexed",
        }

    @staticmethod
    def _exact_filter(
        field_name: str,
        field_value: str,
    ) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key=field_name,
                    match=MatchValue(value=field_value),
                )
            ]
        )

    @staticmethod
    def _scroll_all(
        query_filter: Filter,
        batch_size: int = 256,
    ) -> list:
        points = []
        offset = None

        while True:
            batch, next_offset = client.scroll(
                collection_name=COLLECTION_NAME,
                scroll_filter=query_filter,
                limit=batch_size,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            points.extend(batch)

            if next_offset is None:
                break

            offset = next_offset

        return points

    def _find_points(
        self,
        document,
        filename_counts: Counter,
    ) -> tuple[list, str | None]:
        points = self._scroll_all(
            self._exact_filter(
                "document_id",
                document.id,
            )
        )

        if points:
            return points, "document_id"

        points = self._scroll_all(
            self._exact_filter(
                "file_hash",
                document.file_hash,
            )
        )

        if points:
            return points, "file_hash"

        if filename_counts[document.filename] != 1:
            return [], None

        points = self._scroll_all(
            self._exact_filter(
                "filename",
                document.filename,
            )
        )

        if points:
            return points, "filename"

        return [], None

    @staticmethod
    def _changes_required(
        payload: dict[str, Any],
        canonical_metadata: dict[str, Any],
    ) -> bool:
        return any(
            payload.get(key) != value
            for key, value in canonical_metadata.items()
        )

    @staticmethod
    def _memory_status(report: dict[str, Any]) -> str:
        if report["failures"]:
            return "ATTENTION_REQUIRED"

        if report["documents_without_vectors"]:
            return "PARTIALLY_UNIFIED"

        if report["dry_run"]:
            if report["vectors_requiring_update"]:
                return "MIGRATION_REQUIRED"

            return "ALREADY_UNIFIED"

        if (
            report["vectors_requiring_update"]
            == report["vectors_updated"]
        ):
            return "UNIFIED"

        return "ATTENTION_REQUIRED"

    def run(
        self,
        *,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        documents = self.repository.list_documents()

        filename_counts = Counter(
            document.filename
            for document in documents
        )

        report: dict[str, Any] = {
            "status": (
                "dry_run_complete"
                if dry_run
                else "migration_complete"
            ),
            "dry_run": dry_run,
            "documents_scanned": len(documents),
            "documents_matched": 0,
            "documents_requiring_update": 0,
            "documents_updated": 0,
            "documents_without_vectors": 0,
            "vectors_examined": 0,
            "vectors_requiring_update": 0,
            "vectors_updated": 0,
            "vectors_already_current": 0,
            "matched_by_document_id": 0,
            "matched_by_file_hash": 0,
            "matched_by_filename": 0,
            "ambiguous_filenames": [],
            "missing_documents": [],
            "failures": [],
        }

        for document in documents:
            try:
                points, matched_by = self._find_points(
                    document,
                    filename_counts,
                )

                if not points:
                    if filename_counts[document.filename] > 1:
                        report["ambiguous_filenames"].append(
                            {
                                "document_id": document.id,
                                "filename": document.filename,
                                "count": filename_counts[
                                    document.filename
                                ],
                            }
                        )

                    report["documents_without_vectors"] += 1
                    report["missing_documents"].append(
                        {
                            "document_id": document.id,
                            "filename": document.filename,
                            "file_hash": document.file_hash,
                        }
                    )
                    continue

                report["documents_matched"] += 1
                report[f"matched_by_{matched_by}"] += 1
                report["vectors_examined"] += len(points)

                canonical_metadata = self._canonical_metadata(
                    document
                )

                point_ids = []

                for point in points:
                    payload = point.payload or {}

                    if self._changes_required(
                        payload,
                        canonical_metadata,
                    ):
                        point_ids.append(point.id)
                        report[
                            "vectors_requiring_update"
                        ] += 1
                    else:
                        report[
                            "vectors_already_current"
                        ] += 1

                if not point_ids:
                    continue

                report["documents_requiring_update"] += 1

                if dry_run:
                    continue

                client.set_payload(
                    collection_name=COLLECTION_NAME,
                    payload=canonical_metadata,
                    points=point_ids,
                    wait=True,
                )

                report["documents_updated"] += 1
                report["vectors_updated"] += len(point_ids)

            except Exception as error:
                report["failures"].append(
                    {
                        "document_id": document.id,
                        "filename": document.filename,
                        "error": str(error),
                    }
                )

        report["memory_status"] = self._memory_status(report)

        return report
