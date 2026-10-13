"""Synthetic credential/principal policy tests; no real authentication or hashes."""
import base64
from dataclasses import replace

import pytest
from pydantic import ValidationError

from evaluation.governed_answers.identity_resolution import (
    CredentialAttempt, PrincipalRecord, OfflinePrincipalResolver,
)
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope


def header(username="fixture-admin", password="synthetic-password"):
    return "Basic " + base64.b64encode(f"{username}:{password}".encode()).decode()


class Reader:
    execution_source = "unit_test"
    def __init__(self, record):
        self.record, self.calls, self.hook, self.failure = record, 0, None, False
    def read(self, *, username):
        self.calls += 1
        if self.failure: raise RuntimeError("synthetic-password private reader error")
        if self.hook: self.hook()
        return self.record


class Verifier:
    execution_source = "unit_test"
    supported_formats = ("fixture-v1",)
    def __init__(self):
        self.calls, self.hook, self.failure = 0, None, False
        self.result = True
    def verify(self, *, attempt, principal):
        self.calls += 1
        if self.failure: raise RuntimeError("synthetic-password private verifier error")
        if self.hook: self.hook()
        if attempt.password != "synthetic-password": return False
        return self.result


@pytest.fixture
def setup():
    scope = EvidenceScope(organization_id="org", collection="knowledge", module="engineering", topic="policy")
    reader = Reader(PrincipalRecord(username="fixture-admin", principal_id="principal-1", enabled=True,
        credential_version=2, credential_format="fixture-v1", permission_epoch=3, grants=(scope,)))
    verifier = Verifier()
    resolver = OfflinePrincipalResolver(principal_reader=reader, verifier=verifier)
    args = dict(authorization_values=(header(),), requested_scope=scope, request_id="request-1")
    return resolver, args, reader, verifier


def closed(result):
    assert result.authenticated_scope_verified is result.semantic_grounding_verified is False
    assert result.release_authorized is result.production_enabled is False
    assert result.proposition_to_inference == "closed"
    assert "synthetic-password" not in repr(result)
    if not result.verified_fixture: assert result.principal is None


def test_valid_fixture_resolves_and_rechecks_without_reverifying(setup):
    resolver, args, _, verifier = setup
    result = resolver.resolve(**args)
    closed(result)
    assert result.verified_fixture and verifier.calls == 1
    assert "synthetic-password" not in result.principal.context_json
    assert "Authorization" not in result.principal.context_json
    for _ in range(2):
        checked = resolver.recheck(result.principal)
        closed(checked)
        assert checked.verified_fixture
    assert verifier.calls == 1


@pytest.mark.parametrize("values", [None, [], (), (header(), header()), ("Bearer abc",),
    ("X-User: fixture-admin",), ("Basic",), ("Basic ",), ("Basic  YTpi",), ("Basic YTpi\n",),
    ("Basic !!!",), ("Basic YQ==",), (header("", "pass"),), (header("admin", ""),),
    (header(" admin", "pass"),), (header("admin", "pass\x00"),),
    ("Basic /w==",), ("Basic " + "a"*4096,), ({"Authorization": header()},),
    ("Basic YTpi=",)])
def test_malformed_or_duplicate_credentials_do_not_reach_reader(setup, values):
    resolver, args, reader, verifier = setup
    args["authorization_values"] = values
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture and reader.calls == verifier.calls == 0


def test_password_failure_is_terminal_with_no_retry(setup):
    resolver, args, _, verifier = setup
    args["authorization_values"] = (header(password="wrong"),)
    denied = resolver.resolve(**args)
    closed(denied)
    assert denied.reason == "credentials_rejected"
    args["authorization_values"] = (header(),)
    assert not resolver.resolve(**args).verified_fixture and verifier.calls == 1


@pytest.mark.parametrize("response", [None, False, 1, "true", {"verified": True}, {"release_authorized": True}])
def test_verifier_truthy_metadata_cannot_certify_identity(setup, response):
    resolver, args, _, verifier = setup
    verifier.result = response
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture


@pytest.mark.parametrize("mode", ["missing", "disabled", "wrong_username", "foreign_scope", "revoked", "unsupported_format", "reader_failure", "verifier_failure", "actual_reader", "actual_verifier"])
def test_denied_or_unavailable_capabilities_fail_closed(setup, mode):
    resolver, args, reader, verifier = setup
    if mode == "missing": reader.record = None
    if mode == "disabled": reader.record = reader.record.model_copy(update={"enabled": False})
    if mode == "wrong_username": reader.record = reader.record.model_copy(update={"username": "other"})
    if mode == "foreign_scope": args["requested_scope"] = args["requested_scope"].model_copy(update={"organization_id": "other"})
    if mode == "revoked": reader.record = reader.record.model_copy(update={"grants": ()})
    if mode == "unsupported_format": reader.record = reader.record.model_copy(update={"credential_format": "unsupported"})
    if mode == "reader_failure": reader.failure = True
    if mode == "verifier_failure": verifier.failure = True
    if mode == "actual_reader": reader.execution_source = "actual_api"
    if mode == "actual_verifier": verifier.execution_source = "actual_api"
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture
    if mode != "verifier_failure": assert verifier.calls == 0


@pytest.mark.parametrize("field,value", [("enabled", False), ("credential_version", 3),
    ("permission_epoch", 4), ("principal_id", "other"), ("grants", ()), ("credential_format", "unsupported")])
