"""In-memory authority/catalog contracts; no infrastructure imports or writes."""
import hashlib
from dataclasses import replace

import pytest
from pydantic import ValidationError

from evaluation.governed_answers.scope_catalog_contracts import (
    EvidenceScope, ScriptedIdentity, AuthoritySnapshot, DocumentVersion, CatalogSnapshot,
    EvidenceChunk, OfflineEligibilityGuard,
)


class Reader:
    execution_source = "unit_test"
    def __init__(self, value):
        self.value, self.calls, self.failure, self.hook = value, 0, False, None
    def read(self, **kwargs):
        self.calls += 1
        if self.failure:
            raise RuntimeError("private store detail")
        if self.hook:
            self.hook(self)
        return self.value


@pytest.fixture
def setup():
    scope = EvidenceScope(organization_id="org", collection="knowledge", module="engineering", topic="policy")
    identity = ScriptedIdentity(principal_id="fixture-admin")
    doc = DocumentVersion(document_id="doc", scope=scope, state="indexed", lifecycle_epoch=3,
        content_epoch=2, index_epoch=2, file_sha256="a"*64,
        chunk_hashes=(hashlib.sha256(b"Source text.").hexdigest(),))
    authority = Reader(AuthoritySnapshot(principal_id=identity.principal_id, permission_epoch=4, grants=(scope,)))
    catalog = Reader(CatalogSnapshot(scope=scope, revision=5, documents=(doc,)))
    chunk = EvidenceChunk(document_id="doc", scope=scope, chunk_index=0, text="Source text.",
        file_sha256=doc.file_sha256, lifecycle_epoch=3, content_epoch=2, index_epoch=2)
    guard = OfflineEligibilityGuard(authority_reader=authority, catalog_reader=catalog)
    args = dict(identity=identity, scope=scope, request_id="request-1", question="What is stated?", evidence=(chunk,))
    return guard, args, authority, catalog


def closed(result):
    assert result.authenticated_scope_verified is result.release_authorized is result.production_enabled is False
    assert result.execution_source == "unit_test" and result.proposition_to_inference == "closed"
    if not result.eligible_fixture:
        assert result.context is None


def test_capture_and_repeated_check_are_bound_and_offline(setup):
    guard, args, _, _ = setup
    capture = guard.capture(**args)
    assert capture.eligible_fixture
    assert len(capture.context.context_sha256) == 64
    assert capture.context.context_sha256 == hashlib.sha256(capture.context.context_json.encode()).hexdigest()
    for _ in range(2):
        result = guard.recheck(capture.context)
        closed(result)
        assert result.eligible_fixture


@pytest.mark.parametrize("field", ["organization_id", "collection", "module", "topic"])
def test_client_scope_cannot_expand_grants(setup, field):
    guard, args, _, catalog = setup
    args["scope"] = args["scope"].model_copy(update={field: "other"})
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture and catalog.calls == 0


@pytest.mark.parametrize("identity", [None, {"principal_id": "fixture-admin"}, {"X-User": "fixture-admin"}])
def test_absent_or_header_identity_is_not_authority(setup, identity):
    guard, args, authority, catalog = setup
    args["identity"] = identity
    closed(guard.capture(**args))
    assert authority.calls == catalog.calls == 0


@pytest.mark.parametrize("mode", ["wrong_principal", "revoked", "failure", "non_scripted", "malformed"])
def test_authority_denied_before_catalog(setup, mode):
    guard, args, authority, catalog = setup
    if mode == "wrong_principal": authority.value = authority.value.model_copy(update={"principal_id": "other"})
    if mode == "revoked": authority.value = authority.value.model_copy(update={"grants": ()})
    if mode == "failure": authority.failure = True
    if mode == "non_scripted": authority.execution_source = "actual_api"
    if mode == "malformed": authority.value = {}
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture and catalog.calls == 0
    assert "private store detail" not in repr(result)


@pytest.mark.parametrize("state", ["pending", "archiving", "archived", "restoring", "failed", "deleting", "tombstoned"])
def test_only_indexed_documents_are_eligible(setup, state):
    guard, args, _, catalog = setup
    catalog.value = catalog.value.model_copy(update={"documents": (catalog.value.documents[0].model_copy(update={"state": state}),)})
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture


@pytest.mark.parametrize("field,value", [("lifecycle_epoch", 4), ("content_epoch", 3), ("index_epoch", 3),
    ("file_sha256", "b"*64), ("text", "Other text."), ("chunk_index", 1), ("document_id", "foreign")])
def test_stale_or_unbound_chunks_deny(setup, field, value):
    guard, args, _, _ = setup
    args["evidence"] = (args["evidence"][0].model_copy(update={field: value}),)
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture


