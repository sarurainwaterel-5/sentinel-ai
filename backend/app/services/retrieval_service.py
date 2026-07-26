from qdrant_client.models import (
    FieldCondition,
    Filter,
    MatchValue,
)

from app.services.embedding_service import EmbeddingService
from app.services.qdrant_service import (
    COLLECTION_NAME,
    client,
)


embedding_service = EmbeddingService()


class RetrievalService:
    """
    Domain-aware semantic retrieval.

    Retrieval searches SentinelAI's semantic memory while preserving
    explicit workspace and organizational boundaries.

    Retrieval finds evidence.

    Retrieval does not reason.

    Retrieval does not generate answers.
    """

    def search(
        self,
        question: str,
        limit: int = 5,
        score_threshold: float = 0.45,
        module: str | None = None,
        topic: str | None = None,
        organization_id: str = "default",
    ):
        query_vector = embedding_service.generate_embedding(question)

        must_conditions = [
            FieldCondition(
                key="organization_id",
                match=MatchValue(value=organization_id),
            )
        ]

        if module and module != "all":
            must_conditions.append(
                FieldCondition(
                    key="module",
                    match=MatchValue(value=module),
                )
            )

        if topic and topic != "all":
            must_conditions.append(
                FieldCondition(
                    key="topic",
                    match=MatchValue(value=topic),
                )
            )

        query_filter = Filter(
            must=must_conditions,
        )

        results = client.query_points(
            collection_name=COLLECTION_NAME,
            query=query_vector,
            query_filter=query_filter,
            limit=limit,
            score_threshold=score_threshold,
        )

        return results.points
