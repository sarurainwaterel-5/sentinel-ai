from collections import Counter
from app.repositories.document_repository import DocumentRepository


class KnowledgeAnalyticsService:
    def __init__(self, db):
        self.repository = DocumentRepository(db)

    def dashboard(self):
        documents = self.repository.list_documents()
        recent = self.repository.list_recent_documents(limit=5)

        modules = Counter(doc.module or "unknown" for doc in documents)
        topics = Counter(doc.topic or "general" for doc in documents)
        collections = Counter(doc.collection or "general" for doc in documents)

        indexed_docs = [doc for doc in documents if doc.status == "indexed"]
        archived_docs = [doc for doc in documents if doc.status == "archived"]

        return {
            "overview": {
                "total_documents": len(documents),
                "indexed_documents": len(indexed_docs),
                "archived_documents": len(archived_docs),
                "knowledge_domains": len(modules),
                "topics": len(topics),
                "collections": len(collections),
                "indexed_chunks": sum(doc.chunk_count or 0 for doc in documents),
            },
            "knowledge_domains": [
                {
                    "name": name,
                    "document_count": count
                }
                for name, count in modules.items()
            ],
            "topics": [
                {
                    "name": name,
                    "document_count": count
                }
                for name, count in topics.items()
            ],
            "collections": [
                {
                    "name": name,
                    "document_count": count
                }
                for name, count in collections.items()
            ],
            "recent_documents": [
                {
                    "id": doc.id,
                    "filename": doc.filename,
                    "module": doc.module,
                    "topic": doc.topic,
                    "collection": doc.collection,
                    "status": doc.status,
                    "chunk_count": doc.chunk_count,
                    "uploaded_at": doc.uploaded_at.isoformat() if doc.uploaded_at else None,
                }
                for doc in recent
            ]
        }
