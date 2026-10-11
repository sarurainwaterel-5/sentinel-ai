"""Isolated ASGI boundary tests: no application lifespan, storage or provider work."""
import ast
import importlib
from pathlib import Path
import pytest
from fastapi import FastAPI
from httpx import AsyncClient, ASGITransport
from app.routes import governed_answers


pytestmark = pytest.mark.anyio


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
async def client():
    app=FastAPI()
    app.include_router(governed_answers.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as value:
        yield value


async def test_readiness_is_disabled_without_environment_or_providers(client,monkeypatch):
    monkeypatch.setenv("GOVERNED_ANSWERS_ENABLED","true")
    monkeypatch.setenv("SEMANTIC_GROUNDING_VERIFIED","true")
    payload=(await client.get("/cognition/answer/readiness")).json()
    assert payload["enabled"] is False and payload["status"]=="disabled"
    assert payload["semantic_grounding_verified"] is False
    assert payload["proposition_to_inference"]=="closed"
    assert len(payload["blockers"])==3


async def test_disabled_post_returns_inspectable_503_not_generated_content(client):
    response=await client.post("/cognition/answer",json={"question":" Test question ","module":"engineering"})
    assert response.status_code==503
    payload=response.json()
    assert payload["question"]=="Test question"
    assert payload["answer_text"] is None and payload["claims"]==[] and payload["evidence"]==[]
    assert payload["validation"]["release_status"]=="disabled"
    assert payload["scope"]["module"]=="engineering"


@pytest.mark.parametrize("body", [{"question":" "},{"question":"Q","enable":True},{"question":"Q","limit":26},{"question":"Q","limit":"5"}])
async def test_malformed_request_never_crosses_disabled_boundary(client,body):
    assert (await client.post("/cognition/answer",json=body)).status_code==422


async def test_client_cannot_claim_other_organization(client):
    assert (await client.post("/cognition/answer",json={"question":"Q","organization_id":"other"})).status_code==403


async def test_disabled_routes_import_no_execution_dependencies(monkeypatch):
    from app.services.cognition.reasoning.answer_orchestrator import OfflineAnswerCoordinator
    def forbidden(*args,**kwargs):
        raise AssertionError("Disabled route crossed cognitive boundary")
    monkeypatch.setattr(OfflineAnswerCoordinator,"__init__",forbidden)
    importlib.reload(governed_answers)
    app=FastAPI();app.include_router(governed_answers.router)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        assert (await client.post("/cognition/answer",json={"question":"Q"})).status_code==503
    tree=ast.parse(Path(governed_answers.__file__).read_text())
    imports=[n.module or "" for n in ast.walk(tree) if isinstance(n,ast.ImportFrom)]
    assert not any(any(term in value for term in ("orchestrator","retrieval","providers","inference","openai")) for value in imports)
