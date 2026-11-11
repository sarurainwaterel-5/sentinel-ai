"""Isolated durable catalog harness. Never opens the application database.

SQL transactions prove relational atomicity only. Supplied chunks are stored
bytes, not extraction or vector-index verification, and cannot authorize release.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import sqlite3
import uuid

from .scope_catalog_contracts import EvidenceScope

SCHEMA_VERSION = "sentinel-isolated-catalog-v1"
SCHEMA = """
CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);
CREATE TABLE scopes(scope TEXT PRIMARY KEY,revision INTEGER NOT NULL CHECK(revision>=0));
CREATE TABLE identities(document_id TEXT PRIMARY KEY,scope TEXT NOT NULL REFERENCES scopes(scope),
 lifecycle INTEGER NOT NULL CHECK(lifecycle>=1),content INTEGER NOT NULL CHECK(content>=1),
 state TEXT NOT NULL CHECK(state IN ('pending','archived','tombstoned')));
CREATE TABLE versions(document_id TEXT NOT NULL REFERENCES identities(document_id),content INTEGER NOT NULL,
 source BLOB NOT NULL,source_hash TEXT NOT NULL,manifest TEXT NOT NULL,manifest_hash TEXT NOT NULL,
 PRIMARY KEY(document_id,content));
CREATE TABLE chunks(document_id TEXT NOT NULL,content INTEGER NOT NULL,locator INTEGER NOT NULL CHECK(locator>=0),
 bytes BLOB NOT NULL,PRIMARY KEY(document_id,content,locator),
 FOREIGN KEY(document_id,content) REFERENCES versions(document_id,content));
CREATE TABLE outbox(operation_id TEXT PRIMARY KEY,payload_hash TEXT NOT NULL,document_id TEXT NOT NULL,
 scope TEXT NOT NULL,lifecycle INTEGER NOT NULL,content INTEGER NOT NULL,state TEXT NOT NULL,
 manifest_hash TEXT NOT NULL,status TEXT NOT NULL CHECK(status IN ('pending','reconciled','stale')));
