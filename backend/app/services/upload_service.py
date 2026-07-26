from pathlib import Path
from uuid import uuid4

from sqlalchemy.orm import Session

from app.services.pdf_service import extract_text_from_pdf
from app.services.chunking_service import chunk_text
from app.services.qdrant_service import store_chunks
from app.services.fingerprint_service import FingerprintService
from app.services.embedding_service import EmbeddingService
from app.repositories.document_repository import DocumentRepository

UPLOAD_DIR = "uploads"
Path(UPLOAD_DIR).mkdir(exist_ok=True)

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
        file_path = f"{UPLOAD_DIR}/{file.filename}"

        with open(file_path, "wb") as buffer:
            buffer.write(await file.read())

        file_hash = FingerprintService.calculate_sha256(file_path)

        existing_document = self.document_repository.get_by_hash(file_hash)

        if existing_document:
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
                "filename": file.filename,
                "file_hash": file_hash,
            }

        document_id = str(uuid4())

        text = extract_text_from_pdf(file_path)
        chunks = chunk_text(text)

        stored_vectors = store_chunks(
    document_id=document_id,
    filename=file.filename,
    file_hash=file_hash,
    chunks=chunks,
    module=module,
    topic=topic,
    collection=collection,
    organization_id=organization_id,
    description=description,
)

        document = self.document_repository.create_document(
            document_id=document_id,
            filename=file.filename,
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
