from pathlib import Path

from sqlalchemy.orm import Session
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.repositories.document_repository import DocumentRepository
from app.services.qdrant_service import client, COLLECTION_NAME


class KnowledgeManagementService:

    def __init__(self, db: Session):
        self.db = db
        self.repository = DocumentRepository(db)

    def archive_document(self, document_id: str):

        document = self.repository.get_by_id(document_id)

        if not document:
            return {
                "status": "not_found"
            }

        if (document.chunk_count or 0) > 0 and document.embedding_model != "not_indexed":
            self._set_index_status(document_id, "archived")
        document.status = "archived"
        self.db.commit()
        return {"status": "archived", "document_id": document.id, "filename": document.filename}

    @staticmethod
    def _set_index_status(document_id, status):
        client.set_payload(collection_name=COLLECTION_NAME, payload={"status": status},
            points=Filter(must=[FieldCondition(key="document_id", match=MatchValue(value=document_id))]), wait=True)

    def restore_document(self, document_id: str):
        document = self.repository.get_by_id(document_id)

        if not document:
            return {
                "status": "not_found"
            }

        indexed = (document.chunk_count or 0) > 0 and document.embedding_model != "not_indexed"
        if indexed:
            self._set_index_status(document_id, "indexed")
        document.status = "indexed" if indexed else "stored"
        self.db.commit()
        restored = document

        return {
            "status": "restored",
            "document_id": restored.id,
            "filename": restored.filename
        }
