"""Persist factual ingestion progress independently from cognitive acceptance."""
from sqlalchemy import Column, String, JSON
from app.database import Base


class TeachingMission(Base):
    __tablename__ = "teaching_missions"
    id = Column(String, primary_key=True)
    organization_id = Column(String, nullable=False, index=True)
    domain_id = Column(String, nullable=False)
    filename = Column(String, nullable=False)
    file_path = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False)
    stage = Column(String, nullable=False)
    created_at = Column(String, nullable=False)
    updated_at = Column(String, nullable=False)
    events = Column(JSON, nullable=False)
    result = Column(JSON, nullable=True)
    error = Column(String, nullable=True)

    def public(self):
        return {key: getattr(self, key) for key in (
            "id", "organization_id", "domain_id", "filename", "topic", "description",
            "status", "stage", "created_at", "updated_at", "events", "result", "error",
        )}
