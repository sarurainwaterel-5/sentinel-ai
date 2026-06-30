from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.search import router as search_router
from app.routes.ask import router as ask_router
from app.services.qdrant_service import create_collection_if_not_exists

app = FastAPI(title="SentinelAI API")

app.include_router(upload_router)
app.include_router(search_router)
app.include_router(ask_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelAI"
    }

@app.get("/vector/initialize")
def initialize_vector_db():
    result = create_collection_if_not_exists()
    return {
        "status": "initialized",
        **result
    }
