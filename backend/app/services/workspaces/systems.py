"""Observe availability independently from cognitive or constitutional acceptance."""
from datetime import datetime, timezone
import os
from sqlalchemy import inspect, text
from app.database import engine
from app.services.qdrant_service import client, COLLECTION_NAME
from app.services.core_memory_service import CORE_COLLECTION_NAME
from app.services.workspaces.models import ServiceObservation, SystemsSnapshot


class SystemsObserver:
    def __init__(self, database=engine, vectors=client):
        self.database = database
        self.vectors = vectors

    def observe(self) -> SystemsSnapshot:
        services = []
        try:
            with self.database.connect() as connection:
                connection.execute(text("SELECT 1"))
                tables = set(inspect(connection).get_table_names())
            missing = {"documents", "reflection_history"} - tables
            services.append(ServiceObservation(name="Persistent history", status="migration_required" if missing else "ready",
                                               detail="Required storage tables are missing." if missing else "Document catalog and reflection history are available."))
        except Exception:
            services.append(ServiceObservation(name="Persistent history", status="unavailable", detail="Persistent storage could not be reached."))
        try:
            names = {collection.name for collection in self.vectors.get_collections().collections}
            for name, title in [(COLLECTION_NAME, "Knowledge memory"), (CORE_COLLECTION_NAME, "Principle memory")]:
                if name not in names:
                    services.append(ServiceObservation(name=title, status="initialization_required", detail="Memory collection has not been initialized."))
                else:
                    count = self.vectors.count(collection_name=name, exact=True).count
                    services.append(ServiceObservation(name=title, status="ready" if count else "empty", detail=f"{count} stored memory chunks."))
        except Exception:
            services.append(ServiceObservation(name="Vector memory", status="unavailable", detail="Vector memory could not be reached."))
        configured = bool(os.getenv("OPENAI_API_KEY", "").strip())
        warnings = [s.detail for s in services if s.status not in {"ready", "empty"}]
        if not configured:
            warnings.append("Model credentials are not configured; Recall, Reason, Planning, and Verification are unavailable.")
        warnings.append("Constitutional semantic judgment and Sprint 20.3 semantic grounding have not been independently verified.")
        return SystemsSnapshot(observed_at=datetime.now(timezone.utc).isoformat(),
                               status="degraded" if any(s.status not in {"ready", "empty"} for s in services) else "ready",
                               services=services, model_features_configured=configured, warnings=warnings)
