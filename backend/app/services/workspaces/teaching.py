"""Single-process local ingestion queue with durable, observed mission progress.

Accepted jobs survive as history. After process interruption they require an
explicit resubmission; partial storage is never reported as a successful job.
"""
from datetime import datetime, timezone
from pathlib import Path
from threading import BoundedSemaphore, Lock
from fastapi import HTTPException
from sqlalchemy import inspect
from app.database import SessionLocal, engine
from app.models.teaching_mission import TeachingMission
from app.services.upload_service import UploadService

slots = BoundedSemaphore(8)
worker_lock = Lock()


def now():
    return datetime.now(timezone.utc).isoformat()


def advance(db, mission, stage, *, status="running", detail=None):
    timestamp = now()
    mission.stage = stage
    mission.status = status
    mission.updated_at = timestamp
    mission.events = [*mission.events, {"stage": stage, "at": timestamp, "detail": detail}]
    db.commit()


def run_mission(mission_id):
    try:
        # Serial indexing bounds memory use and prevents duplicate job races.
        with worker_lock, SessionLocal() as db:
            mission = db.get(TeachingMission, mission_id)
            if mission is None or mission.status != "queued":
                return
            try:
                result = UploadService(db).process_saved_pdf(
                    file_path=Path(mission.file_path), filename=mission.filename,
                    module=mission.domain_id, topic=mission.topic, collection=mission.domain_id,
                    organization_id=mission.organization_id, description=mission.description,
                    progress=lambda stage: advance(db, mission, stage),
                )
                mission.result = result
                advance(db, mission, "finished", status="duplicate" if result["status"] == "duplicate" else "completed",
                        detail=result.get("history_warning"))
            except Exception as exc:
                db.rollback()
                # Input errors are already bounded by the ingestion service.
                mission.error = exc.detail if isinstance(exc, HTTPException) and exc.status_code == 422 else "Teaching could not finish. Check Systems before resubmitting this PDF."
                if mission.stage != "recording":
                    Path(mission.file_path).unlink(missing_ok=True)
                advance(db, mission, "failed", status="failed", detail=mission.error)
    finally:
        slots.release()


def recover_interrupted(database=engine, session_factory=SessionLocal):
    if not inspect(database).has_table("teaching_missions"):
        return
    with session_factory() as db:
        for mission in db.query(TeachingMission).filter(TeachingMission.status.in_(["queued", "running"])):
            mission.error = "Sentinel restarted before this mission finished. Check the catalog, then resubmit if needed; duplicate detection remains active."
            advance(db, mission, "interrupted", status="interrupted", detail=mission.error)
