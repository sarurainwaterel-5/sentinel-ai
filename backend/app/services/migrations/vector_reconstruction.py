"""
Vector Reconstruction Service

Rebuilds missing Qdrant vector memory from existing PDF source files
while preserving canonical Postgres document identity.

The service never creates new document records.

It reuses:

- document ID
- file hash
- domain metadata
- organization identity
- original PDF content
"""

from pathlib import Path
from typing import Any

from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)
from sqlalchemy.orm import Session

from app.repositories.document_repository import DocumentRepository
from app.services.chunking_service import chunk_text
from app.services.pdf_service import extract_text_from_pdf
from app.services.qdrant_service import (
    COLLECTION_NAME,
    client,
    store_chunks,
)


class VectorReconstructionService:
    """Restore absent vector memory for existing documents."""

    def __init__(
        self,
        db: Session,
        upload_directory: str = "uploads",
    ):
        self.repository = DocumentRepository(db)
        self.upload_directory = Path(upload_directory)

    @staticmethod
    def _document_filter(document_id: str) -> Filter:
        return Filter(
            must=[
                FieldCondition(
                    key="document_id",
                    match=MatchValue(value=document_id),
                )
            ]
        )

    @classmethod
    def _vector_count(cls, document_id: str) -> int:
        result = client.count(
            collection_name=COLLECTION_NAME,
            count_filter=cls._document_filter(document_id),
            exact=True,
        )

        return result.count

    def _source_path(self, filename: str) -> Path:
        return self.upload_directory / filename

    def reconstruct_document(
        self,
        document,
        *,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        existing_vector_count = self._vector_count(document.id)

        result: dict[str, Any] = {
            "document_id": document.id,
            "filename": document.filename,
            "dry_run": dry_run,
            "existing_vectors": existing_vector_count,
            "expected_chunks": document.chunk_count or 0,
            "reconstructed_vectors": 0,
            "status": "pending",
        }

        if existing_vector_count > 0:
            result["status"] = "already_present"
            return result

        source_path = self._source_path(document.filename)

        if not source_path.exists():
            result["status"] = "source_missing"
            result["source_path"] = str(source_path)
            return result

        text = extract_text_from_pdf(str(source_path))

        if not text.strip():
            result["status"] = "no_extractable_text"
            return result

        chunks = chunk_text(text)

        result["reconstructed_chunk_count"] = len(chunks)
        result["character_count"] = len(text)

        if dry_run:
            result["status"] = "reconstruction_required"
            return result

        stored_vectors = store_chunks(
            document_id=document.id,
            filename=document.filename,
            file_hash=document.file_hash,
            chunks=chunks,
            module=document.module or "engineering",
            topic=document.topic or "general",
            collection=document.collection or "general",
            organization_id=(
                document.organization_id or "default"
            ),
            description=document.description,
        )

        result["reconstructed_vectors"] = stored_vectors
        result["status"] = "reconstructed"

        return result

    def run(
        self,
        *,
        filenames: list[str] | None = None,
        dry_run: bool = True,
    ) -> dict[str, Any]:
        documents = self.repository.list_documents()

        if filenames:
            selected = set(filenames)
            documents = [
                document
                for document in documents
                if document.filename in selected
            ]

        report: dict[str, Any] = {
            "dry_run": dry_run,
            "documents_scanned": len(documents),
            "documents_requiring_reconstruction": 0,
            "documents_reconstructed": 0,
            "documents_already_present": 0,
            "source_files_missing": 0,
            "documents_without_text": 0,
            "vectors_reconstructed": 0,
            "results": [],
            "failures": [],
        }

        for document in documents:
            try:
                result = self.reconstruct_document(
                    document,
                    dry_run=dry_run,
                )

                report["results"].append(result)

                status = result["status"]

                if status == "reconstruction_required":
                    report[
                        "documents_requiring_reconstruction"
                    ] += 1

                elif status == "reconstructed":
                    report["documents_reconstructed"] += 1
                    report["vectors_reconstructed"] += result[
                        "reconstructed_vectors"
                    ]

                elif status == "already_present":
                    report["documents_already_present"] += 1

                elif status == "source_missing":
                    report["source_files_missing"] += 1

                elif status == "no_extractable_text":
                    report["documents_without_text"] += 1

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

    @staticmethod
    def _memory_status(report: dict[str, Any]) -> str:
        if report["failures"]:
            return "ATTENTION_REQUIRED"

        if report["source_files_missing"]:
            return "SOURCE_RECOVERY_REQUIRED"

        if report["documents_without_text"]:
            return "TEXT_EXTRACTION_REQUIRED"

        if report["dry_run"]:
            if report["documents_requiring_reconstruction"]:
                return "RECONSTRUCTION_REQUIRED"

            return "ALREADY_COMPLETE"

        if report["documents_reconstructed"]:
            return "RECONSTRUCTED"

        return "ALREADY_COMPLETE"
