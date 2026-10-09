from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.settings import UPLOAD_DIR, MAX_UPLOAD_BYTES
from app.services.upload_io import save_pdf_upload

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text
from app.services.qdrant_service import store_chunks
from app.services.fingerprint_service import FingerprintService
from app.services.embedding_service import EmbeddingService
from app.repositories.document_repository import DocumentRepository

class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.embedding_service = EmbeddingService()

    async def process_pdf_upload(
        self,
        file,
        module: str = "engineering",
        topic: str = "general",
        collection: str = "general",
        organization_id: str = "default",
        description: str | None = None,
    ):
        file_path, filename = await save_pdf_upload(file, UPLOAD_DIR, MAX_UPLOAD_BYTES)
        try:
            result = self._index_pdf(
                file_path=file_path, filename=filename, module=module, topic=topic,
                collection=collection, organization_id=organization_id, description=description,
            )
        except BaseException:
            file_path.unlink(missing_ok=True)
            raise
        if result["status"] == "indexed":
            from app.services.workspaces.learning_history import IngestionHistoryRecorder
            try:
                event = IngestionHistoryRecorder().record(result, organization_id)
                result["learning_event_id"] = event.learning_event_id
            except Exception:
                # The document is already indexed. Preserve it and report the
                # independent historical recording failure explicitly.
                result["history_warning"] = "Document indexed, but its Learning Event could not be preserved."
        return result

    def _index_pdf(self, *, file_path, filename, module, topic, collection, organization_id, description):
        file_hash = FingerprintService.calculate_sha256(file_path)

        existing_document = self.document_repository.get_by_hash(file_hash)

        if existing_document:
            file_path.unlink(missing_ok=True)
            return {
                "status": "duplicate",
                "message": "This exact document has already been uploaded.",
                "existing_document": {
                    "document_id": existing_document.id,
                    "filename": existing_document.filename,
                    "file_hash": existing_document.file_hash,
                    "module": existing_document.module,
                    "topic": existing_document.topic,
                    "collection": existing_document.collection,
                    "chunk_count": existing_document.chunk_count,
                    "uploaded_at": existing_document.uploaded_at.isoformat() if existing_document.uploaded_at else None,
                },
                "filename": filename,
                "file_hash": file_hash,
            }

        document_id = str(uuid4())

        try:
            text = extract_text_from_pdf(file_path)
        except Exception as exc:
            raise HTTPException(status_code=422, detail="The PDF could not be read.") from exc
        chunks = chunk_text(text)
        if not chunks:
            raise HTTPException(status_code=422, detail="The PDF contains no extractable text. OCR is not available.")

        stored_vectors = store_chunks(
            document_id=document_id, filename=filename, file_hash=file_hash,
            chunks=chunks, module=module, topic=topic, collection=collection,
            organization_id=organization_id, description=description,
        )

        document = self.document_repository.create_document(
            document_id=document_id,
            filename=filename,
            file_hash=file_hash,
            module=module,
            topic=topic,
            collection=collection,
            description=description,
            chunk_count=len(chunks),
            embedding_model=self.embedding_service.get_model_name(),
            status="indexed",
            organization_id=organization_id,
        )

        return {
            "status": "indexed",
            "document_id": document.id,
            "filename": document.filename,
            "file_hash": document.file_hash,
            "module": document.module,
            "topic": document.topic,
            "collection": document.collection,
            "characters": len(text),
            "chunks": len(chunks),
            "stored_vectors": stored_vectors,
            "embedding_model": document.embedding_model,
            "preview": chunks[0][:300] if chunks else ""
        }
