CREATE TABLE schema_migrations (
 version INTEGER PRIMARY KEY CHECK(version=1),
 schema_sha256 TEXT NOT NULL CHECK(length(schema_sha256)=64)
) STRICT;
CREATE TABLE audit_records (
 seq INTEGER PRIMARY KEY,
 kind TEXT NOT NULL CHECK(kind IN ('DECISION','INVALID','CONFLICT','REPLAY')),
 record_id TEXT NOT NULL UNIQUE,
 payload TEXT NOT NULL CHECK(json_valid(payload)),
 previous_hash TEXT NOT NULL CHECK(length(previous_hash)=64),
 record_hash TEXT NOT NULL UNIQUE CHECK(length(record_hash)=64),
 CHECK(json_extract(payload,'$.authority.advisory_only') IS 1),
 CHECK(json_extract(payload,'$.authority.execution_authorized') IS 0),
 CHECK(json_extract(payload,'$.authority.live_authorized') IS 0)
) STRICT;
CREATE TABLE proposal_claims (
 proposal_id TEXT PRIMARY KEY,
 event_id TEXT NOT NULL UNIQUE,
 input_hash TEXT NOT NULL CHECK(length(input_hash)=64),
 assessment_id TEXT NOT NULL UNIQUE,
 record_seq INTEGER NOT NULL UNIQUE REFERENCES audit_records(seq),
 correlation_id TEXT NOT NULL
) STRICT;
CREATE TRIGGER migrations_no_update BEFORE UPDATE ON schema_migrations BEGIN SELECT RAISE(ABORT,'IMMUTABLE_MIGRATION'); END;
CREATE TRIGGER migrations_no_delete BEFORE DELETE ON schema_migrations BEGIN SELECT RAISE(ABORT,'IMMUTABLE_MIGRATION'); END;
CREATE TRIGGER records_no_update BEFORE UPDATE ON audit_records BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
CREATE TRIGGER records_no_delete BEFORE DELETE ON audit_records BEGIN SELECT RAISE(ABORT,'IMMUTABLE_AUDIT'); END;
CREATE TRIGGER claims_no_update BEFORE UPDATE ON proposal_claims BEGIN SELECT RAISE(ABORT,'IMMUTABLE_CLAIM'); END;
CREATE TRIGGER claims_no_delete BEFORE DELETE ON proposal_claims BEGIN SELECT RAISE(ABORT,'IMMUTABLE_CLAIM'); END;
PRAGMA user_version=1;
