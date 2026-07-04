from fastapi import APIRouter

from app.services.constitutional_reasoning_service import ConstitutionalReasoningService
from app.services.constitution.constitution_builder_service import ConstitutionBuilderService

router = APIRouter(
    prefix="/constitution",
    tags=["Constitution"]
)

from pathlib import Path
import json


@router.get("/recall")
def recall_constitution(question: str, limit: int = 5):
    service = ConstitutionalReasoningService()

    return service.build_constitution_context(
        question=question,
        limit=limit
    )


@router.post("/rebuild")
def rebuild_constitution():
    service = ConstitutionBuilderService()
    return service.rebuild_constitution()

@router.get("/build-info")
def constitution_build_info():
    project_root = Path(__file__).resolve().parents[2]
    manifest_path = project_root / "docs" / "architecture" / "constitution-build-manifest.json"

    if not manifest_path.exists():
        return {
            "status": "not_built",
            "message": "The Constitution has not been rebuilt yet."
        }

    return json.loads(manifest_path.read_text(encoding="utf-8"))
