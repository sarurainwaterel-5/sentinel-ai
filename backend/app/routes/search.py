from fastapi import APIRouter
from app.services.retrieval_service import RetrievalService

router = APIRouter()
retrieval = RetrievalService()

@router.get("/search")
def semantic_search(question: str):
    results = retrieval.search(question)

    return [
        {
            "score": point.score,
            "filename": point.payload.get("filename"),
            "chunk_index": point.payload.get("chunk_index"),
            "text": point.payload.get("text")
        }
        for point in results
    ]
