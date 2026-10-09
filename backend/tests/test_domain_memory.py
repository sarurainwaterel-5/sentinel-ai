from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient
from app.models.document import Document
from app.services.workspaces.domain_memory import observe_domain_memory


def test_memory_counts_preserve_scope_status_and_zero_chunks():
    engine = create_engine("sqlite://")
    Document.__table__.create(engine)
    with Session(engine) as db:
        for id, organization, status, chunks in [("a","default","indexed",119),("b","default","archived",5),("c","other","indexed",999),("d","default","indexed",0),("e","default","failed",0)]:
            db.add(Document(id=id,filename=id+".pdf",file_hash=id,module="trading",organization_id=organization,status=status,chunk_count=chunks,embedding_model="model"))
        db.commit()
        observed = observe_domain_memory(db)
        assert observed["domains"]["trading"] == {"indexed_documents":2,"indexed_chunks":119,"archived_documents":1,"other_documents":1}
        assert observe_domain_memory(db,"empty")["domains"] == {}
        assert observed["organization_id"] == "default"


def test_memory_route_is_not_treated_as_a_domain_identifier():
    from app.main import app
    from app.database import get_db
    engine = create_engine("sqlite://",connect_args={"check_same_thread":False},poolclass=StaticPool)
    Document.__table__.create(engine)
    def session():
        with Session(engine) as db: yield db
    app.dependency_overrides[get_db] = session
    try:
        result = TestClient(app).get("/domains/memory")
        assert result.status_code == 200
        assert result.json()["domains"] == {}
        assert TestClient(app).get("/domains/memory?organization_id=%20").status_code == 422
    finally:
        app.dependency_overrides.pop(get_db,None)


def test_memory_failure_is_bounded(monkeypatch):
    from app.main import app
    from app.database import get_db
    from app.routes import domains
    from sqlalchemy.exc import OperationalError
    def fail(*args): raise OperationalError("secret-db-details",{},RuntimeError("private"))
    monkeypatch.setattr(domains,"observe_domain_memory",fail)
    app.dependency_overrides[get_db] = lambda: None
    try:
        response = TestClient(app).get("/domains/memory")
        assert response.status_code == 503
        assert "retry" in response.json()["detail"]
        assert "secret" not in response.text
    finally:
        app.dependency_overrides.pop(get_db,None)
