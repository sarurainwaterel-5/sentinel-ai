"""Thin HTTP boundaries for Intelligence, Governance, and Systems."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.canon.report import build_canon_report
from app.core.canon.discovery import CANON_ROOT
from app.services.workspaces.connections import ConnectionEngine
from app.services.workspaces.systems import SystemsObserver
from app.services.workspaces.models import SystemsSnapshot, ConnectionSnapshot
from app.repositories.reflection_history_repository import PersistentReflectionHistoryRepository
from app.routes.reflection import repository, resolver, orchestrator, formatter, record_factory
from app.services.cognition.reflection.reflection_application_service import ReflectionApplicationService
from app.services.cognition.reflection.reflection_api import ReflectionAPIResponse
from app.repositories.learning_event_repository import LearningEventNotFoundError
from app.services.workspaces.reflection import WorkspaceReflectionService, GoverningContextUnavailableError

router = APIRouter(tags=["Operator Workspaces"])


@router.get("/systems/status", response_model=SystemsSnapshot)
def systems_status():
    return SystemsObserver().observe()


@router.get("/intelligence/connections", response_model=ConnectionSnapshot)
def intelligence_connections():
    return ConnectionEngine().inspect()


@router.get("/intelligence/learning-events")
def learning_events(organization_id: str = "default", limit: int = Query(50, ge=1, le=100)):
    return [event.to_dict() for event in repository.recent_for_organization(organization_id, limit)]


@router.get("/reflection/history")
def reflection_history(organization_id: str = "default", limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    return [record.model_dump(mode="json") for record in PersistentReflectionHistoryRepository(db).recent_for_organization(organization_id, limit)]


@router.get("/governance/summary")
def governance_summary():
    return {
        "principles": build_canon_report(),
        "semantic_grounding_verified": False,
        "constitutional_evaluation": "not_verified",
        "adr_037_status": "Proposed",
        "proposition_inference_boundary": "closed",
        "history_policy": "append_only",
        "execution_authority": "human",
        "limitations": [
            "Structural document checks do not establish semantic truth.",
            "The independent semantic benchmark and final architecture acceptance remain outstanding.",
            "Plans, verification, and reflection never authorize execution.",
        ],
    }


class WorkspaceReflectionRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1, max_length=500)
    learning_event_ids: list[str] = Field(min_length=1, max_length=100)
    organization_id: str = Field(default="default", min_length=1)

    @field_validator("learning_event_ids")
    @classmethod
    def normalize_event_ids(cls, value):
        cleaned = [event_id.strip() for event_id in value]
        if any(not event_id for event_id in cleaned):
            raise ValueError("Learning Event IDs cannot be blank.")
        return list(dict.fromkeys(cleaned))



@router.post("/intelligence/reflection", response_model=ReflectionAPIResponse)
def reflect_on_history(request: WorkspaceReflectionRequest, db: Session = Depends(get_db)):
    application_service = ReflectionApplicationService(
        resolver=resolver, orchestrator=orchestrator, formatter=formatter,
        record_factory=record_factory, history_repository=PersistentReflectionHistoryRepository(db))
    service = WorkspaceReflectionService(repository=repository,
        application_service=application_service, canon_root=CANON_ROOT)
    try:
        return service.reflect(request)
    except LearningEventNotFoundError as exc:
        raise HTTPException(status_code=404, detail="A selected Learning Event is unavailable in this organization.") from exc
    except GoverningContextUnavailableError as exc:
        raise HTTPException(status_code=503, detail="Sentinel's governing principles could not be loaded.") from exc
