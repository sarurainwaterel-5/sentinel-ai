from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.knowledge_management_service import KnowledgeManagementService

router = APIRouter(
    prefix="/knowledge",
    tags=["Knowledge Management"]
)


@router.put("/{document_id}/archive")
def archive_document(
    document_id: str,
    db: Session = Depends(get_db)
):

    service = KnowledgeManagementService(db)

    return service.archive_document(document_id)



@router.put("/{document_id}/restore")
def restore_document(
    document_id: str,
    db: Session = Depends(get_db)
):
    service = KnowledgeManagementService(db)

    return service.restore_document(document_id)
