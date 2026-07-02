from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.knowledge_analytics_service import KnowledgeAnalyticsService
from app.schemas.dashboard import DashboardResponse

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Management"]
)

@router.get("/dashboard", response_model=DashboardResponse)
def get_knowledge_dashboard(db: Session = Depends(get_db)):
    service = KnowledgeAnalyticsService(db)
    return service.dashboard()
