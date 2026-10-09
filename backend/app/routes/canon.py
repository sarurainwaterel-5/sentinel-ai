from fastapi import APIRouter, HTTPException, Query
from app.services.workspaces.canon_library import observe_library, read_library_document

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


@router.get("/library")
def canon_library():
    try:
        return observe_library()
    except (OSError, UnicodeError) as exc:
        raise HTTPException(status_code=503, detail="The principle library could not be read. Check Systems and retry.") from exc


@router.get("/document")
def canon_document(path: str = Query(min_length=1, max_length=500)):
    try:
        return read_library_document(path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail="This principle document is no longer available. Refresh the library.") from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="This principle document cannot be opened by the read-only reader.") from exc
    except (OSError, UnicodeError) as exc:
        raise HTTPException(status_code=503, detail="The principle document could not be read. Retry later.") from exc
