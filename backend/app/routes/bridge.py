from fastapi import APIRouter

from app.core.bridge.summary import build_bridge_summary

router = APIRouter(
    prefix="/bridge",
    tags=["Bridge"]
)


@router.get("/summary")
def bridge_summary():
    return build_bridge_summary()
