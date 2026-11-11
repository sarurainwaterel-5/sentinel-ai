"""Real SQLite transactions in pytest temporary files; no application DB."""
import hashlib
import json
import sqlite3

import pytest

from evaluation.governed_answers.scope_catalog_contracts import EvidenceScope
from evaluation.governed_answers.sqlite_catalog import IsolatedCatalog


SCOPE = EvidenceScope(organization_id="org",collection="manuals",module="ir",topic="sre")
FOREIGN = SCOPE.model_copy(update={"topic":"foreign"})


@pytest.fixture
def store(tmp_path):
    catalog = IsolatedCatalog.create(tmp_path / "isolated.db")
    yield catalog
    catalog.close()


def put(store, **overrides):
    args = dict(operation_id="create",document_id="document",scope=SCOPE,source=b"source",chunks=(b"one",b"two"))
    args.update(overrides)
    return store.put(**args)


def test_persists_bytes_scope_revision_manifest_and_outbox_after_reopen(store):
    assert put(store) == 1
    before = store.snapshot(SCOPE)
    assert before.revision == 1
    second = IsolatedCatalog.open(store.path)
    try:
        assert second.snapshot(SCOPE) == before
        evidence = second.evidence(scope=SCOPE,document_id="document")
        assert evidence["chunks"] == ("one","two")
        assert evidence["file_sha256"] == hashlib.sha256(b"source").hexdigest()
        assert evidence["index_verified"] is evidence["release_authorized"] is evidence["production_enabled"] is False
        assert second.reconcile("create")["status"] == "reconciled"
        assert json.loads(second.snapshot(SCOPE).documents_json)[0]["state"] == "pending"
    finally:
        second.close()


def test_duplicate_bytes_keep_distinct_identities_and_scopes(store):
    put(store)
    put(store,operation_id="other",document_id="other")
    put(store,operation_id="foreign",document_id="foreign",scope=FOREIGN)
    assert len(json.loads(store.snapshot(SCOPE).documents_json)) == 2
    assert len(json.loads(store.snapshot(FOREIGN).documents_json)) == 1
    with pytest.raises(ValueError):
        store.evidence(scope=FOREIGN,document_id="document")


def test_idempotence_has_exact_payload_identity(store):
    assert put(store) == put(store) == 1
    assert store.snapshot(SCOPE).revision == 1
    with pytest.raises(ValueError,match="operation identity"):
        put(store,chunks=(b"changed",))
    assert store.snapshot(SCOPE).revision == 1


def test_separate_connection_cas_and_stale_completion(store):
    put(store)
    second = IsolatedCatalog.open(store.path)
    try:
        assert put(second,operation_id="replace",expected_lifecycle=1,source=b"new") == 2
        with pytest.raises(ValueError):
            put(store,operation_id="late",expected_lifecycle=1)
        assert store.reconcile("create")["status"] == "stale"
        assert store.reconcile("replace")["status"] == "reconciled"
        # An old identical retry does not overwrite the replacement.
        assert put(store) == 1
        assert store.snapshot(SCOPE).revision == 2
    finally:
        second.close()


def test_outbox_failure_rolls_back_catalog_manifest_scope_and_bytes(store):
    # Fail at the LAST write so all earlier changes must roll back.
    connection = sqlite3.connect(store.path)
    connection.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT, 'injected'); END")
    connection.close()
    with pytest.raises(sqlite3.IntegrityError):
        put(store)
    assert store.snapshot(SCOPE).revision == 0
    assert json.loads(store.snapshot(SCOPE).documents_json) == []
    connection = sqlite3.connect(store.path)
    assert connection.execute("SELECT count(*) FROM versions").fetchone()[0] == 0
    assert connection.execute("SELECT count(*) FROM chunks").fetchone()[0] == 0
    connection.execute("DROP TRIGGER fail_outbox")
    connection.close()
    assert put(store) == 1


