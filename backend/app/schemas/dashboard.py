from pydantic import BaseModel
from typing import Optional


class DashboardOverview(BaseModel):
    total_documents: int
    indexed_documents: int
    archived_documents: int
    knowledge_domains: int
    topics: int
    collections: int
    indexed_chunks: int


class KnowledgeDomainSummary(BaseModel):
    name: str
    document_count: int


class TopicSummary(BaseModel):
    name: str
    document_count: int


class CollectionSummary(BaseModel):
    name: str
    document_count: int


class RecentDocument(BaseModel):
    id: str
    filename: str
    module: Optional[str]
    topic: Optional[str]
    collection: Optional[str]
    status: str
    chunk_count: int
    uploaded_at: Optional[str]


class DashboardResponse(BaseModel):
    overview: DashboardOverview
    knowledge_domains: list[KnowledgeDomainSummary]
    topics: list[TopicSummary]
    collections: list[CollectionSummary]
    recent_documents: list[RecentDocument]
