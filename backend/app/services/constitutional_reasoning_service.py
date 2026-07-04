from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.services.core_memory_service import CORE_COLLECTION_NAME
from app.services.qdrant_service import client
from app.services.embedding_service import EmbeddingService


class ConstitutionalReasoningService:
    def __init__(self):
        self.embedding_service = EmbeddingService()

    def retrieve_constitution(self, question: str, limit: int = 5):
        query_vector = self.embedding_service.generate_embedding(question)

        response = client.query_points(
            collection_name=CORE_COLLECTION_NAME,
            query=query_vector,
            query_filter=Filter(
                must=[
                    FieldCondition(
                        key="memory_type",
                        match=MatchValue(value="core")
                    )
                ]
            ),
            limit=limit,
            with_payload=True
        )

        return [
            {
                "source_file": point.payload.get("source_file"),
                "text": point.payload.get("text"),
                "score": point.score,
                "priority": point.payload.get("priority")
            }
            for point in response.points
        ]

    def build_constitution_context(self, question: str, limit: int = 5):
        memories = self.retrieve_constitution(question, limit=limit)

        context = "\n\n".join(
            f"[{memory['source_file']}]\n{memory['text']}"
            for memory in memories
        )

        return {
            "question": question,
            "constitutional_context": context,
            "sources": memories
        }
