from app.models.document import Document


class DocumentRepository:
    def __init__(self, db):
        self.db = db

    def create_document(
        self,
        document_id: str,
        filename: str,
        file_hash: str,
        collection: str,
        chunk_count: int,
        embedding_model: str,
        module: str = "engineering",
        topic: str = "general",
        status: str = "indexed",
        organization_id: str = "default",
        description: str | None = None,
    ):
        document = Document(
            id=document_id,
            filename=filename,
            file_hash=file_hash,
            module=module,
            topic=topic,
            collection=collection,
            description=description,
            chunk_count=chunk_count,
            embedding_model=embedding_model,
            status=status,
            organization_id=organization_id,
        )

        self.db.add(document)
        self.db.commit()
        self.db.refresh(document)
        return document

    def archive_document(self, document):
        document.status = "archived"
        self.db.commit()
        self.db.refresh(document)
        return document

    def restore_document(self, document):
        document.status = "indexed"
        self.db.commit()
        self.db.refresh(document)
        return document

    def get_by_hash(self, file_hash: str):
        return self.db.query(Document).filter(Document.file_hash == file_hash).first()

    def get_by_id(self, document_id: str):
        return self.db.query(Document).filter(Document.id == document_id).first()

    def list_documents(self):
        return self.db.query(Document).order_by(Document.uploaded_at.desc()).all()

    def count_documents(self):
        return self.db.query(Document).count()

    def count_archived(self):
        return self.db.query(Document).filter(Document.status == "archived").count()

    def total_chunks(self):
        return sum(
            document.chunk_count or 0
            for document in self.db.query(Document).all()
        )

    def list_recent_documents(self, limit=5):
        return (
            self.db.query(Document)
            .order_by(Document.uploaded_at.desc())
            .limit(limit)
            .all()
        )

    def count_modules(self):
        return len({
            document.module
            for document in self.db.query(Document).all()
            if document.module
        })

    def count_topics(self):
        return len({
            document.topic
            for document in self.db.query(Document).all()
            if document.topic
        })

    def count_collections(self):
        return len({
            document.collection
            for document in self.db.query(Document).all()
            if document.collection
        })