def test_archive_restore_and_retained_tombstone_deny_aba(store):
    put(store)
    assert store.transition(operation_id="archive",document_id="document",expected_lifecycle=1,state="archived") == 2
    with pytest.raises(ValueError):
        store.evidence(scope=SCOPE,document_id="document")
    assert store.transition(operation_id="restore",document_id="document",expected_lifecycle=2,state="restoring") == 3
    assert store.reconcile("create")["status"] == "stale"
    assert store.evidence(scope=SCOPE,document_id="document")["content_epoch"] == 1
    assert store.transition(operation_id="delete",document_id="document",expected_lifecycle=3,state="tombstoned") == 4
    with pytest.raises(ValueError):
        put(store,operation_id="resurrect",expected_lifecycle=4)
    with pytest.raises(ValueError):
        store.transition(operation_id="restore-deleted",document_id="document",expected_lifecycle=4,state="restoring")
    assert store.snapshot(SCOPE).revision == 4
    assert json.loads(store.snapshot(SCOPE).documents_json)[0]["state"] == "tombstoned"


def test_scope_move_denied_and_manifest_order_preserved(store):
    put(store)
    with pytest.raises(ValueError):
        put(store,operation_id="move",scope=FOREIGN,expected_lifecycle=1)
    first = store.evidence(scope=SCOPE,document_id="document")
    put(store,operation_id="reverse",expected_lifecycle=1,chunks=(b"two",b"one"))
    second = store.evidence(scope=SCOPE,document_id="document")
    assert first["manifest_sha256"] != second["manifest_sha256"]
    assert second["chunks"] == ("two","one")


@pytest.mark.parametrize("changes",[
    {"source":b""},{"source":b"x"*(1024*1024+1)}, {"source":"string"},
    {"chunks":[]},{"chunks":()},{"chunks":(b"",)}, {"chunks":(b"\xff",)},
    {"chunks":(b"x"*65537,)},{"expected_lifecycle":True}, {"document_id":"*"},
    {"operation_id":""}, {"scope":{"organization_id":"org"}},
])
def test_invalid_write_has_no_side_effect(store,changes):
    with pytest.raises((ValueError,UnicodeError)):
        put(store,**changes)
    assert store.snapshot(SCOPE).revision == 0


def test_restore_requires_archived_and_unknown_operations_deny(store):
    put(store)
    with pytest.raises(ValueError):
        store.transition(operation_id="restore",document_id="document",expected_lifecycle=1,state="restoring")
    with pytest.raises(ValueError):
        store.reconcile("unknown")
    assert store.snapshot(SCOPE).revision == 1


@pytest.mark.parametrize("table,statement",[
    ("source","UPDATE versions SET source=X'00'"),
    ("manifest","UPDATE versions SET manifest='[]'"),
    ("chunks","DELETE FROM chunks WHERE locator=1"),
    ("chunks","UPDATE chunks SET bytes=X'00' WHERE locator=0"),
])
def test_stored_byte_corruption_denies_reads_and_reconciliation(store,table,statement):
    put(store)
    connection = sqlite3.connect(store.path)
    connection.execute(statement)
    connection.commit()
    connection.close()
    with pytest.raises(ValueError):
        store.evidence(scope=SCOPE,document_id="document")
    with pytest.raises(ValueError):
        store.snapshot(SCOPE)
    with pytest.raises(ValueError):
        store.reconcile("create")


