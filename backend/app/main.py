from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.search import router as search_router
from app.routes.ask import router as ask_router
from app.routes.documents import router as documents_router
from app.routes.lifecycle import router as lifecycle_router
from app.routes.knowledge_dashboard import router as knowledge_dashboard_router
from app.routes.core_memory import router as core_memory_router
from app.routes.constitution import router as constitution_router
from app.routes.cognition import router as cognition_router
from app.routes.canon import router as canon_router
from app.routes.bridge import router as bridge_router
from app.services.qdrant_service import create_collection_if_not_exists
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="SentinelAI API")

app.include_router(upload_router)
app.include_router(search_router)
app.include_router(ask_router)
app.include_router(documents_router)
app.include_router(lifecycle_router)
app.include_router(knowledge_dashboard_router)
app.include_router(core_memory_router)
app.include_router(constitution_router)
app.include_router(cognition_router)
app.include_router(canon_router)
app.include_router(bridge_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
