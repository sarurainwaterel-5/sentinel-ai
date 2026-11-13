-- Explicit opt-in application schema. No legacy table or release flag changes.
CREATE TABLE principals (
 principal_id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
 salt BYTEA NOT NULL CHECK(octet_length(salt)=16),
 password_hash BYTEA NOT NULL CHECK(octet_length(password_hash)=32),
 credential_epoch BIGINT NOT NULL CHECK(credential_epoch>=1),
 permission_epoch BIGINT NOT NULL CHECK(permission_epoch>=1),
 disabled BOOLEAN NOT NULL DEFAULT FALSE
);
CREATE TABLE scopes (
 scope_sha256 TEXT PRIMARY KEY CHECK(scope_sha256 ~ '^[a-f0-9]{64}$'),
 scope_json JSONB NOT NULL, catalog_epoch BIGINT NOT NULL CHECK(catalog_epoch>=1)
);
CREATE TABLE grants (
 principal_id TEXT NOT NULL REFERENCES principals(principal_id),
 scope_sha256 TEXT NOT NULL REFERENCES scopes(scope_sha256),
 PRIMARY KEY(principal_id,scope_sha256)
);
CREATE TABLE source_objects (
 source_sha256 TEXT PRIMARY KEY CHECK(source_sha256 ~ '^[a-f0-9]{64}$'),
 byte_length BIGINT NOT NULL CHECK(byte_length BETWEEN 1 AND 1073741824),
 store_version TEXT NOT NULL CHECK(store_version='source-cas-v2')
);
CREATE TABLE documents (
 document_id TEXT PRIMARY KEY, scope_sha256 TEXT NOT NULL REFERENCES scopes(scope_sha256),
 version_id TEXT NOT NULL UNIQUE,
 lifecycle_epoch BIGINT NOT NULL CHECK(lifecycle_epoch>=1),
 content_epoch BIGINT NOT NULL CHECK(content_epoch>=1),
 index_epoch BIGINT NOT NULL CHECK(index_epoch>=1),
 state TEXT NOT NULL CHECK(state IN ('pending','active','archiving','archived','restoring','tombstoned','failed'))
);
CREATE TABLE versions (
 version_id TEXT PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id),
 source_sha256 TEXT NOT NULL REFERENCES source_objects(source_sha256),
 binding_json JSONB NOT NULL,
 manifest_sha256 TEXT NOT NULL CHECK(manifest_sha256 ~ '^[a-f0-9]{64}$'),
 UNIQUE(version_id,document_id)
);
ALTER TABLE documents ADD CONSTRAINT documents_current_version_fk
 FOREIGN KEY(version_id,document_id) REFERENCES versions(version_id,document_id) DEFERRABLE INITIALLY DEFERRED;
CREATE TABLE chunks (
 version_id TEXT NOT NULL REFERENCES versions(version_id),
 chunk_index INTEGER NOT NULL CHECK(chunk_index BETWEEN 0 AND 99999),
 chunk_sha256 TEXT NOT NULL CHECK(chunk_sha256 ~ '^[a-f0-9]{64}$'),
 byte_length INTEGER NOT NULL CHECK(byte_length BETWEEN 1 AND 65536),
 storage_reference TEXT NOT NULL CHECK(storage_reference='chunk-cas-v2:' || chunk_sha256),
 PRIMARY KEY(version_id,chunk_index)
);
CREATE TABLE outbox (
 operation_id UUID PRIMARY KEY, document_id TEXT NOT NULL REFERENCES documents(document_id),
 version_id TEXT NOT NULL REFERENCES versions(version_id),
 kind TEXT NOT NULL CHECK(kind IN ('create','archive','restore','tombstone')),
 lifecycle_epoch BIGINT NOT NULL, content_epoch BIGINT NOT NULL,index_epoch BIGINT NOT NULL,
 manifest_sha256 TEXT NOT NULL CHECK(manifest_sha256 ~ '^[a-f0-9]{64}$'),
 status TEXT NOT NULL CHECK(status IN ('pending','leased','acknowledged','superseded')),
 lease_token UUID, lease_until TIMESTAMPTZ, attempts INTEGER NOT NULL DEFAULT 0,
 CHECK((status='leased') = (lease_token IS NOT NULL AND lease_until IS NOT NULL)),
 CHECK(attempts BETWEEN 0 AND 10)
);
CREATE INDEX outbox_pending_idx ON outbox(status,lease_until,operation_id);
-- Version references are append-only even for callers bypassing the service.
CREATE FUNCTION reject_immutable_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN RAISE EXCEPTION 'immutable_governed_reference'; END $$;
CREATE TRIGGER immutable_versions BEFORE UPDATE OR DELETE ON versions
 FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
CREATE TRIGGER immutable_chunks BEFORE UPDATE OR DELETE ON chunks
 FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
CREATE TRIGGER immutable_source_objects BEFORE UPDATE OR DELETE ON source_objects
 FOR EACH ROW EXECUTE FUNCTION reject_immutable_mutation();
