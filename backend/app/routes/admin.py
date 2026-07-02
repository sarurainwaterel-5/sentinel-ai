from collections import defaultdict
from fastapi import APIRouter
from app.services.qdrant_service import client, COLLECTION_NAME

router = APIRouter()

@router.get("/admin/documents")
def list_documents():
    points, _ = client.scroll(
        collection_name=COLLECTION_NAME,
        limit=10000,
        with_payload=True,
        with_vectors=False
    )

    docs = defaultdict(lambda: {"chunks": 0, "filenames": set()})

    for point in points:
        payload = point.payload
        doc_id = payload.get("document_id")
        filename = payload.get("filename")

        docs[doc_id]["chunks"] += 1
        docs[doc_id]["filenames"].add(filename)

    return [
        {
            "document_id": doc_id,
            "chunks": data["chunks"],
            "filenames": list(data["filenames"])
        }
        for doc_id, data in docs.items()
    ]
