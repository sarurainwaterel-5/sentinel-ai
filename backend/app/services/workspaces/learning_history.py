"""Record factual additions to operational memory, without inventing understanding."""
from pathlib import Path
from app.core.cognition.models import LearningEvent
from app.repositories.learning_event_repository import LearningEventRepository, LearningEventNotFoundError

LEARNING_DATABASE_PATH = Path(__file__).resolve().parents[3] / "data" / "learning-events.sqlite3"


class IngestionHistoryRecorder:
    def __init__(self, repository=None):
        self.repository = repository or LearningEventRepository(database_path=LEARNING_DATABASE_PATH)

    def record(self, result: dict, organization_id: str) -> LearningEvent:
        event_id = "ingestion:" + result["document_id"]
        try:
            return self.repository.get(event_id)
        except LearningEventNotFoundError:
            pass
        event = LearningEvent(
            learning_event_id=event_id,
            source=result["filename"],
            domain_ids=[result["module"]],
            observations_added=["document:" + result["document_id"]],
            evidence_added=[f"document:{result['document_id']}:chunk:{index}" for index in range(result["chunks"])],
            summary=f"Recorded {result['chunks']} memory chunks from {result['filename']} in {result['module']}.",
            metadata={"organization_id": organization_id, "document_id": result["document_id"],
                      "file_hash": result["file_hash"], "scope": "ingestion_observation",
                      "limitation": "Ingestion records acquired evidence; it does not establish concepts, principles, or understanding."},
        )
        self.repository.save(event)
        return event
