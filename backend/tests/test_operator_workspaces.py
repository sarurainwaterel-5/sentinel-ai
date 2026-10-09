from types import SimpleNamespace
from datetime import datetime, UTC, timedelta

import pytest
from sqlalchemy import create_engine, text
from fastapi.testclient import TestClient

from app.services.workspaces.connections import ConnectionEngine
from app.services.workspaces.systems import SystemsObserver
from app.services.workspaces.learning_history import IngestionHistoryRecorder
from app.repositories.learning_event_repository import LearningEventRepository
from app.core.cognition.models import LearningEvent
from app.services.cognition.coherence.coherence_engine import CoherenceEngine
from app.services.qdrant_service import COLLECTION_NAME
from app.services.core_memory_service import CORE_COLLECTION_NAME


def document(root, path, content):
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def test_connections_preserve_duplicate_filenames_and_resolve_exact_relative_links(tmp_path):
    document(tmp_path, "a/README.md", "# Alpha\n[Beta](../b/README.md)")
    document(tmp_path, "b/README.md", "# Beta")
    result = ConnectionEngine(tmp_path).inspect()
    ids = {node["id"] for node in result["nodes"]}
    assert {"document:a/README.md", "document:b/README.md"} <= ids
    assert any(edge["source"] == "document:a/README.md" and edge["target"] == "document:b/README.md" for edge in result["edges"])
    assert all(edge["source"] in ids and edge["target"] in ids for edge in result["edges"])


def test_ambiguous_and_missing_references_do_not_acquire_invented_provenance(tmp_path):
    document(tmp_path, "ADR-026-First.md", "# First")
    document(tmp_path, "ADR-026-Second.md", "# Second")
    document(tmp_path, "Sprint-1.0.md", "# Sprint\nADR-026 ADR-999 [outside](../secret.md)")
    result = ConnectionEngine(tmp_path).inspect()
    assert {item["reason"] for item in result["unresolved_references"]} == {"ambiguous_reference", "missing_document"}
    assert not any(edge["relationship"] == "references" for edge in result["edges"])


def test_connections_are_deterministic_and_do_not_promote_mentions_to_implementation(tmp_path):
    document(tmp_path, "ADR-001-Decision.md", "# Decision")
    document(tmp_path, "Sprint-1.0.md", "# Sprint\nADR-001")
    engine = ConnectionEngine(tmp_path)
    assert engine.inspect() == engine.inspect()
    assert set(engine.inspect()["relationships"]) == {"belongs_to", "classified_as", "references"}


class Vectors:
    def __init__(self, names): self.names = names
    def get_collections(self): return SimpleNamespace(collections=[SimpleNamespace(name=name) for name in self.names])
    def count(self, **kwargs): return SimpleNamespace(count=7)


def test_systems_check_schema_and_collections_instead_of_assuming_health(monkeypatch):
    engine = create_engine("sqlite://")
    monkeypatch.setenv("OPENAI_API_KEY", "do-not-disclose-this-secret")
    result = SystemsObserver(engine, Vectors([])).observe()
    assert result.status == "degraded"
    assert any(item.status == "migration_required" for item in result.services)
    assert any(item.status == "initialization_required" for item in result.services)
    assert "do-not-disclose" not in result.model_dump_json()
    assert result.semantic_grounding_verified is False
    with engine.begin() as connection:
        connection.execute(text("CREATE TABLE documents (id TEXT)"))
        connection.execute(text("CREATE TABLE reflection_history (id TEXT)"))
    result = SystemsObserver(engine, Vectors([COLLECTION_NAME, CORE_COLLECTION_NAME])).observe()
    assert result.status == "ready"
    assert result.constitutional_evaluation == "not_verified"


def test_unavailable_services_are_bounded_observations_without_secret_errors():
    class Failed:
        def connect(self): raise RuntimeError("password=secret")
        def get_collections(self): raise RuntimeError("api_key=secret")
    result = SystemsObserver(Failed(), Failed()).observe()
    assert result.status == "degraded"
    assert all(item.status == "unavailable" for item in result.services)
    assert "secret" not in result.model_dump_json()


def test_unassessed_constitutional_result_fails_closed():
    result = CoherenceEngine().evaluate(question="Helpful question", identity_context="Sentinel's principles", knowledge_context="A confident recommendation")
    assert result.coherent is False
    assert result.constitutional_score == 0
    assert result.articles_consulted == []
    assert result.conflicts


def test_history_reads_are_scoped_bounded_and_preserve_original_outcomes(tmp_path):
    repository = LearningEventRepository(database_path=tmp_path / "events.sqlite3")
    now = datetime.now(UTC)
    for index in range(3):
        repository.save(LearningEvent(learning_event_id=str(index), learned_at=now + timedelta(seconds=index), metadata={"organization_id": "other" if index == 2 else "default"}))
    records = repository.recent_for_organization("default", 1)
    assert [event.learning_event_id for event in records] == ["1"]
    assert [event.learning_event_id for event in repository.recent_for_organization("other")] == ["2"]


