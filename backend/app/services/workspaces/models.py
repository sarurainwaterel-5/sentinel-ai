"""Inspectable contracts for observed platform condition and discovered connections."""
from pydantic import BaseModel, Field


class ServiceObservation(BaseModel):
    name: str
    status: str
    detail: str


class SystemsSnapshot(BaseModel):
    observed_at: str
    status: str
    services: list[ServiceObservation]
    model_features_configured: bool
    semantic_grounding_verified: bool = False
    constitutional_evaluation: str = "not_verified"
    execution_authority: str = "human"
    warnings: list[str] = Field(default_factory=list)


class ConnectionNode(BaseModel):
    id: str
    title: str
    layer: str
    type: str
    path: str | None = None


class ConnectionEdge(BaseModel):
    source: str
    target: str
    relationship: str
    basis: str


class ConnectionSnapshot(BaseModel):
    nodes: list[ConnectionNode]
    edges: list[ConnectionEdge]
    unresolved_references: list[dict[str, str]]
    relationships: dict[str, int]
    method: str = "document_structure_and_explicit_references"
    limitation: str = "Connections describe documented structure and references; they do not establish semantic truth or causality."
