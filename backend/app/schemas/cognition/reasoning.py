from pydantic import BaseModel
from typing import Optional


class ReasoningRequest(BaseModel):
    question: str
    workspace: str = "bridge"
    mission_id: Optional[str] = None
    session_id: Optional[str] = None


class CoherenceResult(BaseModel):
    coherent: bool
    constitutional_score: float
    articles_consulted: list[str]
    conflicts: list[str]
    recommendations: list[str]


class ReasoningResponse(BaseModel):
    answer: str
    workspace: str
    constitutional_sources: list[str]
    knowledge_sources: list[str]
    confidence: float
    coherence: CoherenceResult
    reflection: Optional[str] = None
