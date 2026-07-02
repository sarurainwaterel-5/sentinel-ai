from fastapi import APIRouter, UploadFile, File, Depends, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.upload_service import UploadService

router = APIRouter()

@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    module: str = Form("engineering"),
    topic: str = Form("general"),
    collection: str = Form("general"),
    description: str | None = Form(None),
    organization_id: str = Form("default"),
    db: Session = Depends(get_db),
):
    upload_service = UploadService(db)

    return await upload_service.process_pdf_upload(
        file=file,
        module=module,
        topic=topic,
        collection=collection,
        description=description,
        organization_id=organization_id,
    )
