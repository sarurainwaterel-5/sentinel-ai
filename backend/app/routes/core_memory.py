from fastapi import APIRouter

from app.services.core_memory_service import (
    create_core_memory_collection,
    ingest_core_memory
)

router = APIRouter(
    prefix="/core-memory",
    tags=["Core Memory"]
)


@router.post("/initialize")
def initialize_core_memory():
    return create_core_memory_collection()


@router.post("/ingest")
def ingest():
    return ingest_core_memory()
