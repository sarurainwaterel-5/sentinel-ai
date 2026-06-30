from uuid import uuid4

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

from app.services.embedding_service import EmbeddingService

COLLECTION_NAME = "incident_knowledge"

client = QdrantClient(host="localhost", port=6333)
embedding_service = EmbeddingService()

def create_collection_if_not_exists():
    vector_size = embedding_service.get_dimension()

    collections = client.get_collections().collections
    existing = [collection.name for collection in collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    return {
        "collection": COLLECTION_NAME,
        "vector_size": vector_size,
        "embedding_model": embedding_service.get_model_name()
    }

def store_chunks(document_id: str, filename: str, chunks: list[str]):
    create_collection_if_not_exists()

    points = []

    for index, chunk in enumerate(chunks):
        vector = embedding_service.generate_embedding(chunk)

        points.append(
            PointStruct(
                id=str(uuid4()),
                vector=vector,
                payload={
                    "document_id": document_id,
                    "filename": filename,
                    "chunk_index": index,
                    "text": chunk,
                    "embedding_model": embedding_service.get_model_name()
                }
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    return len(points)
