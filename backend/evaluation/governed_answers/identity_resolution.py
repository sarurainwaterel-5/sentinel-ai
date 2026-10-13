"""Isolated scripted credential verification and principal scope resolution.

No actual credentials, hash implementation, environment, HTTP dependency,
database, sessions, routes or production authentication are composed here.
"""
import base64
import hashlib
import inspect
import json
import math
import time
from dataclasses import dataclass, field
from typing import Literal

from pydantic import Field, model_validator

from .scope_catalog_contracts import EvidenceScope, Name, _Record, _json


class PrincipalRecord(_Record):
    username: Name
    principal_id: Name
    enabled: bool
    credential_version: int = Field(ge=0)
    credential_format: Name
    permission_epoch: int = Field(ge=0)
    grants: tuple[EvidenceScope, ...] = Field(max_length=100)
    execution_source: Literal["unit_test"] = "unit_test"

    @model_validator(mode="after")
    def unique_grants(self):
        if len(self.grants) != len({grant.model_dump_json() for grant in self.grants}):
            raise ValueError("Duplicate scope grants.")
        return self


@dataclass(frozen=True)
class CredentialAttempt:
    username: str = field(repr=False)
    password: str = field(repr=False)


def _parse_basic(values):
    # Explicit tuple of Authorization field values rejects duplicates, including
    # identical duplicates. Never interpret a forwarded identity as credentials.
    if type(values) is not tuple or len(values) != 1 or type(values[0]) is not str:
        raise ValueError("One authorization value is required.")
    header = values[0]
    if not 1 <= len(header) <= 4096 or any(ord(char) > 127 for char in header):
        raise ValueError("Invalid authorization framing.")
    scheme, separator, token = header.partition(" ")
    if not separator or scheme.lower() != "basic" or not token or any(char.isspace() for char in token):
        raise ValueError("Invalid authorization framing.")
    decoded = base64.b64decode(token, validate=True).decode("utf-8", errors="strict")
    # Require canonical padded base64; no alternate encodings or repairs.
    if base64.b64encode(decoded.encode("utf-8")).decode("ascii") != token:
        raise ValueError("Noncanonical credentials.")
    username, separator, password = decoded.partition(":")
    if (not separator or not username or username != username.strip() or not password
            or len(username) > 200 or len(password) > 1024
            or any(ord(char) < 32 or ord(char) == 127 for char in decoded)):
        raise ValueError("Invalid credential fields.")
    return CredentialAttempt(username, password)


@dataclass(frozen=True)
class PrincipalHandle:
    context_json: str = field(repr=False)
    context_sha256: str


@dataclass(frozen=True)
class IdentityCheck:
    verified_fixture: bool
    reason: str | None
    principal: PrincipalHandle | None = None
    execution_source: str = field(default="unit_test", init=False)
    authenticated_scope_verified: bool = field(default=False, init=False)
    semantic_grounding_verified: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)
    production_enabled: bool = field(default=False, init=False)
    proposition_to_inference: str = field(default="closed", init=False)


