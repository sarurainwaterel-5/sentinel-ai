"""Local teaching submission and read-only progress/history."""
from uuid import uuid4
from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.settings import UPLOAD_DIR, MAX_UPLOAD_BYTES
from app.models.teaching_mission import TeachingMission
from app.services.upload_io import save_pdf_upload
from app.services.workspaces.teaching import now, run_mission, slots
from app.core.domains.builder import build_domain_registry

router = APIRouter(prefix="/teach", tags=["Teaching Missions"])


@router.get("/config")
def config():
    return {"max_upload_bytes": MAX_UPLOAD_BYTES, "supported_formats": ["pdf"], "ocr_available": False}


@router.post("/missions", status_code=202)
async def submit_mission(background: BackgroundTasks, file: UploadFile = File(...),
                         module: str = Form(..., min_length=1, max_length=200),
                         topic: str = Form("general", max_length=200),
                         description: str = Form("", max_length=2000),
                         organization_id: str = Form("default", min_length=1, max_length=200),
                         db: Session = Depends(get_db)):
    if not organization_id.strip() or module == "all" or build_domain_registry().get(module) is None:
        raise HTTPException(422, "Select a registered specific domain and organization before teaching.")
    if not slots.acquire(blocking=False):
        raise HTTPException(429, "The local teaching queue is full. Wait for a mission to finish, then retry.")
    path = None
    try:
        path, filename = await save_pdf_upload(file, UPLOAD_DIR, MAX_UPLOAD_BYTES)
        timestamp = now()
        mission = TeachingMission(id=str(uuid4()), filename=filename, file_path=str(path),
            organization_id=organization_id, domain_id=module, topic=topic.strip() or "general",
            description=description.strip(), status="queued", stage="received", created_at=timestamp,
            updated_at=timestamp, events=[{"stage": "received", "at": timestamp, "detail": "PDF received and validated."}])
        db.add(mission)
        db.commit()
        payload = mission.public()
        background.add_task(run_mission, mission.id)
        return payload
    except BaseException as exc:
        db.rollback()
        if path is not None:
            path.unlink(missing_ok=True)
        slots.release()
        if isinstance(exc, (SQLAlchemyError, OSError)):
            raise HTTPException(503, "Teaching storage is unavailable. Check Systems and retry.") from exc
        raise


@router.get("/missions")
def list_missions(organization_id: str = Query("default", min_length=1, max_length=200),
                  domain_id: str | None = Query(None, max_length=200),
                  limit: int = Query(20, ge=1, le=100), db: Session = Depends(get_db)):
    try:
        query = db.query(TeachingMission).filter(TeachingMission.organization_id == organization_id)
        if domain_id and domain_id != "all":
            query = query.filter(TeachingMission.domain_id == domain_id)
        return [mission.public() for mission in query.order_by(TeachingMission.created_at.desc(), TeachingMission.id.desc()).limit(limit)]
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Mission history is unavailable. Check Systems and retry.") from exc


@router.get("/missions/{mission_id}")
def get_mission(mission_id: str, organization_id: str = Query("default", min_length=1, max_length=200), db: Session = Depends(get_db)):
    try:
        mission = db.query(TeachingMission).filter(TeachingMission.id == mission_id, TeachingMission.organization_id == organization_id).first()
    except SQLAlchemyError as exc:
        raise HTTPException(503, "Mission progress is unavailable. Check Systems and retry.") from exc
    if mission is None:
        raise HTTPException(404, "Teaching mission not found in this organization.")
    return mission.public()
