from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.document_repository import DocumentRepository

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.get("")
def list_documents(db: Session = Depends(get_db)):
    repository = DocumentRepository(db)

    documents = repository.list_documents()

    return [
        {
            "id": document.id,
            "filename": document.filename,
            "collection": document.collection,
            "status": document.status,
            "chunk_count": document.chunk_count,
            "embedding_model": document.embedding_model,
            "uploaded_at": document.uploaded_at,
        }
        for document in documents
    ]
