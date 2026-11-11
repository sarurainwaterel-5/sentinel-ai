"""Actual SQLite + scrypt + ASGI transport integration, no paid provider calls."""
import base64
from pathlib import Path

import httpx
import pytest

from evaluation.governed_answers.isolated_acceptance_app import create_isolated_acceptance_app
from evaluation.governed_answers.isolated_sqlite_identity import IsolatedAuthorityStore
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.sqlite_catalog import IsolatedCatalog

ROOT = Path(__file__).resolve().parents[2]
SCOPE = EvidenceScope(organization_id="org", collection="kb", module="engineering", topic="policy")
HEADER = "Basic " + base64.b64encode(b"acceptance-user:disposable-password").decode()


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def stores(tmp_path):
    authority = IsolatedAuthorityStore(tmp_path / "authority.db")
    authority.provision(username="acceptance-user", principal_id="acceptance-principal",
                        password="disposable-password", grants=(SCOPE,))
    catalog = IsolatedCatalog.create(tmp_path / "catalog.db")
    catalog.put(operation_id="create", document_id="doc", scope=SCOPE,
                source=b"acceptance source", chunks=(b"Retention is 30 days.",))
    app = create_isolated_acceptance_app(authority_store=authority, catalog=catalog, repository_root=ROOT)
    yield authority, catalog, app
    authority.close()
    catalog.close()


async def post(app, path, *, headers=None, scope=SCOPE):
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://acceptance") as client:
        return await client.post(path, json={"scope": scope.model_dump(), "document_id": "doc"}, headers=headers)


@pytest.mark.anyio
async def test_real_scoped_sql_source_inspection_and_literal_release_denial(stores):
    _, _, app = stores
    response = await post(app, "/integration/inspect-source", headers={"Authorization": HEADER})
    assert response.status_code == 200
    data = response.json()
    assert data["source"]["chunks"] == ["Retention is 30 days."]
    assert data["execution_source"] == "isolated_sqlite_http"
    assert data["governed_eligible"] is data["production_enabled"] is data["release_authorized"] is False
    denied = await post(app, "/integration/answer", headers={"Authorization": HEADER})
    assert denied.status_code == 503 and denied.json()["answer_text"] is None
    assert "empirical_report_missing" in denied.json()["blockers"]
    assert "disposable-password" not in response.text + denied.text


@pytest.mark.anyio
@pytest.mark.parametrize("headers", [None, {"Authorization": "Bearer invalid"},
    [("Authorization", HEADER), ("Authorization", HEADER)], {"Authorization": "Basic dXNlcjp3cm9uZw=="}])
async def test_authentication_denies_before_source_inspection(stores, headers):
    _, catalog, app = stores
    def forbidden(*args, **kwargs):
        raise AssertionError("Unauthenticated retrieval attempted")
    catalog.snapshot = forbidden
    result = await post(app, "/integration/inspect-source", headers=headers)
    assert result.status_code == 401 and "Retention" not in result.text


@pytest.mark.anyio
async def test_exact_foreign_scope_denied(stores):
    _, _, app = stores
    response = await post(app, "/integration/inspect-source", headers={"Authorization": HEADER},
                          scope=SCOPE.model_copy(update={"topic": "foreign"}))
    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize("mutation", ["archive", "delete", "revoke", "rotate", "replace"])
async def test_sql_lifecycle_and_authority_races_withhold_source(stores, mutation):
    authority, catalog, app = stores
    original = catalog.evidence
    def race(**kwargs):
        result = original(**kwargs)
        if mutation in {"archive", "delete"}:
            catalog.transition(operation_id="change", document_id="doc", expected_lifecycle=1,
                               state="archived" if mutation == "archive" else "tombstoned")
        if mutation == "revoke": authority.set_grants(username="acceptance-user", grants=())
        if mutation == "rotate": authority.rotate(username="acceptance-user", password="new-disposable")
        if mutation == "replace":
            catalog.put(operation_id="change", document_id="doc", scope=SCOPE,
                        expected_lifecycle=1, source=b"changed", chunks=(b"changed",))
        return result
    catalog.evidence = race
    response = await post(app, "/integration/inspect-source", headers={"Authorization": HEADER})
    assert response.status_code == 409 and "Retention" not in response.text


@pytest.mark.anyio
async def test_disabled_answer_gate_performs_no_retrieval(stores):
    _, catalog, app = stores
    def forbidden(*args, **kwargs):
        raise AssertionError("Disabled answer attempted retrieval")
    catalog.evidence = catalog.snapshot = forbidden
    response = await post(app, "/integration/answer", headers={"Authorization": HEADER})
    assert response.status_code == 503
