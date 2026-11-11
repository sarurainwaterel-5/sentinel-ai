-- Standalone disposable PostgreSQL 16 rehearsal; never an Alembic revision.
CREATE TABLE principals (
 principal_id text PRIMARY KEY CHECK (length(principal_id) BETWEEN 1 AND 200),
 permission_epoch bigint NOT NULL CHECK(permission_epoch >= 1),
 disabled boolean NOT NULL DEFAULT false
);
CREATE TABLE scopes (
 scope_id text PRIMARY KEY,
 organization_id text NOT NULL CHECK(length(organization_id) BETWEEN 1 AND 200),
 collection text NOT NULL CHECK(length(collection) BETWEEN 1 AND 200),
 module text NOT NULL CHECK(length(module) BETWEEN 1 AND 200),
 topic text NOT NULL CHECK(length(topic) BETWEEN 1 AND 200),
 revision bigint NOT NULL CHECK(revision >= 0),
 UNIQUE(organization_id, collection, module, topic)
);
CREATE TABLE grants (
 principal_id text NOT NULL REFERENCES principals(principal_id),
 scope_id text NOT NULL REFERENCES scopes(scope_id),
 PRIMARY KEY(principal_id,scope_id)
);
CREATE TABLE identities (
 document_id text PRIMARY KEY CHECK(length(document_id) BETWEEN 1 AND 200),
 scope_id text NOT NULL REFERENCES scopes(scope_id),
 lifecycle bigint NOT NULL CHECK(lifecycle >= 1),
 content bigint NOT NULL CHECK(content >= 1),
 state text NOT NULL CHECK(state IN ('pending','archived','tombstoned'))
);
CREATE TABLE versions (
 document_id text NOT NULL REFERENCES identities(document_id),
 content bigint NOT NULL CHECK(content >= 1),
 source bytea NOT NULL CHECK(octet_length(source) BETWEEN 1 AND 1048576),
 source_sha256 text NOT NULL CHECK(source_sha256 ~ '^[0-9a-f]{64}$'),
 manifest_sha256 text NOT NULL CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY(document_id,content)
);
CREATE TABLE chunks (
 document_id text NOT NULL,
 content bigint NOT NULL,
 locator integer NOT NULL CHECK(locator BETWEEN 0 AND 31),
 bytes bytea NOT NULL CHECK(octet_length(bytes) BETWEEN 1 AND 65536),
 sha256 text NOT NULL CHECK(sha256 ~ '^[0-9a-f]{64}$'),
 PRIMARY KEY(document_id,content,locator),
 FOREIGN KEY(document_id,content) REFERENCES versions(document_id,content)
);
CREATE TABLE outbox (
 operation_id text PRIMARY KEY,
 document_id text NOT NULL,
 scope_id text NOT NULL REFERENCES scopes(scope_id),
 lifecycle bigint NOT NULL CHECK(lifecycle >= 1),
 content bigint NOT NULL CHECK(content >= 1),
 state text NOT NULL CHECK(state IN ('pending','archived','tombstoned')),
 manifest_sha256 text NOT NULL CHECK(manifest_sha256 ~ '^[0-9a-f]{64}$'),
 status text NOT NULL CHECK(status IN ('pending','reconciled','stale')),
 FOREIGN KEY(document_id,content) REFERENCES versions(document_id,content)
);
