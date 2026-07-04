from pathlib import Path
from uuid import uuid4

from qdrant_client.models import Distance, VectorParams, PointStruct

from app.services.qdrant_service import client
from app.services.embedding_service import EmbeddingService
from app.services.chunking_service import chunk_text

CORE_COLLECTION_NAME = "sentinel_core_memory"

embedding_service = EmbeddingService()


def create_core_memory_collection():
    vector_size = embedding_service.get_dimension()

    collections = client.get_collections().collections
    existing = [collection.name for collection in collections]

    if CORE_COLLECTION_NAME not in existing:
        client.create_collection(
            collection_name=CORE_COLLECTION_NAME,
            vectors_config=VectorParams(
                size=vector_size,
                distance=Distance.COSINE
            )
        )

    return {
        "collection": CORE_COLLECTION_NAME,
        "vector_size": vector_size,
        "embedding_model": embedding_service.get_model_name()
    }


def ingest_core_memory():
    create_core_memory_collection()

    project_root = Path(__file__).resolve().parents[3]

    memory_paths = [
        project_root / "docs" / "philosophy",
        project_root / "docs" / "design",
        project_root / "docs" / "architecture" / "decisions",
    ]

    points = []

    for memory_path in memory_paths:
        if not memory_path.exists():
            continue

        for file_path in memory_path.glob("*.md"):
            text = file_path.read_text(encoding="utf-8")
            chunks = chunk_text(text)

            for index, chunk in enumerate(chunks):
                points.append(
                    PointStruct(
                        id=str(uuid4()),
                        vector=embedding_service.generate_embedding(chunk),
                        payload={
                            "memory_type": "core",
                            "source_file": str(file_path.relative_to(project_root)),
                            "chunk_index": index,
                            "text": chunk,
                            "priority": "constitutional"
                        }
                    )
                )

    if points:
        client.upsert(
            collection_name=CORE_COLLECTION_NAME,
            points=points
        )

    return {
        "status": "core_memory_ingested",
        "collection": CORE_COLLECTION_NAME,
        "points_stored": len(points)
    }
