"""Actual PostgreSQL 16 disposable-schema rehearsal, never runtime activation.

Explicit DSN must identify sentinel_sprint21_rehearsal. No application DSN is
read. Source bytes in the backup are synthetic; reports exclude bytes and DSNs.
"""
import hashlib
import json
import os
from pathlib import Path
import uuid

import psycopg2
from psycopg2 import sql

DATABASE = "sentinel_sprint21_rehearsal"
DDL_PATH = Path(__file__).resolve().parents[3] / "docs/governance/isolated-postgres-catalog.sql"
TABLES = ("principals", "scopes", "grants", "identities", "versions", "chunks", "outbox")


def _sha(value):
    return hashlib.sha256(value).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _value(value):
    return {"bytea_hex": bytes(value).hex()} if isinstance(value, (bytes, memoryview)) else value


def _restore_value(value):
    return psycopg2.Binary(bytes.fromhex(value["bytea_hex"])) if isinstance(value, dict) else value


def _search_path(cursor, schema):
    cursor.execute(sql.SQL("SET LOCAL search_path TO {},pg_catalog").format(sql.Identifier(schema)))


def _inventory(connection, schema):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY")
            _search_path(cursor, schema)
            tables = {}
            for table in TABLES:
                # Chunk primary keys include locator; content alone leaves ties
                # whose physical order can change after restore or maintenance.
                ordering = sql.SQL("1,2,3" if table == "chunks" else "1,2")
                cursor.execute(sql.SQL("SELECT * FROM {} ORDER BY {}").format(sql.Identifier(table), ordering))
                columns = [column.name for column in cursor.description]
                tables[table] = {"columns": columns, "rows": [[_value(value) for value in row] for row in cursor.fetchall()]}
            return tables


def _schema(connection, schema, ddl):
    with connection:
        with connection.cursor() as cursor:
            cursor.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
            _search_path(cursor, schema)
            cursor.execute(ddl)


def _seed(connection, schema):
    source, chunks = b"Isolated PostgreSQL source: check queue depth before restart.", (b"Check queue depth before restart.", b"Escalate sustained backlog.")
    manifest = [{"locator":i,"sha256":_sha(chunk),"length":len(chunk)} for i,chunk in enumerate(chunks)]
    manifest_hash = _sha(_json(manifest).encode())
    with connection:
        with connection.cursor() as cursor:
            _search_path(cursor, schema)
            cursor.execute("INSERT INTO principals VALUES('principal',1,false)")
            cursor.execute("INSERT INTO scopes VALUES('scope','organization','manuals','ir','sre',0)")
            cursor.execute("INSERT INTO grants VALUES('principal','scope')")
            cursor.execute("INSERT INTO identities VALUES('document','scope',1,1,'pending')")
            cursor.execute("INSERT INTO versions VALUES('document',1,%s,%s,%s)", (psycopg2.Binary(source),_sha(source),manifest_hash))
            for index,chunk in enumerate(chunks):
                cursor.execute("INSERT INTO chunks VALUES('document',1,%s,%s,%s)", (index,psycopg2.Binary(chunk),_sha(chunk)))
            cursor.execute("UPDATE scopes SET revision=revision+1 WHERE scope_id='scope'")
            cursor.execute("INSERT INTO outbox VALUES('create','document','scope',1,1,'pending',%s,'pending')",(manifest_hash,))
    return manifest_hash


def _transition(connection, schema, *, operation, expected, state, manifest_hash):
    with connection:
        with connection.cursor() as cursor:
            _search_path(cursor, schema)
            cursor.execute("UPDATE identities SET lifecycle=lifecycle+1,state=%s WHERE document_id='document' AND lifecycle=%s AND state <> 'tombstoned' RETURNING lifecycle",(state,expected))
            updated = cursor.fetchone()
            if updated is None:
                raise ValueError("expected-generation transition denied")
            cursor.execute("UPDATE scopes SET revision=revision+1 WHERE scope_id='scope'")
            cursor.execute("INSERT INTO outbox VALUES(%s,'document','scope',%s,1,%s,%s,'pending')", (operation,updated[0],state,manifest_hash))
            return updated[0]


