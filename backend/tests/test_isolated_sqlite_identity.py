"""Actual disposable SQLite authority + scrypt acceptance, synthetic secrets only."""
import base64
import sqlite3

import pytest

from evaluation.governed_answers.isolated_sqlite_identity import IsolatedAuthorityStore
from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope


def scope(module="sre", topic="incident"):
    return EvidenceScope(organization_id="synthetic-org", collection="synthetic", module=module, topic=topic)


def header(password="synthetic-password", username="synthetic-user"):
    return ("Basic " + base64.b64encode(f"{username}:{password}".encode()).decode(),)


@pytest.fixture
def store(tmp_path):
    authority = IsolatedAuthorityStore(tmp_path / "synthetic-authority.sqlite")
    authority.provision(username="synthetic-user", principal_id="synthetic-principal", password="synthetic-password", grants=(scope(), scope("ops", "runbook")))
    yield authority
    authority.close()


def test_crypto_exact_grants_and_closed_release(store):
    session = store.session()
    identity = session.authenticate(authorization_values=header(), scope=scope())
    assert identity.principal_id == "synthetic-principal"
    assert identity.execution_source == "isolated_sqlite"
    assert not identity.production_enabled and not identity.release_authorized
    assert session.recheck()
    assert "synthetic-password" not in repr(identity)
    assert "synthetic-user" not in repr(identity)
    assert store.session().authenticate(authorization_values=header(), scope=scope("sre", "runbook")) is None
    assert store.session().authenticate(authorization_values=header(), scope=scope("ops", "incident")) is None


@pytest.mark.parametrize("values", [header("incorrect"), header(username="unknown"), (), ("Basic ???",), header() * 2, ("Bearer synthetic",)])
def test_invalid_authentication_denies_terminally(store, values):
    session = store.session()
    assert session.authenticate(authorization_values=values, scope=scope()) is None
    assert not session.recheck()
    assert session.authenticate(authorization_values=header(), scope=scope()) is None


@pytest.mark.parametrize("mutation", ["rotate", "revoke", "disable"])
def test_persisted_changes_revoke_existing_session(store, mutation):
    session = store.session()
    assert session.authenticate(authorization_values=header(), scope=scope())
    if mutation == "rotate":
        store.rotate(username="synthetic-user", password="synthetic-new-password")
    elif mutation == "revoke":
        store.set_grants(username="synthetic-user", grants=())
    else:
        store.disable(username="synthetic-user")
    assert not session.recheck()
    store.set_grants(username="synthetic-user", grants=(scope(),))
    assert not session.recheck()
    if mutation == "rotate":
        assert store.session().authenticate(authorization_values=header(), scope=scope()) is None
        new = store.session().authenticate(authorization_values=header("synthetic-new-password"), scope=scope())
        assert new.credential_version == 1 and new.permission_epoch == 1


def test_rotation_during_hash_verification_denies(store, monkeypatch):
    original = store._hash
    def racing_hash(password, salt):
        result = original(password, salt)
        monkeypatch.setattr(store, "_hash", original)
        store.rotate(username="synthetic-user", password="synthetic-new-password")
        return result
    monkeypatch.setattr(store, "_hash", racing_hash)
    assert store.session().authenticate(authorization_values=header(), scope=scope()) is None


def test_persistent_hash_not_plaintext_and_unique_salts(store):
    store.provision(username="synthetic-second", principal_id="synthetic-second", password="synthetic-password", grants=())
    rows = store.db.execute("SELECT salt,password_hash FROM principals").fetchall()
    assert rows[0][0] != rows[1][0] and rows[0][1] != rows[1][1]
    assert all(len(salt) == 16 and len(hashed) == 32 for salt, hashed in rows)
    assert b"synthetic-password" not in store.path.read_bytes()


def test_existing_database_is_never_opened(tmp_path):
    path = tmp_path / "existing.sqlite"
    path.write_bytes(b"untouched")
    with pytest.raises(FileExistsError):
        IsolatedAuthorityStore(path)
    assert path.read_bytes() == b"untouched"


def test_external_connection_revocation_observed(store):
    session = store.session()
    assert session.authenticate(authorization_values=header(), scope=scope())
    with sqlite3.connect(store.path) as external:
        external.execute("UPDATE principals SET enabled=0,permission_epoch=permission_epoch+1")
    assert not session.recheck()


def test_database_failure_denies(store):
    session = store.session()
    assert session.authenticate(authorization_values=header(), scope=scope())
    store.db.close()
    assert not session.recheck()


def test_unissued_or_replaced_handle_denies(store):
    from dataclasses import replace
    issued = store.session()
    identity = issued.authenticate(authorization_values=header(), scope=scope())
    forged = store.session()
    forged.identity, forged.scope = identity, scope()
    assert not forged.recheck()
    issued.identity = replace(identity)
    assert not issued.recheck()


def test_forged_scope_instance_rejected(store):
    invalid = scope().model_copy(update={"module": "*"})
    with pytest.raises(ValueError):
        store.set_grants(username="synthetic-user", grants=(invalid,))


@pytest.mark.parametrize("column,value", [("salt", b"bad"), ("password_hash", b"bad")])
def test_corrupt_stored_crypto_denies(store, column, value):
    store.db.execute(f"UPDATE principals SET {column}=?", (value,))
    store.db.commit()
    assert store.session().authenticate(authorization_values=header(), scope=scope()) is None
