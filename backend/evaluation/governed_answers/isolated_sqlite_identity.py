"""Real hash/storage integration for disposable isolated acceptance databases only.

No HTTP registration, environment lookup, startup migration, or release authority.
A caller must supply a brand-new database path and synthetic credentials.
"""
import hashlib
import hmac
import secrets
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from .identity_resolution import _parse_basic
from .scope_catalog_contracts import EvidenceScope


@dataclass(frozen=True)
class IsolatedIdentity:
    principal_id: str
    credential_version: int
    permission_epoch: int
    grants: tuple[EvidenceScope, ...]
    username: str = field(repr=False)
    execution_source: str = field(default="isolated_sqlite", init=False)
    production_enabled: bool = field(default=False, init=False)
    release_authorized: bool = field(default=False, init=False)


class IsolatedAuthorityStore:
    """Explicitly created synthetic authority store; never opens an existing DB."""
    def __init__(self, path):
        path = Path(path)
        # Exclusive create prevents accidentally using an application's database.
        with path.open("xb"):
            pass
        self.path = path
        self.db = sqlite3.connect(path)
        self.db.executescript("""
        PRAGMA foreign_keys=ON;
        CREATE TABLE isolated_authority_marker (purpose TEXT NOT NULL);
        INSERT INTO isolated_authority_marker VALUES ('synthetic-acceptance-only');
        CREATE TABLE principals (
          username TEXT PRIMARY KEY, principal_id TEXT UNIQUE NOT NULL,
          enabled INTEGER NOT NULL CHECK(enabled IN (0,1)),
          salt BLOB NOT NULL, password_hash BLOB NOT NULL,
          credential_version INTEGER NOT NULL CHECK(credential_version>=0), permission_epoch INTEGER NOT NULL CHECK(permission_epoch>=0));
        CREATE TABLE grants (
          username TEXT NOT NULL REFERENCES principals(username),
          organization_id TEXT NOT NULL, collection TEXT NOT NULL,
          module TEXT NOT NULL, topic TEXT NOT NULL,
          PRIMARY KEY(username,organization_id,collection,module,topic));
        """)
        self.db.commit()

    @staticmethod
    def _hash(password, salt):
        if type(password) is not str or not 1 <= len(password) <= 1024:
            raise ValueError("Invalid synthetic credential.")
        return hashlib.scrypt(password.encode("utf-8"), salt=salt, n=16384, r=8, p=1, dklen=32)

    @staticmethod
    def _grants(grants):
        if type(grants) is not tuple or len(grants) > 100 or any(type(g) is not EvidenceScope for g in grants):
            raise ValueError("Explicit exact grants required.")
        validated = tuple(EvidenceScope.model_validate_json(g.model_dump_json(), strict=True) for g in grants)
        rows = tuple((g.organization_id, g.collection, g.module, g.topic) for g in validated)
        if len(rows) != len(set(rows)):
            raise ValueError("Duplicate grants.")
        return rows

    def provision(self, *, username, principal_id, password, grants):
        if any(type(v) is not str or not v.strip() or len(v) > 200 for v in (username, principal_id)):
            raise ValueError("Explicit principal required.")
        rows = self._grants(grants)
        salt = secrets.token_bytes(16)
        hashed = self._hash(password, salt)
        with self.db:
            self.db.execute("INSERT INTO principals VALUES (?,?,1,?,?,0,0)", (username, principal_id, salt, hashed))
            self.db.executemany("INSERT INTO grants VALUES (?,?,?,?,?)", ((username, *r) for r in rows))

    def rotate(self, *, username, password):
        salt = secrets.token_bytes(16)
        hashed = self._hash(password, salt)
        with self.db:
            cursor = self.db.execute("UPDATE principals SET salt=?,password_hash=?,credential_version=credential_version+1 WHERE username=?", (salt, hashed, username))
            if cursor.rowcount != 1:
                raise ValueError("Unknown principal.")

    def set_grants(self, *, username, grants):
        rows = self._grants(grants)
        with self.db:
            cursor = self.db.execute("UPDATE principals SET permission_epoch=permission_epoch+1 WHERE username=?", (username,))
            if cursor.rowcount != 1:
                raise ValueError("Unknown principal.")
            self.db.execute("DELETE FROM grants WHERE username=?", (username,))
            self.db.executemany("INSERT INTO grants VALUES (?,?,?,?,?)", ((username, *r) for r in rows))

    def disable(self, *, username):
        with self.db:
            self.db.execute("UPDATE principals SET enabled=0,permission_epoch=permission_epoch+1 WHERE username=?", (username,))

    def _read(self, username):
        # One read transaction binds the principal version to its complete grants.
        with self.db:
            self.db.execute("BEGIN")
            row = self.db.execute("SELECT principal_id,enabled,salt,password_hash,credential_version,permission_epoch FROM principals WHERE username=?", (username,)).fetchone()
            grants = self.db.execute("SELECT organization_id,collection,module,topic FROM grants WHERE username=? ORDER BY organization_id,collection,module,topic", (username,)).fetchall()
        if row is None or row[1] != 1:
            return None
        if (type(row[0]) is not str or not row[0].strip() or len(row[0]) > 200
                or type(row[2]) is not bytes or len(row[2]) != 16
                or type(row[3]) is not bytes or len(row[3]) != 32
                or type(row[4]) is not int or row[4] < 0
                or type(row[5]) is not int or row[5] < 0 or len(grants) > 100):
            raise ValueError("Malformed principal storage.")
        scopes = tuple(EvidenceScope(organization_id=g[0], collection=g[1], module=g[2], topic=g[3]) for g in grants)
        return row, IsolatedIdentity(row[0], row[4], row[5], scopes, username)

    def session(self):
        return IsolatedIdentitySession(self)

    def close(self):
        self.db.close()


class IsolatedIdentitySession:
    """One verification attempt; revocation/rotation observed by terminal rechecks.

    Rechecks are optimistic observations, not distributed publication locks.
    Identity capabilities are owned by this session, never accepted from callers.
    """
    def __init__(self, store):
        self.store = store
        self.attempted = False
        self.denied = False
        self.identity = None
        self.scope = None
        self._issued_identity = None
        self._issued_scope = None

    def authenticate(self, *, authorization_values, scope):
        if self.attempted:
            self.denied = True
            return None
        self.attempted = True
        try:
            if type(scope) is not EvidenceScope:
                raise ValueError("Invalid scope.")
            attempt = _parse_basic(authorization_values)
            initial = self.store._read(attempt.username)
            # Unknown users still perform one scrypt operation with a dummy salt.
            salt = initial[0][2] if initial else bytes(16)
            computed = self.store._hash(attempt.password, salt)
            expected = initial[0][3] if initial else bytes(32)
            valid = hmac.compare_digest(computed, expected)
            final = self.store._read(attempt.username)
            if not initial or not valid or final != initial or scope not in initial[1].grants:
                raise ValueError("Denied.")
            self.identity, self.scope = initial[1], scope
            self._issued_identity, self._issued_scope = self.identity, scope
            return self.identity
        except (ValueError, TypeError, sqlite3.Error):
            self.denied = True
            return None

    def recheck(self):
        if (self.denied or not self.attempted or self._issued_identity is None
                or self.identity is not self._issued_identity or self.scope is not self._issued_scope):
            self.denied = True
            return False
        try:
            current = self.store._read(self.identity.username)
            valid = current is not None and current[1] == self.identity and self.scope in current[1].grants
        except (ValueError, TypeError, sqlite3.Error):
            valid = False
        if not valid:
            self.denied = True
        return valid
