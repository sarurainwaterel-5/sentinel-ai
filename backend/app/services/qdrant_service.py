from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

COLLECTION_NAME = "incident_knowledge"
VECTOR_SIZE = 384

client = QdrantClient(host="localhost", port=6333)

def create_collection_if_not_exists():
    collections = client.get_collections().collections
    existing = [collection.name for collection in collections]

    if COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=VECTOR_SIZE,
                distance=Distance.COSINE
            )
        )

    return COLLECTION_NAME
