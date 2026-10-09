from threading import BoundedSemaphore
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.database import get_db
from app.models.teaching_mission import TeachingMission
from app.routes import teaching as routes
from app.services.workspaces import teaching as service


@pytest.fixture
def setup(tmp_path, monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TeachingMission.__table__.create(engine)
    factory = sessionmaker(engine)
    semaphore = BoundedSemaphore(8)
    monkeypatch.setattr(routes, "UPLOAD_DIR", tmp_path)
    monkeypatch.setattr(routes, "slots", semaphore)
    monkeypatch.setattr(service, "slots", semaphore)
    monkeypatch.setattr(service, "SessionLocal", factory)
    class FakeUpload:
        def __init__(self, db): pass
        def process_saved_pdf(self, **kwargs):
            for stage in ["fingerprinting", "extracting", "chunking", "indexing", "cataloging", "recording"]:
                kwargs["progress"](stage)
            return {"status": "indexed", "filename": kwargs["filename"], "module": kwargs["module"], "chunks": 3, "document_id": "doc", "learning_event_id": "event"}
    monkeypatch.setattr(service, "UploadService", FakeUpload)
    app = FastAPI(); app.include_router(routes.router)
    def db():
        with factory() as session: yield session
    app.dependency_overrides[get_db] = db
    return TestClient(app), factory, engine


def submit(client, **data):
    return client.post("/teach/missions", data={"module": "trading", **data}, files={"file": ("source.pdf", b"%PDF-test", "application/pdf")})


def test_accepted_mission_observes_real_worker_stages_and_scoped_history(setup):
    client, factory, _ = setup
    accepted = submit(client)
    assert accepted.status_code == 202
    assert accepted.json()["status"] == "queued"
    assert "file_path" not in accepted.json()
    mission_id = accepted.json()["id"]
    completed = client.get(f"/teach/missions/{mission_id}").json()
    assert completed["status"] == "completed"
    assert [event["stage"] for event in completed["events"]] == ["received", "fingerprinting", "extracting", "chunking", "indexing", "cataloging", "recording", "finished"]
    assert completed["result"]["chunks"] == 3
    assert client.get(f"/teach/missions/{mission_id}?organization_id=other").status_code == 404
    assert client.get("/teach/missions?organization_id=other").json() == []
    assert client.get("/teach/missions?domain_id=engineering").json() == []
    assert len(client.get("/teach/missions?domain_id=trading").json()) == 1


def test_failure_is_bounded_and_partial_progress_is_retained(setup, monkeypatch):
    client, _, _ = setup
    def fail(self, **kwargs):
        kwargs["progress"]("extracting")
        raise RuntimeError("private provider/storage credentials")
    monkeypatch.setattr(service.UploadService, "process_saved_pdf", fail)
    mission = client.get(f"/teach/missions/{submit(client).json()['id']}").json()
    assert mission["status"] == "failed"
    assert "private" not in str(mission)
    assert [event["stage"] for event in mission["events"]] == ["received", "extracting", "failed"]


def test_duplicate_does_not_create_later_stage_observations(setup, monkeypatch):
    client, _, _ = setup
    def duplicate(self, **kwargs):
        kwargs["progress"]("fingerprinting")
        return {"status": "duplicate", "existing_document": {"module": "engineering"}}
    monkeypatch.setattr(service.UploadService, "process_saved_pdf", duplicate)
    mission = client.get(f"/teach/missions/{submit(client).json()['id']}").json()
    assert mission["status"] == "duplicate"
    assert [event["stage"] for event in mission["events"]] == ["received", "fingerprinting", "finished"]


@pytest.mark.parametrize("module", ["all", "unknown-domain"])
def test_invalid_context_rejected_before_upload(setup, module):
    client, _, _ = setup
    assert submit(client, module=module).status_code == 422
    assert client.get("/teach/missions").json() == []


def test_restart_preserves_interrupted_jobs_as_history(setup):
    client, factory, engine = setup
    with factory() as db:
        mission = TeachingMission(id="pending", organization_id="default", domain_id="trading", filename="old.pdf", file_path="/never-expose", topic="general", status="running", stage="indexing", created_at="2026-10-09", updated_at="2026-10-09", events=[{"stage": "indexing", "at": "2026-10-09"}])
        db.add(mission); db.commit()
    service.recover_interrupted(engine, factory)
    observed = client.get("/teach/missions/pending").json()
    assert observed["status"] == "interrupted"
    assert observed["events"][0]["stage"] == "indexing"
    assert "file_path" not in observed
    service.recover_interrupted(engine, factory)
    assert len(client.get("/teach/missions/pending").json()["events"]) == 2


def test_queue_is_bounded_and_rejected_input_releases_capacity(setup, monkeypatch):
    client, _, _ = setup
    for _ in range(8): assert routes.slots.acquire(False)
    assert submit(client).status_code == 429
    for _ in range(8): routes.slots.release()
    assert client.post("/teach/missions", data={"module": "trading"}, files={"file": ("bad.pdf", b"not-pdf")}).status_code == 415
    assert submit(client).status_code == 202
