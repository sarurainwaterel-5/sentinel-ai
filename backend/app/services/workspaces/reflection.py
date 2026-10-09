"""Coordinate workspace Reflection with authoritative history and governing context."""
from pathlib import Path
from app.repositories.learning_event_repository import LearningEventNotFoundError
from app.services.cognition.reflection.reflection_api import ReflectionAPIRequest


class GoverningContextUnavailableError(RuntimeError):
    pass


class WorkspaceReflectionService:
    def __init__(self, *, repository, application_service, canon_root: Path):
        self.repository = repository
        self.application_service = application_service
        self.canon_root = canon_root

    def reflect(self, request):
        events = self.repository.get_many(request.learning_event_ids)
        if any(event.metadata.get("organization_id", "default") != request.organization_id for event in events):
            raise LearningEventNotFoundError("Selected history is unavailable in this organization.")
        context_paths = [self.canon_root / "philosophy" / "SENTINELAI_PRINCIPLES.md",
                         self.canon_root / "architecture" / "cognitive" / "COGNITIVE_ARCHITECTURE_DOCTRINE.md"]
        context = "\n\n".join(path.read_text(encoding="utf-8") for path in context_paths if path.exists())
        if not context.strip():
            raise GoverningContextUnavailableError("Governing context is unavailable.")
        return self.application_service.reflect(ReflectionAPIRequest(
            title=request.title, learning_event_ids=request.learning_event_ids,
            constitutional_context=context, organization_id=request.organization_id))