"""


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _name(value):
    if type(value) is not str or not value.strip() or len(value) > 200 or value in {"*", "all"}:
        raise ValueError("explicit bounded identifier required")
    return value


def _scope(value):
    if type(value) is not EvidenceScope:
        raise ValueError("exact scope required")
    return EvidenceScope.model_validate_json(value.model_dump_json(), strict=True).model_dump_json()


@dataclass(frozen=True)
class StorageSnapshot:
    scope_json: str
    revision: int
    documents_json: str
    sha256: str
    index_verified: bool = False
    release_authorized: bool = False
    production_enabled: bool = False


def _schema_inventory(db):
    return tuple((row[0], row[1], row[2], " ".join((row[3] or "").split()))
                 for row in db.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"))


def _expected_schema():
    db = sqlite3.connect(":memory:")
    try:
        db.executescript(SCHEMA)
        return _schema_inventory(db)
    finally:
        db.close()


class IsolatedCatalog:
    """Explicit disposable file, foreign keys, FULL sync, serialized CAS writes.

    Each handle owns one SQLite connection; use separate handles for concurrency.
    No mutable connection is exposed. This is not a runtime authority reader.
    """
    def __init__(self, path, connection):
        self.path, self._db = Path(path), connection
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")

    @classmethod
    def create(cls, path):
        path = Path(path)
        # Exclusive creation prevents accidental adoption/overwrite of user data.
        with path.open("xb"):
            pass
        db = sqlite3.connect(str(path), isolation_level=None, timeout=2)
        instance = cls(path, db)
        try:
            db.executescript("BEGIN IMMEDIATE;" + SCHEMA)
            db.executemany("INSERT INTO metadata VALUES(?,?)", (
                ("schema_version", SCHEMA_VERSION), ("schema_sha256", _sha(SCHEMA.encode())),
                ("database_id", str(uuid.uuid4())), ("purpose", "isolated-test-only")))
            db.execute("COMMIT")
        except BaseException:
            db.close()
            raise
        return instance

    @classmethod
    def open(cls, path):
        path = Path(path)
        # mode=rw cannot create a missing file. Metadata excludes application DBs.
        db = sqlite3.connect(path.resolve().as_uri() + "?mode=rw", uri=True, isolation_level=None, timeout=2)
        try:
            metadata = dict(db.execute("SELECT key,value FROM metadata"))
            if (metadata.get("schema_version") != SCHEMA_VERSION or
                    metadata.get("schema_sha256") != _sha(SCHEMA.encode()) or
                    metadata.get("purpose") != "isolated-test-only"):
                raise ValueError("incompatible isolated database")
            if _schema_inventory(db) != _expected_schema():
                raise ValueError("actual isolated schema mismatch")
            if db.execute("PRAGMA foreign_key_check").fetchone() is not None:
                raise ValueError("database foreign key failure")
            if db.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
                raise ValueError("database integrity failure")
            instance = cls(path, db)
            instance._budget()
            return instance
        except BaseException:
            db.close()
            raise

    def _budget(self):
        if self._db.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise ValueError("database foreign key failure")
        for table, limit in (("identities", 1000), ("versions", 10000), ("chunks", 320000), ("outbox", 10000), ("scopes", 1000)):
            if self._db.execute("SELECT count(*) FROM " + table).fetchone()[0] > limit:
                raise ValueError("isolated storage row budget exceeded")
        size = self._db.execute("SELECT coalesce(sum(length(source)),0) FROM versions").fetchone()[0]
        size += self._db.execute("SELECT coalesce(sum(length(bytes)),0) FROM chunks").fetchone()[0]
        if size > 256*1024*1024:
            raise ValueError("isolated storage byte budget exceeded")

    def close(self):
        self._db.close()

    @contextmanager
    def _transaction(self, write=False):
        self._db.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        try:
            self._budget()
            yield
            if write:
                self._budget()
            self._db.execute("COMMIT")
        except BaseException:
            self._db.execute("ROLLBACK")
            raise

    def _operation(self, operation_id, payload):
        _name(operation_id)
        digest = _sha(_json(payload).encode())
        prior = self._db.execute("SELECT * FROM outbox WHERE operation_id=?", (operation_id,)).fetchone()
        if prior is not None and prior["payload_hash"] != digest:
            raise ValueError("operation identity reused")
        return digest, prior

    def _record(self, operation_id, digest, document_id, scope, lifecycle, content, state, manifest):
        self._db.execute("UPDATE scopes SET revision=revision+1 WHERE scope=?", (scope,))
        self._db.execute("INSERT INTO outbox VALUES(?,?,?,?,?,?,?,?, 'pending')",
                         (operation_id, digest, document_id, scope, lifecycle, content, state, manifest))

    def put(self, *, operation_id, document_id, scope, source, chunks, expected_lifecycle=None):
        """Create/replace explicit bytes and enqueue work in the same transaction.

        Repeating an identical operation is idempotent even after later writes.
        Different identities may have equal hashes. Scope moves are unsupported.
        """
        _name(document_id)
        scope = _scope(scope)
        if (type(source) is not bytes or not 1 <= len(source) <= 1024*1024 or
                type(chunks) is not tuple or not 1 <= len(chunks) <= 32 or
                any(type(c) is not bytes or not 1 <= len(c) <= 65536 for c in chunks) or
                sum(map(len, chunks)) > 1024*1024):
            raise ValueError("bounded explicit byte manifest required")
        for chunk in chunks:
            chunk.decode("utf-8", errors="strict")
        if expected_lifecycle is not None and (type(expected_lifecycle) is not int or expected_lifecycle < 1):
            raise ValueError("invalid expected lifecycle")
        manifest = _json([{ "locator": i, "sha256": _sha(c), "length": len(c)} for i,c in enumerate(chunks)])
        manifest_hash, source_hash = _sha(manifest.encode()), _sha(source)
        payload = ["put", document_id, scope, source_hash, manifest_hash, expected_lifecycle]
        with self._transaction(write=True):
            digest, prior = self._operation(operation_id, payload)
            if prior is not None:
                return prior["lifecycle"]
            old = self._db.execute("SELECT * FROM identities WHERE document_id=?", (document_id,)).fetchone()
            if old is None:
                if expected_lifecycle is not None:
                    raise ValueError("missing expected identity")
                lifecycle = content = 1
                self._db.execute("INSERT OR IGNORE INTO scopes VALUES(?,0)", (scope,))
                self._db.execute("INSERT INTO identities VALUES(?,?,1,1,'pending')", (document_id,scope))
            else:
                if old["state"] != "pending" or old["scope"] != scope or old["lifecycle"] != expected_lifecycle:
                    raise ValueError("stale, moved, or tombstoned identity")
                lifecycle, content = old["lifecycle"]+1, old["content"]+1
                self._db.execute("UPDATE identities SET lifecycle=?,content=?,state='pending' WHERE document_id=?",
                                 (lifecycle,content,document_id))
            self._db.execute("INSERT INTO versions VALUES(?,?,?,?,?,?)",
                             (document_id,content,source,source_hash,manifest,manifest_hash))
            self._db.executemany("INSERT INTO chunks VALUES(?,?,?,?)",
                                 [(document_id,content,i,c) for i,c in enumerate(chunks)])
            self._record(operation_id,digest,document_id,scope,lifecycle,content,"pending",manifest_hash)
            return lifecycle

    def transition(self, *, operation_id, document_id, expected_lifecycle, state):
        _name(document_id)
        if state not in {"archived", "tombstoned", "restoring"} or type(expected_lifecycle) is not int or expected_lifecycle < 1:
            raise ValueError("invalid lifecycle transition")
        with self._transaction(write=True):
            digest, prior = self._operation(operation_id,["transition",document_id,expected_lifecycle,state])
            if prior is not None:
                return prior["lifecycle"]
            old = self._db.execute("SELECT * FROM identities WHERE document_id=?", (document_id,)).fetchone()
            if old is None or old["lifecycle"] != expected_lifecycle or old["state"] == "tombstoned":
                raise ValueError("stale or tombstoned identity")
            if state == "archived" and old["state"] != "pending":
                raise ValueError("archive requires pending identity")
            if state == "restoring" and old["state"] != "archived":
                raise ValueError("restore requires archived identity")
            final_state = "pending" if state == "restoring" else state
            lifecycle = expected_lifecycle+1
            self._db.execute("UPDATE identities SET lifecycle=?,state=? WHERE document_id=?", (lifecycle,final_state,document_id))
            manifest = self._db.execute("SELECT manifest_hash FROM versions WHERE document_id=? AND content=?",(document_id,old["content"])).fetchone()[0]
            self._record(operation_id,digest,document_id,old["scope"],lifecycle,old["content"],final_state,manifest)
            return lifecycle

    def _bytes(self, document):
        _name(document["document_id"])
        parsed_scope = EvidenceScope.model_validate_json(document["scope"], strict=True)
        if _scope(parsed_scope) != document["scope"] or any(type(document[k]) is not int or document[k] < 1 for k in ("lifecycle", "content")) or document["state"] not in {"pending", "archived", "tombstoned"}:
            raise ValueError("invalid persisted identity")
        version = self._db.execute("SELECT * FROM versions WHERE document_id=? AND content=?",(document["document_id"],document["content"])).fetchone()
        if version is None or type(version["source"]) is not bytes or not 1 <= len(version["source"]) <= 1024*1024 or type(version["manifest"]) is not str or len(version["manifest"]) > 65536 or _sha(version["source"]) != version["source_hash"] or _sha(version["manifest"].encode()) != version["manifest_hash"]:
            raise ValueError("stored byte integrity failure")
        chunks = self._db.execute("SELECT locator,bytes FROM chunks WHERE document_id=? AND content=? ORDER BY locator",(document["document_id"],document["content"])).fetchall()
        if not 1 <= len(chunks) <= 32 or any(type(c["bytes"]) is not bytes or not 1 <= len(c["bytes"]) <= 65536 for c in chunks) or sum(len(c["bytes"]) for c in chunks) > 1024*1024:
            raise ValueError("invalid persisted chunk bytes")
        for chunk in chunks:
            chunk["bytes"].decode("utf-8", errors="strict")
        manifest = [{"locator": c["locator"], "sha256": _sha(c["bytes"]), "length": len(c["bytes"])} for c in chunks]
        if _json(manifest) != version["manifest"] or [c["locator"] for c in chunks] != list(range(len(chunks))) or not chunks:
            raise ValueError("stored manifest integrity failure")
        return version, tuple(c["bytes"] for c in chunks)

    def reconcile(self, operation_id):
        """Verify current relational bytes. Never certifies a real vector index."""
        _name(operation_id)
        with self._transaction(write=True):
            event = self._db.execute("SELECT * FROM outbox WHERE operation_id=?",(operation_id,)).fetchone()
            if event is None:
                raise ValueError("unknown operation")
            doc = self._db.execute("SELECT * FROM identities WHERE document_id=?",(event["document_id"],)).fetchone()
            current = doc is not None and all(doc[k] == event[k] for k in ("scope","lifecycle","content","state"))
            if current:
                version, _ = self._bytes(doc)
                current = version["manifest_hash"] == event["manifest_hash"]
            status = "reconciled" if current else "stale"
            self._db.execute("UPDATE outbox SET status=? WHERE operation_id=?",(status,operation_id))
            return {"operation_id":operation_id,"status":status,"index_verified":False,"release_authorized":False}

    def snapshot(self, scope):
        scope = _scope(scope)
        with self._transaction():
            revision = self._db.execute("SELECT revision FROM scopes WHERE scope=?",(scope,)).fetchone()
            rows = self._db.execute("SELECT * FROM identities WHERE scope=? ORDER BY document_id",(scope,)).fetchall()
            docs = []
            for row in rows:
                version, _ = self._bytes(row)
                docs.append({**dict(row), "file_sha256":version["source_hash"],"manifest_sha256":version["manifest_hash"],"index_verified":False})
            revision = 0 if revision is None else revision[0]
            if type(revision) is not int or revision < 0:
                raise ValueError("invalid persisted scope revision")
            serialized = _json(docs)
            return StorageSnapshot(scope,revision,serialized,_sha(_json([scope,revision,docs]).encode()))

    def evidence(self, *, scope, document_id):
        """Read pending stored chunks for integration inspection, not governed answers."""
        scope = _scope(scope)
        _name(document_id)
        with self._transaction():
            doc = self._db.execute("SELECT * FROM identities WHERE document_id=? AND scope=?",(document_id,scope)).fetchone()
            if doc is None or doc["state"] != "pending":
                raise ValueError("document unavailable")
            version, chunks = self._bytes(doc)
            return {"document_id":document_id,"scope":json.loads(scope),"lifecycle_epoch":doc["lifecycle"],
                    "content_epoch":doc["content"],"file_sha256":version["source_hash"],
                    "manifest_sha256":version["manifest_hash"],"chunks":tuple(c.decode("utf-8",errors="strict") for c in chunks),
                    "index_verified":False,"release_authorized":False,"production_enabled":False}

    def backup(self, destination):
        """Online SQLite backup to an exclusive new artifact, with target bindings."""
        destination = Path(destination)
        with destination.open("xb"):
            pass
        target = sqlite3.connect(str(destination), isolation_level=None)
        try:
            self._db.backup(target)
        finally:
            target.close()
        clone = self.open(destination)
        try:
            metadata = dict(clone._db.execute("SELECT key,value FROM metadata"))
        finally:
            clone.close()
        return {"database_id":metadata["database_id"],"schema_version":SCHEMA_VERSION,
                "schema_sha256":_sha(SCHEMA.encode()),"sqlite_version":sqlite3.sqlite_version,
                "backup_sha256":_sha(destination.read_bytes()),"application_migration_authorized":False}
