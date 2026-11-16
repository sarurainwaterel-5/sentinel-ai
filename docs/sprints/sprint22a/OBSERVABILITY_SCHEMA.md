# Operational observation schema

An observation describes a source claim about one registered service. Ingestion alone never establishes truth or grants health authority.

| Field | Meaning |
|---|---|
| `schema_version` | Explicit supported record version |
| `observation_id` | Stable event identity within the owning scope |
| `tenant_id`, `application_id`, `service_id` | Exact owning service identity |
| `observation_type` | Bounded supported event category |
| `source_id` | Declared producing source |
| `source_timestamp` | UTC event time reported by the source |
| `ingested_at` | UTC ingestion time |
| `evidence_ref` | SHA-256 reference binding evidence bytes |
| `severity` | Normalized operational severity |
| `data_quality` | Source claim versus separately validated evidence |
| `correlation_id` | Bounded correlation identity, not causal proof |
| `payload` | Strict bounded operational attributes |

Health, errors, logs, metrics, dependency failures, deployment, resource and security events have foundational representation. This does not mean collectors for those categories are installed. Arbitrary log text, stack traces, URLs, credentials and provider responses are not a necessary ingestion surface.

Version-1 type values are `SERVICE_HEALTH`, `APPLICATION_ERROR`, `STRUCTURED_LOG`, `PERFORMANCE_METRIC`, `DEPENDENCY_FAILURE`, `DEPLOYMENT_EVENT`, `RESOURCE_USAGE` and `SECURITY_EVENT`. Severities are `INFO`, `WARNING`, `ERROR` and `CRITICAL`. Incoming quality is `SOURCE_CLAIM` or `INVALID`; callers cannot ingest `VALIDATED` directly. Service-health payloads contain exactly `check_id` and `outcome`, where outcome is `PASS`, `PARTIAL`, `FAIL` or `COLLECTOR_ERROR`. Other event types require `event_code` and permit only `metric_name`, finite bounded numeric `value` and `unit` in addition. A structured-log category therefore does not permit free-form log ingestion.

All fields are required and unknown keys are rejected. Identifiers are bounded to 128 characters, timestamps normalize to UTC microseconds, evidence references use `sha256:` plus 64 lowercase hexadecimal digits, and serialized records are bounded to 8,192 characters. Pattern-based sensitive-data rejection supplements this strict schema; it is not a general-purpose data-loss-prevention guarantee.

## Integrity and validation

Ordinary ingestion preserves `SOURCE_CLAIM` status. A distinct authorization capability must validate an observation and leave an audit record before it can contribute as `VALIDATED` evidence. A producer's self-declared quality is not an authority credential. Validation establishes the checks performed by this local system; it cannot certify an external event's semantic accuracy.

The original claim remains immutable. A separate validation record binds `observation_id`, its `observation_hash`, `reviewer_id`, `reviewed_at` and a review `evidence_ref` to the same tenant/application. `INVALID` observations cannot be promoted. Review time cannot precede ingestion. Query results preserve `source_data_quality` and the source `record_sha256`, and attach the validation separately. Health evaluation applies a validation only when its review time is no later than the explicit evaluation time. Exact canonical validation replay is idempotent; changed review bytes for an already validated identity conflict.

Canonical record digests detect conflicting reuse of an event identity. Exact replays are idempotent; changed bytes under an existing identity are rejected. Source order and ingestion order are distinct. Out-of-order arrival is retained without allowing an older success to supersede newer source-time failure evidence. Stable timestamp/identity ordering supports deterministic retrieval and replay.

Evidence references bind bytes, not their real-world interpretation. An observation digest is not a signature, a trusted timestamp, or proof that a collector reported accurately. Queries remain scoped and bounded, and references must resolve within the permitted application boundary.

## Safe local collection

The one-shot adapter calls a separate constant-time development liveness function with the same trivial response semantics as Sentinel's existing `/health` handler. It does not invoke that HTTP handler or establish that an installed daemon is running. The existing application entrypoint and routes remain unchanged, preserving frozen acceptance bindings. The adapter performs no socket or database operation, accepts no target URL or arbitrary callback, reads no production credential, hashes the bounded signal bytes and emits a source claim. Source time is explicit; no production history is fabricated. There is no polling loop, retry system or external collector.

`SREStore.collect_local` requires read access plus explicit ingest and validate grants. It stores the claim and its explicit local validation in separate audited transactions. If validation fails after ingestion, the immutable claim remains unvalidated and cannot establish health. The wrapper is one-shot and does not provision a principal or start background work.