def _reconcile(connection, schema, operation):
    with connection:
        with connection.cursor() as cursor:
            _search_path(cursor, schema)
            cursor.execute("SELECT o.lifecycle,o.content,o.state,o.scope_id,o.manifest_sha256,i.lifecycle,i.content,i.state,i.scope_id,v.manifest_sha256 FROM outbox o JOIN identities i USING(document_id) JOIN versions v ON v.document_id=o.document_id AND v.content=o.content WHERE operation_id=%s FOR UPDATE OF o",(operation,))
            row = cursor.fetchone()
            if row is None:
                raise ValueError("unknown operation")
            status = "reconciled" if row[:5] == row[5:] else "stale"
            cursor.execute("UPDATE outbox SET status=%s WHERE operation_id=%s",(status,operation))
            return status


def _verify_bytes(connection, schema):
    with connection:
        with connection.cursor() as cursor:
            _search_path(cursor,schema)
            cursor.execute("SELECT document_id,content,source,source_sha256,manifest_sha256 FROM versions ORDER BY document_id,content")
            versions = cursor.fetchall()
            for document,content,source,digest,manifest_digest in versions:
                if _sha(bytes(source)) != digest:
                    raise ValueError("source bytes mismatch")
                cursor.execute("SELECT locator,bytes,sha256 FROM chunks WHERE document_id=%s AND content=%s ORDER BY locator", (document,content))
                rows = cursor.fetchall()
                if not rows or [row[0] for row in rows] != list(range(len(rows))):
                    raise ValueError("incomplete manifest")
                manifest = []
                for locator,chunk,chunk_digest in rows:
                    chunk = bytes(chunk)
                    chunk.decode("utf-8",errors="strict")
                    if _sha(chunk) != chunk_digest:
                        raise ValueError("chunk bytes mismatch")
                    manifest.append({"locator":locator,"sha256":chunk_digest,"length":len(chunk)})
                if _sha(_json(manifest).encode()) != manifest_digest:
                    raise ValueError("manifest mismatch")
    return True