@pytest.mark.parametrize("mode", ["missing_document", "missing_manifest", "stale_index", "foreign_catalog", "duplicate", "empty", "oversize"])
def test_invalid_catalog_or_coverage_deny(setup, mode):
    guard, args, _, catalog = setup
    doc = catalog.value.documents[0]
    if mode == "missing_document": catalog.value = catalog.value.model_copy(update={"documents": ()})
    if mode == "missing_manifest": catalog.value = catalog.value.model_copy(update={"documents": (doc.model_copy(update={"chunk_hashes": ()}),)})
    if mode == "stale_index": catalog.value = catalog.value.model_copy(update={"documents": (doc.model_copy(update={"index_epoch": 1}),)})
    if mode == "foreign_catalog": catalog.value = catalog.value.model_copy(update={"scope": doc.scope.model_copy(update={"organization_id": "other"})})
    if mode == "duplicate": args["evidence"] *= 2
    if mode == "empty": args["evidence"] = ()
    if mode == "oversize": args["evidence"] *= 26
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture


@pytest.mark.parametrize("mutation", ["permission_epoch", "revocation", "revision", "archive_restore", "delete_recreate", "content", "failure"])
def test_changes_after_capture_deny_terminally(setup, mutation):
    guard, args, authority, catalog = setup
    capture = guard.capture(**args)
    original_authority, original_catalog = authority.value, catalog.value
    if mutation == "permission_epoch": authority.value = authority.value.model_copy(update={"permission_epoch": 5})
    if mutation == "revocation": authority.value = authority.value.model_copy(update={"grants": ()})
    if mutation == "revision": catalog.value = catalog.value.model_copy(update={"revision": 6})
    if mutation in {"archive_restore", "delete_recreate", "content"}:
        doc = catalog.value.documents[0]
        field = "content_epoch" if mutation == "content" else "lifecycle_epoch"
        catalog.value = catalog.value.model_copy(update={"documents": (doc.model_copy(update={field: getattr(doc, field)+2}),)})
    if mutation == "failure": catalog.failure = True
    denied = guard.recheck(capture.context)
    closed(denied)
    assert not denied.eligible_fixture
    authority.value, catalog.value, catalog.failure = original_authority, original_catalog, False
    assert not guard.recheck(capture.context).eligible_fixture


@pytest.mark.parametrize("which", ["authority", "catalog"])
def test_observed_torn_snapshots_deny(setup, which):
    guard, args, authority, catalog = setup
    reader = authority if which == "authority" else catalog
    def mutate(reader):
        if reader.calls == 2:
            field = "permission_epoch" if which == "authority" else "revision"
            reader.value = reader.value.model_copy(update={field: getattr(reader.value, field)+1})
    reader.hook = mutate
    result = guard.capture(**args)
    closed(result)
    assert not result.eligible_fixture


@pytest.mark.parametrize("mode", ["clone", "cross_session", "tampered", "no_capture"])
def test_forged_context_cannot_be_rechecked(setup, mode):
    guard, args, authority, catalog = setup
    capture = guard.capture(**args)
    context = capture.context
    if mode == "clone": context = replace(context)
    if mode == "cross_session": guard = OfflineEligibilityGuard(authority_reader=authority, catalog_reader=catalog)
    if mode == "tampered": object.__setattr__(context, "context_json", "{}")
    if mode == "no_capture": context = None
    result = guard.recheck(context)
    closed(result)
    assert not result.eligible_fixture


@pytest.mark.parametrize("at_capture", [True, False])
def test_expiration_does_not_reopen_session(setup, at_capture):
    _, args, authority, catalog = setup
    now = [100.0]
    guard = OfflineEligibilityGuard(authority_reader=authority, catalog_reader=catalog, clock=lambda: now[0])
    capture = None if at_capture else guard.capture(**args)
    now[0] += 3
    result = guard.capture(**args) if at_capture else guard.recheck(capture.context)
    closed(result)
    assert result.reason == "request_expired"


def test_repeated_capture_cannot_replace_bound_request(setup):
    guard, args, _, _ = setup
    capture = guard.capture(**args)
    args["question"] = "Different question?"
    denied = guard.capture(**args)
    closed(denied)
    assert denied.reason == "context_already_captured"
    assert not guard.recheck(capture.context).eligible_fixture


@pytest.mark.parametrize("value", ["*", "all", " "])
def test_wildcards_are_invalid(value):
    with pytest.raises(ValidationError):
        EvidenceScope(organization_id=value, collection="knowledge", module="engineering", topic="policy")


def test_model_metadata_cannot_supply_authority_or_authorization():
    with pytest.raises(ValidationError):
        ScriptedIdentity(principal_id="admin", authenticated=True)
    with pytest.raises(ValidationError):
        AuthoritySnapshot(principal_id="admin", permission_epoch=0, grants=(), release_authorized=True)
