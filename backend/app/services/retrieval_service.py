from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import client, COLLECTION_NAME

embedding_service = EmbeddingService()

class RetrievalService:
    def search(self, question: str, limit: int = 5, score_threshold: float = 0.45):
        query_vector = embedding_service.generate_embedding(question)

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            limit=limit,
            score_threshold=score_threshold
        )

        return results.points
