from fastapi import APIRouter, HTTPException

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