class OfflinePrincipalResolver:
    """One attempt per request, no retry/fallback; positive results stay local.

    Verifiers/readers must be explicitly scripted injected capabilities. Boolean
    success is a fixture judgment, never production authentication. Rechecks
    observe revocation/rotation but do not provide a publication barrier.
    """
    def __init__(self, *, principal_reader, verifier, timeout_seconds=3.0, clock=time.monotonic):
        if isinstance(timeout_seconds, bool) or not isinstance(timeout_seconds, (int, float)) or not math.isfinite(timeout_seconds) or not 0 < timeout_seconds <= 120:
            raise ValueError("A bounded finite deadline is required.")
        self.reader, self.verifier = principal_reader, verifier
        self.timeout, self.clock = timeout_seconds, clock
        self.started = self._now()
        self.terminal = None
        self.handle = None
        self.attempted = False

    def _now(self):
        now = self.clock()
        if isinstance(now, bool) or not isinstance(now, (int, float)) or not math.isfinite(now) or now < 0 or (hasattr(self, "last") and now < self.last):
            raise ValueError("Invalid monotonic clock.")
        self.last = now
        return now

    def _expired(self):
        return self._now() - self.started >= self.timeout

    def _deny(self, reason):
        self.terminal = self.terminal or reason
        return IdentityCheck(False, self.terminal)

    def _read(self, username):
        if (getattr(self.reader, "execution_source", None) != "unit_test"
                or not callable(getattr(self.reader, "read", None))
                or inspect.iscoroutinefunction(self.reader.read)):
            raise ValueError("Scripted principal reader required.")
        record = self.reader.read(username=username)
        if type(record) is not PrincipalRecord:
            raise ValueError("Missing or malformed principal.")
        record = PrincipalRecord.model_validate_json(record.model_dump_json(), strict=True)
        if record.username != username or not record.enabled:
            raise ValueError("Principal unavailable.")
        return record

    def _verifier_valid(self, record):
        formats = getattr(self.verifier, "supported_formats", None)
        return (getattr(self.verifier, "execution_source", None) == "unit_test"
            and callable(getattr(self.verifier, "verify", None))
            and not inspect.iscoroutinefunction(self.verifier.verify)
            and type(formats) is tuple and record.credential_format in formats)

    def resolve(self, *, authorization_values, requested_scope, request_id):
        if self.terminal:
            return self._deny(self.terminal)
        if self.attempted:
            return self._deny("identity_attempt_already_used")
        self.attempted = True
        try:
            capabilities = (self.reader, self.verifier)
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            if type(requested_scope) is not EvidenceScope:
                return self._deny("identity_scope_invalid")
            scope = EvidenceScope.model_validate_json(requested_scope.model_dump_json(), strict=True)
            if type(request_id) is not str or not request_id.strip() or len(request_id) > 200:
                return self._deny("identity_request_invalid")
            try:
                attempt = _parse_basic(authorization_values)
            except Exception:
                return self._deny("credentials_malformed")
            try:
                record = self._read(attempt.username)
            except Exception:
                return self._deny("principal_unavailable_or_denied")
            if scope not in record.grants:
                return self._deny("principal_scope_denied")
            if not self._verifier_valid(record):
                return self._deny("credential_verifier_unavailable_or_unsupported")
            formats = self.verifier.supported_formats
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            try:
                verified = self.verifier.verify(attempt=attempt, principal=record.model_copy(deep=True))
            except Exception:
                return self._deny("credential_verifier_failure")
            if verified is not True:
                return self._deny("credentials_rejected")
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            if (any(a is not b for a, b in zip(capabilities, (self.reader, self.verifier)))
                    or not self._verifier_valid(record) or self.verifier.supported_formats != formats
                    or self._read(attempt.username) != record):
                return self._deny("principal_or_credential_policy_changed")
            if (any(a is not b for a, b in zip(capabilities, (self.reader, self.verifier)))
                    or not self._verifier_valid(record) or self.verifier.supported_formats != formats):
                return self._deny("principal_or_credential_policy_changed")
            context = _json({"schema_version": "21-I-offline-principal-v1", "request_id": request_id,
                "requested_scope": scope.model_dump(mode="json"), "principal": record.model_dump(mode="json")})
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            self.handle = PrincipalHandle(context, hashlib.sha256(context.encode()).hexdigest())
            self._binding = (context, self.handle.context_sha256)
            self._capabilities = capabilities
            self._formats = formats
            return IdentityCheck(True, None, self.handle)
        except Exception:
            return self._deny("identity_resolution_failure")

    def recheck(self, principal):
        if self.terminal:
            return self._deny(self.terminal)
        if principal is not self.handle or self.handle is None:
            return self._deny("principal_handle_unbound")
        try:
            if (principal.context_json, principal.context_sha256) != self._binding or any(a is not b for a, b in zip(self._capabilities, (self.reader, self.verifier))):
                return self._deny("principal_handle_unbound")
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            data = json.loads(principal.context_json)
            record = PrincipalRecord.model_validate_json(_json(data["principal"]), strict=True)
            if (self._read(record.username) != record or not self._verifier_valid(record)
                    or self.verifier.supported_formats != self._formats):
                return self._deny("principal_or_credential_policy_changed")
            if any(a is not b for a, b in zip(self._capabilities, (self.reader, self.verifier))):
                return self._deny("principal_handle_unbound")
            if self._expired():
                return self._deny("identity_deadline_exceeded")
            return IdentityCheck(True, None, principal)
        except Exception:
            return self._deny("identity_recheck_unavailable_or_denied")