def test_ingestion_history_records_facts_once_without_manufacturing_understanding(tmp_path):
    repository = LearningEventRepository(database_path=tmp_path / "events.sqlite3")
    recorder = IngestionHistoryRecorder(repository)
    result = {"document_id": "d1", "filename": "proof.pdf", "file_hash": "abc", "module": "engineering", "chunks": 2}
    first = recorder.record(result, "owner")
    second = recorder.record(result, "owner")
    assert first.to_dict() == second.to_dict()
    assert len(repository.recent_for_organization("owner")) == 1
    assert first.evidence_added == ["document:d1:chunk:0", "document:d1:chunk:1"]
    assert first.understandings_added == []
    assert first.concepts_added == []


def test_workspace_reflection_rejects_cross_organization_history_before_cognition(tmp_path, monkeypatch):
    from app.main import app
    from app.database import get_db
    from app.routes import workspaces
    repository = LearningEventRepository(database_path=tmp_path / "events.sqlite3")
    repository.save(LearningEvent(learning_event_id="private", metadata={"organization_id": "other"}))
    monkeypatch.setattr(workspaces, "repository", repository)
    app.dependency_overrides[get_db] = lambda: None
    try:
        response = TestClient(app).post("/intelligence/reflection", json={"title": "Inspect history", "learning_event_ids": ["private"]})
        assert response.status_code == 404
        response = TestClient(app).post("/intelligence/reflection", json={"title": "Inspect history", "learning_event_ids": ["missing"]})
        assert response.status_code == 404
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_workspace_history_limits_are_validated():
    from app.main import app
    client = TestClient(app)
    assert client.get("/intelligence/learning-events?limit=10001").status_code == 422


def test_real_reflection_preserves_rejected_outcome_and_history_scope(tmp_path, monkeypatch):
    from app.main import app
    from app.database import get_db
    from app.routes import workspaces
    from app.models.reflection_history import ReflectionHistoryRecordModel
    from app.services.cognition.reflection.learning_event_resolver import LearningEventResolver
    from sqlalchemy.orm import Session
    from sqlalchemy.pool import StaticPool
    repository = LearningEventRepository(database_path=tmp_path / "events.sqlite3")
    for event_id in ["first", "second"]:
        repository.save(LearningEvent(learning_event_id=event_id, source="recorded.pdf", domain_ids=["engineering"], evidence_added=["document:actual-source:chunk:0"]))
    monkeypatch.setattr(workspaces, "repository", repository)
    monkeypatch.setattr(workspaces, "resolver", LearningEventResolver(repository=repository))
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    ReflectionHistoryRecordModel.__table__.create(engine)
    def session():
        with Session(engine) as db:
            yield db
    app.dependency_overrides[get_db] = session
    try:
        client = TestClient(app)
        result = client.post("/intelligence/reflection", json={"title": "Examine recurrence", "learning_event_ids": ["first", "second"]})
        assert result.status_code == 200, result.text
        assert result.json()["admissible"] is False
        assert result.json()["pattern_count"] >= 1
        records = client.get("/reflection/history").json()
        assert len(records) == 1
        assert records[0]["admissible"] is False
        assert records[0]["learning_event_ids"] == ["first", "second"]
        assert client.get("/reflection/history?organization_id=other").json() == []
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_provider_failure_is_bounded_and_actionable(monkeypatch):
    from app.main import app
    from app.routes import planning
    from openai import AuthenticationError
    import httpx
    monkeypatch.setenv("OPENAI_API_KEY", "configured")
    class FailedPlanner:
        def plan(self, request):
            raise AuthenticationError("sensitive-provider-payload", response=httpx.Response(401, request=httpx.Request("POST", "https://provider.example")), body=None)
    monkeypatch.setattr(planning, "PlanningOrchestrator", FailedPlanner)
    response = TestClient(app).post("/cognition/plan", json={"objective": "Inspect a plan"})
    assert response.status_code == 503
    assert "rejected" in response.json()["detail"]
    assert "sensitive" not in response.text


@pytest.mark.parametrize("payload", [
    {"title": "   ", "learning_event_ids": ["event"]},
    {"title": "Reflect", "learning_event_ids": [" "]},
    {"title": "Reflect", "learning_event_ids": ["event"], "organization_id": " "},
])
def test_workspace_reflection_rejects_blank_inputs_before_workflow(payload):
    from app.main import app
    from app.database import get_db
    app.dependency_overrides[get_db] = lambda: None
    try:
        assert TestClient(app).post("/intelligence/reflection", json=payload).status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_recall_vector_transport_failure_is_retryable_and_does_not_claim_missing_evidence(monkeypatch):
    from app.main import app
    from app.routes import ask
    from qdrant_client.http.exceptions import ResponseHandlingException
    monkeypatch.setenv("OPENAI_API_KEY", "configured")
    class FailedRecall:
        def answer_question(self, **kwargs):
            raise ResponseHandlingException(RuntimeError("sensitive-vector-connection"))
    monkeypatch.setattr(ask, "ReasoningService", FailedRecall)
    response = TestClient(app).post("/ask", json={"question": "What is a fair value gap?", "module": "trading"})
    assert response.status_code == 503
    assert "retry" in response.json()["detail"]
    assert "preserved" in response.json()["detail"]
    assert "sensitive" not in response.text
    assert "not have enough evidence" not in response.text
