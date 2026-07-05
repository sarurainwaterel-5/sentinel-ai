from pydantic import BaseModel


class CanonSource(BaseModel):
    name: str
    path: str
    layer: str
    description: str


class CanonManifest(BaseModel):
    name: str = "SentinelAI Canon"
    version: str = "1.0"
    description: str = "Permanent identity and governing knowledge for SentinelAI."
    sources: list[CanonSource]
