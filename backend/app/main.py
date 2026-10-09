import os
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from app.settings import CORS_ORIGINS
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
from app.routes.domains import router as domains_router
from app.routes.planning import (
    router as planning_router,
)
from app.routes.reflection import (
    router as reflection_router,
)

from app.routes.verification import (
    router as verification_router,
)


from app.routes.workspaces import router as workspaces_router

from contextlib import asynccontextmanager
from app.routes.teaching import router as teaching_router
from app.services.workspaces.teaching import recover_interrupted


@asynccontextmanager
async def lifespan(app):
    recover_interrupted()
    yield


app = FastAPI(title="SentinelAI API", lifespan=lifespan)
app.include_router(teaching_router)
app.include_router(workspaces_router)

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
app.include_router(domains_router)
app.include_router(planning_router)
app.include_router(verification_router)
app.include_router(reflection_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def model_configuration_guard(request, call_next):
    if request.url.path in {"/ask", "/cognition/reason", "/cognition/plan", "/verification"} and request.method == "POST" and not os.getenv("OPENAI_API_KEY"):
        return JSONResponse(status_code=503, content={"detail": "Configure OPENAI_API_KEY in backend/.env and restart Sentinel to enable this feature."})
    return await call_next(request)

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

@app.get("/ready")
def readiness_check():
    from sqlalchemy import text, inspect
    from app.database import engine
    from app.services.qdrant_service import client
    services = {}
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
            tables = set(inspect(connection).get_table_names())
        services["postgres"] = "ready" if {"documents", "reflection_history"} <= tables else "migration_required"
    except Exception:
        services["postgres"] = "unavailable"
    try:
        client.get_collections()
        services["qdrant"] = "ready"
    except Exception:
        services["qdrant"] = "unavailable"
    ready = all(value == "ready" for value in services.values())
    return JSONResponse(status_code=200 if ready else 503, content={
        "status": "ready" if ready else "unavailable",
        "services": services,
        "model_features_configured": bool(os.getenv("OPENAI_API_KEY")),
    })


# Provider failures are bounded operational errors, never raw SDK payloads.
from openai import OpenAIError, AuthenticationError, RateLimitError


@app.exception_handler(OpenAIError)
async def provider_error_handler(request, exc):
    if isinstance(exc, AuthenticationError):
        detail = "The model provider rejected Sentinel's credentials. Update backend/.env and restart Sentinel."
    elif isinstance(exc, RateLimitError):
        detail = "The model provider's quota or rate limit was reached. Check the provider account before retrying."
    else:
        detail = "The model provider could not complete this operation. No action was executed. Retry later."
    return JSONResponse(status_code=503, content={"detail": detail})


from qdrant_client.http.exceptions import ResponseHandlingException


@app.exception_handler(ResponseHandlingException)
async def vector_transport_error_handler(request, exc):
    return JSONResponse(status_code=503, content={"detail": "Sentinel could not search its indexed evidence. The vector service may be busy or unavailable. Check Systems and retry; your taught documents are preserved."})
