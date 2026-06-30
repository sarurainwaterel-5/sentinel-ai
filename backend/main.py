from fastapi import FastAPI
from app.routes.upload import router as upload_router
from app.routes.search import router as search_router

app = FastAPI(title="SentinelAI API")
app.include_router(upload_router)
app.include_router(search_router)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "SentinelAI"
    }