def test_backup_restore_rehearsal_binds_exact_schema_database_and_artifact(store,tmp_path):
    put(store)
    store.transition(operation_id="archive",document_id="document",expected_lifecycle=1,state="archived")
    artifact = tmp_path / "backup.db"
    receipt = store.backup(artifact)
    assert receipt["backup_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    assert receipt["application_migration_authorized"] is False
    restored = IsolatedCatalog.open(artifact)
    try:
        assert restored.snapshot(SCOPE) == store.snapshot(SCOPE)
        assert restored.reconcile("create")["status"] == "stale"
        assert restored.reconcile("archive")["status"] == "reconciled"
        assert restored.transition(operation_id="restore",document_id="document",expected_lifecycle=2,state="restoring") == 3
        assert store.snapshot(SCOPE).revision == 2
    finally:
        restored.close()
    with pytest.raises(FileExistsError):
        store.backup(artifact)


def test_create_open_refuse_adoption_and_overwrite(tmp_path):
    path = tmp_path / "missing.db"
    with pytest.raises(sqlite3.OperationalError):
        IsolatedCatalog.open(path)
    assert not path.exists()
    path.write_bytes(b"private application bytes")
    with pytest.raises(FileExistsError):
        IsolatedCatalog.create(path)
    assert path.read_bytes() == b"private application bytes"
    with pytest.raises(sqlite3.DatabaseError):
        IsolatedCatalog.open(path)


def test_simultaneous_writers_only_one_expected_generation_wins(store):
    from concurrent.futures import ThreadPoolExecutor
    import threading
    put(store)
    barrier = threading.Barrier(2)

    def writer(operation):
        handle = IsolatedCatalog.open(store.path)
        try:
            barrier.wait(timeout=5)
            try:
                return handle.transition(operation_id=operation,document_id="document",expected_lifecycle=1,state="archived")
            except ValueError:
                return "stale"
        finally:
            handle.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        futures = [pool.submit(writer, operation) for operation in ("worker-a", "worker-b")]
        results = [future.result(timeout=10) for future in futures]
    assert sorted(results,key=str) == [2,"stale"]
    assert store.snapshot(SCOPE).revision == 2
    connection = sqlite3.connect(store.path)
    assert connection.execute("SELECT count(*) FROM outbox").fetchone()[0] == 2
    connection.close()


def test_failed_replace_keeps_original_catalog_and_outbox(store):
    put(store)
    before = store.snapshot(SCOPE)
    connection = sqlite3.connect(store.path)
    connection.execute("CREATE TRIGGER fail_outbox BEFORE INSERT ON outbox BEGIN SELECT RAISE(ABORT, 'injected'); END")
    connection.close()
    with pytest.raises(sqlite3.IntegrityError):
        put(store,operation_id="failed",expected_lifecycle=1,source=b"replacement")
    assert store.snapshot(SCOPE) == before
    connection = sqlite3.connect(store.path)
    connection.execute("DROP TRIGGER fail_outbox")
    connection.close()
    reopened = IsolatedCatalog.open(store.path)
    try:
        assert reopened.snapshot(SCOPE) == before
        assert reopened.evidence(scope=SCOPE,document_id="document")["content_epoch"] == 1
        with pytest.raises(ValueError):
            reopened.reconcile("failed")
    finally:
        reopened.close()


def test_archived_replace_and_duplicate_archive_require_explicit_restore(store):
    put(store)
    store.transition(operation_id="archive",document_id="document",expected_lifecycle=1,state="archived")
    with pytest.raises(ValueError):
        put(store,operation_id="implicit-restore",expected_lifecycle=2)
    with pytest.raises(ValueError):
        store.transition(operation_id="archive-again",document_id="document",expected_lifecycle=2,state="archived")
    assert store.snapshot(SCOPE).revision == 2


def test_reopen_validates_actual_schema_not_metadata_label(store):
    connection = sqlite3.connect(store.path)
    connection.execute("ALTER TABLE identities ADD COLUMN unexpected TEXT")
    connection.close()
    with pytest.raises(ValueError,match="schema mismatch"):
        IsolatedCatalog.open(store.path)


@pytest.mark.parametrize("statement",[
    "UPDATE versions SET source='text'",
    "UPDATE identities SET scope='{}'",
    "UPDATE identities SET lifecycle=0",
    "UPDATE identities SET content=0",
])
def test_persisted_invalid_types_scope_and_epochs_fail_closed(store,statement):
    put(store)
    connection = sqlite3.connect(store.path)
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute(statement)
    connection.commit()
    connection.close()
    with pytest.raises((ValueError,TypeError)):
        store.snapshot(SCOPE)


@pytest.mark.parametrize("revision",[0.5,-1,"bad"])
def test_persisted_scope_revision_requires_nonnegative_exact_integer(store,revision):
    put(store)
    connection = sqlite3.connect(store.path)
    connection.execute("PRAGMA ignore_check_constraints=ON")
    connection.execute("UPDATE scopes SET revision=?",(revision,))
    connection.commit()
    connection.close()
    with pytest.raises(ValueError,match="scope revision"):
        store.snapshot(SCOPE)
