from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from app.database import get_db
from app.services.workspaces.domain_memory import observe_domain_memory

from app.core.domains.builder import build_domain_registry
from app.core.domains.renderer import (
    DomainModelValidationError,
    render_domain_model,
)


router = APIRouter(
    prefix="/domains",
    tags=["Operational Domains"],
)


@router.get("")
def get_domain_model():
    """
    Return SentinelAI's validated, read-only Domain Model.
    """

    try:
        return render_domain_model()
    except DomainModelValidationError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


@router.get("/memory")
def get_domain_memory(organization_id: str = Query(default="default", min_length=1, max_length=200), db: Session = Depends(get_db)):
    if not organization_id.strip():
        raise HTTPException(status_code=422, detail="An organization scope is required.")
    try:
        return observe_domain_memory(db, organization_id)
    except SQLAlchemyError as exc:
        raise HTTPException(status_code=503, detail="Domain memory counts are unavailable. Check Systems and retry.") from exc


@router.get("/{domain_id}")
def get_domain(domain_id: str):
    """
    Return one registered operational domain by identifier.
    """

    registry = build_domain_registry()
    domain = registry.get(domain_id)

    if domain is None:
        raise HTTPException(
            status_code=404,
            detail=f"Operational domain '{domain_id}' was not found.",
        )

    return domain.to_dict()
