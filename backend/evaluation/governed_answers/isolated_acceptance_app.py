"""Explicit unregistered HTTP acceptance harness over disposable SQL stores.

Source inspection exercises actual credentials and hash-checked relational bytes.
It never supplies governed answer evidence or opens the production release gate.
Instantiate and serve on the store-owning thread; this is not public HTTP auth.
"""
from pathlib import Path
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field

from app.services.cognition.reasoning.release_gate import inspect_release_gate
from .isolated_sqlite_identity import IsolatedAuthorityStore
from .scope_catalog_contracts import EvidenceScope
from .sqlite_catalog import IsolatedCatalog


class SourceInspectionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    scope: EvidenceScope
    document_id: str = Field(min_length=1, max_length=200)


def create_isolated_acceptance_app(*, authority_store, catalog, repository_root):
    """No implicit store creation, configuration lookup, providers or registration."""
    if type(authority_store) is not IsolatedAuthorityStore or type(catalog) is not IsolatedCatalog:
        raise ValueError("Explicit isolated stores required.")
    root = Path(repository_root)
    app = FastAPI(title="Sentinel isolated integration acceptance", docs_url=None, redoc_url=None)

    def authenticate(request, scope):
        session = authority_store.session()
        try:
            values = tuple(value.decode("ascii") for key, value in request.scope["headers"]
                           if key.lower() == b"authorization")
            identity = session.authenticate(authorization_values=values, scope=scope)
        except Exception:
            identity = None
        if identity is None:
            raise HTTPException(status_code=401, detail="Access denied.", headers={"WWW-Authenticate": "Basic"})
        return session

    @app.get("/integration/readiness")
    async def readiness():
        return inspect_release_gate(root)

    @app.post("/integration/inspect-source")
    async def inspect_source(body: SourceInspectionRequest, request: Request):
        started = time.monotonic()
        session = authenticate(request, body.scope)
        try:
            before = catalog.snapshot(body.scope)
            source = catalog.evidence(scope=body.scope, document_id=body.document_id)
            after = catalog.snapshot(body.scope)
            if before.sha256 != after.sha256 or not session.recheck() or time.monotonic() - started >= 3:
                raise ValueError("Changed integration state.")
        except Exception:
            raise HTTPException(status_code=409, detail="Source unavailable or changed.") from None
        return {"status": "isolated_source_inspection", "execution_source": "isolated_sqlite_http",
                "catalog_sha256": after.sha256, "source": source, "governed_eligible": False,
                "production_enabled": False, "release_authorized": False,
                "semantic_grounding_verified": False, "authenticated_scope_verified": False,
                "proposition_to_inference": "closed"}

    @app.post("/integration/answer")
    async def answer(body: SourceInspectionRequest, request: Request):
        session = authenticate(request, body.scope)
        gate = inspect_release_gate(root)
        if not session.recheck():
            raise HTTPException(status_code=401, detail="Access denied.")
        # Deliberately no retrieval/provider composition after a disabled gate.
        return JSONResponse(status_code=503, content={"status": "disabled", "answer_text": None,
            "claims": [], "blockers": gate["blockers"], "production_enabled": False,
            "release_authorized": False, "proposition_to_inference": "closed"})

    return app
