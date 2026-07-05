from fastapi import APIRouter

from app.core.canon.canon_registry import get_canon_manifest
from app.core.canon.canon_model import CanonManifest

router = APIRouter(
    prefix="/canon",
    tags=["Canon"]
)


@router.get("/manifest", response_model=CanonManifest)
def canon_manifest():
    return get_canon_manifest()
