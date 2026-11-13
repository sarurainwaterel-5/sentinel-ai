from uuid import uuid4

from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.settings import UPLOAD_DIR, MAX_UPLOAD_BYTES
from app.services.upload_io import save_pdf_upload
from app.services.source_upload_io import save_source_upload, READABLE_FORMATS
from app.services.media_extraction import extract_source_text

from app.services.chunking_service import chunk_text

from app.services.fingerprint_service import FingerprintService
from app.repositories.document_repository import DocumentRepository

class UploadService:
    def __init__(self, db: Session):
        self.db = db
        self.document_repository = DocumentRepository(db)
        self.embedding_service = None

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
        return self.process_saved_pdf(
            file_path=file_path, filename=filename, module=module, topic=topic,
            collection=collection, organization_id=organization_id, description=description,
        )

    async def process_source_upload(self, file, module="engineering", topic="general",
                                    collection="general", organization_id="default", description=None):
        path, filename = await save_source_upload(file, UPLOAD_DIR, MAX_UPLOAD_BYTES)
        return self.process_saved_pdf(file_path=path, filename=filename, module=module,
            topic=topic, collection=collection, organization_id=organization_id, description=description)

    def process_saved_pdf(self, *, file_path, filename, module, topic, collection,
                          organization_id, description, progress=None):
        report = progress or (lambda stage: None)
        try:
            result = self._index_pdf(
                file_path=file_path, filename=filename, module=module, topic=topic,
                collection=collection, organization_id=organization_id, description=description,
                progress=report,
            )
        except BaseException:
            # Accepted sources remain available to their recorded mission for review/retry.
            raise
        if result["status"] == "indexed":
            report("recording")
            from app.services.workspaces.learning_history import IngestionHistoryRecorder
            try:
                event = IngestionHistoryRecorder().record(result, organization_id)
                result["learning_event_id"] = event.learning_event_id
            except Exception:
                result["history_warning"] = "Document indexed, but its Learning Event could not be preserved."
        return result

    def _index_pdf(self, *, file_path, filename, module, topic, collection, organization_id, description, progress=None):
        report = progress or (lambda stage: None)
        report("fingerprinting")
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

        report("extracting")
        extension = file_path.suffix.lower().lstrip(".")
        if extension not in READABLE_FORMATS:
            extracted = {"text": "", "media_type": "application/octet-stream",
                         "extraction_method": "stored_only", "warnings": ["This file type is stored but not searchable."], "metadata": {}}
        else:
            try:
                extracted = extract_source_text(file_path, filename, progress=lambda detail: report("transcribing" if isinstance(detail, dict) and detail.get("phase") == "audio_transcription" else "extracting"))
            except HTTPException as exc:
                if exc.status_code != 503:
                    raise
                extracted = {"text": "", "media_type": extension,
                             "extraction_method": "processing_unavailable",
                             "warnings": [exc.detail], "metadata": {}}
        report("chunking")
        text = extracted["text"]
        chunks = chunk_text(text) if text.strip() else []
        if not chunks:
            report("cataloging")
            document = self.document_repository.create_document(
                document_id=document_id, filename=filename, file_hash=file_hash,
                module=module, topic=topic, collection=collection, description=description,
                chunk_count=0, embedding_model="not_indexed", status="stored",
                organization_id=organization_id)
            return {"status": "stored", "document_id": document.id, "filename": filename,
                    "file_hash": file_hash, "module": module, "topic": topic,
                    "collection": collection, "characters": 0, "chunks": 0,
                    "stored_vectors": 0, "embedding_model": "not_indexed",
                    "media_type": extracted["media_type"], "extraction_method": extracted["extraction_method"],
                    "warnings": extracted["warnings"], "metadata": extracted["metadata"],
                    "message": "Source preserved. No searchable text or Learning Event was created."}

        report("indexing")
        from app.services.qdrant_service import store_chunks
        from app.services.embedding_service import EmbeddingService
        self.embedding_service = self.embedding_service or EmbeddingService()
        stored_vectors = store_chunks(
            document_id=document_id, filename=filename, file_hash=file_hash,
            chunks=chunks, module=module, topic=topic, collection=collection,
            organization_id=organization_id, description=description,
        )

        report("cataloging")
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
            "media_type": extracted["media_type"],
            "extraction_method": extracted["extraction_method"],
            "warnings": extracted["warnings"], "metadata": extracted["metadata"],
            "preview": chunks[0][:300] if chunks else ""
        }
