from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime

from app.database import Base

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True)
    filename = Column(String, nullable=False)
    file_hash = Column(String, unique=True, index=True, nullable=False)

    module = Column(String, default="engineering")
    topic = Column(String, default="general")
    collection = Column(String, default="general")

    description = Column(String, nullable=True)
    chunk_count = Column(Integer, default=0)
    embedding_model = Column(String, nullable=False)
    status = Column(String, default="indexed")
    organization_id = Column(String, default="default")
    uploaded_at = Column(DateTime, default=datetime.utcnow)
