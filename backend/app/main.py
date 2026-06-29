from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.services.qdrant_service import create_collection_if_not_exists

app = FastAPI(title="SentinelAI API")

app.include_router(upload_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelAI"
    }

@app.get("/vector/initialize")
def initialize_vector_db():
    collection = create_collection_if_not_exists()
    return {
        "status": "initialized",
        "collection": collection
    }
