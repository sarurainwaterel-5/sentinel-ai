from fastapi import APIRouter

from app.core.canon.manifest import build_canon_manifest
from app.core.canon.report import build_canon_report
from app.core.canon.graph import build_canon_graph

router = APIRouter(
    prefix="/canon",
    tags=["Canon"]
)


@router.get("/manifest")
def canon_manifest():
    return build_canon_manifest()


@router.get("/health")
def canon_health():
    return build_canon_report()


@router.get("/graph")
def canon_graph():
    return build_canon_graph()
