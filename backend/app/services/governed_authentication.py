"""Explicit application credential verification for opt-in governed services.

No environment fallback, proxy identity trust or automatic principal provisioning.
The supplied catalog must transactionally version credentials and permissions.
"""
import hashlib
import hmac
import secrets
from dataclasses import dataclass, field

from evaluation.governed_answers.identity_resolution import _parse_basic
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope


def password_record(password):
    """Create a salted record for an explicitly provisioned principal only."""
    salt = secrets.token_bytes(16)
    return salt, _hash(password, salt)


def _hash(password, salt):
    if type(password) is not str or not 1 <= len(password) <= 1024:
        raise ValueError('invalid_credential')
    return hashlib.scrypt(password.encode('utf-8'), salt=salt, n=16384, r=8, p=1, dklen=32)


def _scope(value):
    if type(value) is EvidenceScope:
        return EvidenceScope.model_validate_json(value.model_dump_json(), strict=True)
    if type(value) is dict:
        return EvidenceScope.model_validate(value, strict=True)
    if type(value) in (list, tuple) and len(value) == 4:
        return EvidenceScope.model_validate(dict(zip(('organization_id','collection','module','topic'), value)), strict=True)
    raise ValueError('invalid_scope')


def _record(value, username):
    if value is None:
        return None
    if type(value) is not dict:
        raise ValueError('invalid_principal_record')
    for key in ('principal_id', 'username'):
        if type(value[key]) is not str or not value[key].strip() or len(value[key]) > 200:
            raise ValueError('invalid_principal_record')
    if value['username'] != username or type(value['disabled']) is not bool:
        raise ValueError('invalid_principal_record')
    for key in ('credential_epoch','permission_epoch'):
        if type(value[key]) is not int or not 1 <= value[key] < 2**63:
            raise ValueError('invalid_principal_record')
    salt, hashed = value['salt'], value['password_hash']
    if isinstance(salt, memoryview): salt = bytes(salt)
    if isinstance(hashed, memoryview): hashed = bytes(hashed)
    if type(salt) is not bytes or len(salt) != 16 or type(hashed) is not bytes or len(hashed) != 32:
        raise ValueError('invalid_principal_record')
    if type(value['scopes']) not in (list, tuple) or len(value['scopes']) > 100:
        raise ValueError('invalid_principal_record')
    scopes = tuple(_scope(item) for item in value['scopes'])
    if len(set(s.model_dump_json() for s in scopes)) != len(scopes):
        raise ValueError('duplicate_grants')
    return (value['principal_id'], value['username'], value['credential_epoch'],
            value['permission_epoch'], value['disabled'], salt, hashed,
            tuple(sorted(s.model_dump_json() for s in scopes)))


@dataclass(frozen=True)
class AuthenticatedGovernedPrincipal:
    principal_id: str
    credential_epoch: int
    permission_epoch: int
    scope: EvidenceScope
    username: str = field(repr=False)
    production_enabled: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)


class GovernedAuthenticationSession:
    """One attempt; handle ownership plus exact current-record rechecks.

    read_principal is a synchronous bounded catalog read capability, never a
    caller-provided identity header. Publication additionally requires SQL locks
    and current version checks; this session alone is not a publication barrier.
    """
    def __init__(self, catalog):
        self._catalog = catalog
        self._attempted = False
        self._denied = False
        self._issued = None
        self._binding = None

    def bound_to(self, catalog):
        """Object identity binds this issuance capability to its configured catalog."""
        return self._catalog is catalog

    def authenticate(self, *, authorization_values, scope):
        if self._attempted:
            self._denied = True
            return None
        self._attempted = True
        try:
            if type(scope) is not EvidenceScope:
                raise ValueError('exact_scope_required')
            scope = _scope(scope)
            attempt = _parse_basic(authorization_values)
            initial = _record(self._catalog.read_principal(attempt.username), attempt.username)
            salt = initial[5] if initial else bytes(16)
            expected = initial[6] if initial else bytes(32)
            valid = hmac.compare_digest(_hash(attempt.password, salt), expected)
            final = _record(self._catalog.read_principal(attempt.username), attempt.username)
            if (not initial or not valid or initial != final or initial[4]
                    or scope.model_dump_json() not in initial[7]):
                raise ValueError('credentials_or_scope_denied')
            self._binding = initial
            self._issued = AuthenticatedGovernedPrincipal(initial[0], initial[2], initial[3], scope, initial[1])
            return self._issued
        except Exception:
            self._denied = True
            return None

    def recheck(self, principal):
        if self._denied or self._issued is None or principal is not self._issued:
            self._denied = True
            return False
        try:
            current = _record(self._catalog.read_principal(principal.username), principal.username)
            valid = current == self._binding
        except Exception:
            valid = False
        if not valid:
            self._denied = True
        return valid