@pytest.mark.parametrize("during_verification", [True, False])
def test_rotation_and_revocation_are_detected(setup, field, value, during_verification):
    resolver, args, reader, verifier = setup
    original = reader.record
    def change(): reader.record = reader.record.model_copy(update={field: value})
    if during_verification:
        verifier.hook = change
        result = resolver.resolve(**args)
    else:
        initial = resolver.resolve(**args)
        change()
        result = resolver.recheck(initial.principal)
        reader.record = original
        assert not resolver.recheck(initial.principal).verified_fixture
    closed(result)
    assert not result.verified_fixture


@pytest.mark.parametrize("mode", ["clone", "cross_session", "tamper", "empty"])
def test_forged_handle_is_denied(setup, mode):
    resolver, args, reader, verifier = setup
    initial = resolver.resolve(**args)
    handle = initial.principal
    if mode == "clone": handle = replace(handle)
    if mode == "cross_session": resolver = OfflinePrincipalResolver(principal_reader=reader, verifier=verifier)
    if mode == "tamper": object.__setattr__(handle, "context_json", "{}")
    if mode == "empty": handle = None
    result = resolver.recheck(handle)
    closed(result)
    assert not result.verified_fixture


@pytest.mark.parametrize("stage", ["before", "reader", "verifier", "recheck"])
def test_deadline_covers_entire_identity_session(setup, stage):
    _, args, reader, verifier = setup
    now = [100.0]
    resolver = OfflinePrincipalResolver(principal_reader=reader, verifier=verifier, clock=lambda: now[0])
    def expire(): now[0] += 3
    if stage == "before": expire()
    if stage == "reader": reader.hook = expire
    if stage == "verifier": verifier.hook = expire
    if stage == "recheck":
        initial = resolver.resolve(**args)
        expire()
        result = resolver.recheck(initial.principal)
    else: result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture and result.reason == "identity_deadline_exceeded"


@pytest.mark.parametrize("mode", ["reader", "verifier", "formats"])
def test_capabilities_cannot_be_swapped_during_verification(setup, mode):
    resolver, args, reader, verifier = setup
    def swap():
        if mode == "reader": resolver.reader = Reader(reader.record)
        if mode == "verifier": resolver.verifier = Verifier()
        if mode == "formats": verifier.supported_formats = ("fixture-v1", "new-format")
    verifier.hook = swap
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture


@pytest.mark.parametrize("which", ["reader", "verifier"])
def test_async_callbacks_are_not_dispatched_by_sync_resolver(setup, which):
    resolver, args, reader, verifier = setup
    async def callback(**kwargs): raise AssertionError("Must not be dispatched")
    if which == "reader": reader.read = callback
    else: verifier.verify = callback
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture and verifier.calls == 0


def test_request_id_does_not_allow_second_resolution(setup):
    resolver, args, _, verifier = setup
    initial = resolver.resolve(**args)
    args["request_id"] = "request-2"
    closed(resolver.resolve(**args))
    assert not resolver.recheck(initial.principal).verified_fixture and verifier.calls == 1


def test_credential_attempt_hides_password_in_repr():
    assert "synthetic-password" not in repr(CredentialAttempt("admin", "synthetic-password"))


def test_extra_model_authorization_and_wildcard_grants_are_forbidden(setup):
    _, _, reader, _ = setup
    data = reader.record.model_dump()
    data["authenticated_scope_verified"] = True
    with pytest.raises(ValidationError): PrincipalRecord(**data)
    with pytest.raises(ValidationError): EvidenceScope(organization_id="*", collection="knowledge", module="engineering", topic="policy")


def test_scope_grants_are_not_a_cross_product(setup):
    resolver, args, reader, verifier = setup
    other = args["requested_scope"].model_copy(update={"module": "finance", "topic": "invoices"})
    reader.record = reader.record.model_copy(update={"grants": (*reader.record.grants, other)})
    args["requested_scope"] = args["requested_scope"].model_copy(update={"topic": "invoices"})
    result = resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture and verifier.calls == 0


def test_final_principal_read_cannot_issue_expired_handle(setup):
    _, args, reader, verifier = setup
    now = [100.0]
    resolver = OfflinePrincipalResolver(principal_reader=reader, verifier=verifier, clock=lambda: now[0])
    def expire_on_second_read():
        if reader.calls == 2: now[0] += 3
    reader.hook = expire_on_second_read
    result = resolver.resolve(**args)
    closed(result)
    assert result.reason == "identity_deadline_exceeded" and verifier.calls == 1


@pytest.mark.parametrize("value", [99.0, float("nan"), float("inf"), True])
def test_invalid_clock_cannot_extend_authority(setup, value):
    _, args, reader, verifier = setup
    now = [100.0]
    resolver = OfflinePrincipalResolver(principal_reader=reader, verifier=verifier, clock=lambda: now[0])
    initial = resolver.resolve(**args)
    now[0] = value
    result = resolver.recheck(initial.principal)
    closed(result)
    assert not result.verified_fixture


@pytest.mark.parametrize("during_recheck", [False, True])
def test_reader_cannot_swap_verifier_during_final_read(setup, during_recheck):
    resolver, args, reader, _ = setup
    initial = resolver.resolve(**args) if during_recheck else None
    def swap():
        if during_recheck or reader.calls == 2:
            resolver.verifier = Verifier()
    reader.hook = swap
    result = resolver.recheck(initial.principal) if during_recheck else resolver.resolve(**args)
    closed(result)
    assert not result.verified_fixture