def run_rehearsal(dsn, backup_path):
    """Run real isolated DDL/transactions and restore an exact logical artifact.

    Schemas remain for inspection until the disposable container is destroyed.
    The logical artifact contains this harness's supplied bytes; never secrets.
    """
    if type(dsn) is not str or not dsn:
        raise ValueError("explicit isolated PostgreSQL DSN required")
    backup_path = Path(backup_path)
    # Refuse overwrite before opening a database or creating schemas.
    with backup_path.open("xb"):
        pass
    connection = psycopg2.connect(dsn, connect_timeout=5)
    second = None
    try:
        with connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT current_database(),current_setting('server_version_num')::int")
                database, version = cursor.fetchone()
                if database != DATABASE or not 160000 <= version < 170000:
                    raise ValueError("dedicated PostgreSQL 16 rehearsal database required")
        ddl = DDL_PATH.read_text()
        schema = "sentinel_rehearsal_" + uuid.uuid4().hex
        restore_schema = schema + "_restore"
        _schema(connection,schema,ddl)
        manifest_hash = _seed(connection,schema)
        before = _inventory(connection,schema)
        # Force the LAST statement to fail after catalog and revision changed.
        try:
            _transition(connection,schema,operation="create",expected=1,state="archived",manifest_hash=manifest_hash)
        except psycopg2.errors.UniqueViolation:
            pass
        else:
            raise AssertionError("outbox failure was not raised")
        if _inventory(connection,schema) != before:
            raise AssertionError("catalog/outbox rollback was not atomic")
        second = psycopg2.connect(dsn,connect_timeout=5)
        if _transition(second,schema,operation="archive",expected=1,state="archived",manifest_hash=manifest_hash) != 2:
            raise AssertionError("archive generation mismatch")
        try:
            _transition(connection,schema,operation="late",expected=1,state="archived",manifest_hash=manifest_hash)
        except ValueError:
            pass
        else:
            raise AssertionError("stale CAS accepted")
        if _reconcile(connection,schema,"create") != "stale":
            raise AssertionError("late completion accepted")
        _transition(connection,schema,operation="restore",expected=2,state="pending",manifest_hash=manifest_hash)
        _transition(connection,schema,operation="delete",expected=3,state="tombstoned",manifest_hash=manifest_hash)
        try:
            _transition(connection,schema,operation="resurrect",expected=4,state="pending",manifest_hash=manifest_hash)
        except ValueError:
            pass
        else:
            raise AssertionError("tombstone resurrected")
        if _reconcile(connection,schema,"delete") != "reconciled":
            raise AssertionError("current relational completion rejected")
        _verify_bytes(connection,schema)
        # Exercise a real permission revocation in the same dialect.
        with connection:
            with connection.cursor() as cursor:
                _search_path(cursor,schema)
                cursor.execute("DELETE FROM grants WHERE principal_id='principal' AND scope_id='scope'")
                cursor.execute("UPDATE principals SET permission_epoch=permission_epoch+1 WHERE principal_id='principal'")
        inventory = _inventory(connection,schema)
        artifact = {"format":"sentinel-isolated-postgres-logical-v1","database":database,"server_version_num":version,
                    "schema_sha256":_sha(ddl.encode()),"source_schema":schema,"tables":inventory}
        serialized = _json(artifact).encode()
        backup_path.write_bytes(serialized)
        artifact_digest = _sha(backup_path.read_bytes())
        # Reload and check exact artifact/schema binding before replay.
        loaded_bytes = backup_path.read_bytes()
        if _sha(loaded_bytes) != artifact_digest:
            raise ValueError("backup artifact changed")
        loaded = json.loads(loaded_bytes)
        if loaded["schema_sha256"] != _sha(ddl.encode()) or loaded["database"] != database:
            raise ValueError("backup target/schema binding mismatch")
        _schema(connection,restore_schema,ddl)
        with connection:
            with connection.cursor() as cursor:
                _search_path(cursor,restore_schema)
                for table in TABLES:
                    data = loaded["tables"][table]
                    query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                        sql.Identifier(table),sql.SQL(",").join(map(sql.Identifier,data["columns"])),
                        sql.SQL(",").join(sql.Placeholder() for _ in data["columns"]))
                    for row in data["rows"]:
                        cursor.execute(query,tuple(_restore_value(value) for value in row))
        restored = _inventory(connection,restore_schema)
        if restored != inventory:
            raise AssertionError("restore inventory mismatch")
        _verify_bytes(connection,restore_schema)
        if _reconcile(connection,restore_schema,"create") != "stale" or _reconcile(connection,restore_schema,"delete") != "reconciled":
            raise AssertionError("restored event state mismatch")
        return {"format":"sentinel-isolated-postgres-rehearsal-report-v1","database":database,
                "server_version_num":version,"schema":schema,"restore_schema":restore_schema,
                "schema_sha256":_sha(ddl.encode()),"backup_sha256":artifact_digest,
                "source_inventory_sha256":_sha(_json(inventory).encode()),"restore_inventory_sha256":_sha(_json(restored).encode()),
                "counts":{table:len(data["rows"]) for table,data in inventory.items()},
                "checks":{"actual_postgres_transactions":True,"atomic_outbox_rollback":True,"separate_connection_cas":True,
                          "stale_completion_denied":True,"tombstone_retained":True,"permission_revoked":True,
                          "source_manifest_bytes_verified":True,"exact_artifact_restore":True},
                "index_verified":False,"application_migrated":False,"production_enabled":False,
                "release_authorized":False,"semantic_grounding_verified":False,"proposition_to_inference":"closed"}
    finally:
        if second is not None:
            second.close()
        connection.close()


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--backup",required=True)
    parser.add_argument("--report",required=True)
    arguments = parser.parse_args()
    # Do not print connection exceptions: they can include host/user details.
    try:
        result = run_rehearsal(os.environ.get("SENTINEL_ISOLATED_POSTGRES_DSN"),arguments.backup)
        with Path(arguments.report).open("x") as stream:
            stream.write(_json(result) + "\n")
        print(_json(result))
    except Exception as error:
        print(_json({"status":"failed","reason":type(error).__name__,"production_enabled":False}))
        raise SystemExit(1) from None
