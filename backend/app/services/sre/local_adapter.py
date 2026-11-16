"""Explicit one-shot, no-network Sentinel development liveness adapter."""
import hashlib
import json
import re
from .health import _time
from .local_health import sentinel_process_liveness

SOURCE_ID = "sentinel-local-liveness"


def collect_local_observation(service, *, observed_at, observation_id, correlation_id):
    """Return a bounded observation claim for trusted store validation.

    This is process-callable liveness, not HTTP reachability, database readiness,
    semantic correctness, or a production health assertion. No background work.
    """
    _time(observed_at)
    for value in (observation_id, correlation_id, service.get("tenant_id", "")):
        if not isinstance(value, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}", value):
            raise ValueError("invalid local observation identifier")
    if (service.get("application_id") != "sentinel-ai" or service.get("service_id") != "sentinel-api" or
            service.get("environment") not in {"local", "development"} or service.get("monitoring_enabled") is not True):
        raise ValueError("local Sentinel observation scope required")
    # This known function has no blocking IO, callbacks, loops, or external inputs.
    try:
        snapshot = sentinel_process_liveness()
    except Exception:
        # Collector exceptions are not evidence of application failure. Never
        # persist exception text, which can include environment or credentials.
        snapshot = {"collector_status": "unavailable"}
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()
    if len(encoded) > 256:
        raise ValueError("local signal exceeds evidence bound")
    outcome = "PASS" if snapshot == {"status": "healthy", "service": "SentinelAI"} else "COLLECTOR_ERROR"
    return {"schema_version": 1, "observation_id": observation_id,
            "tenant_id": service["tenant_id"], "application_id": service["application_id"],
            "service_id": service["service_id"], "observation_type": "SERVICE_HEALTH", "source_id": SOURCE_ID,
            "source_timestamp": observed_at, "ingested_at": observed_at,
            "evidence_ref": "sha256:" + hashlib.sha256(encoded).hexdigest(),
            "severity": "INFO" if outcome == "PASS" else "WARNING", "data_quality": "SOURCE_CLAIM",
            "correlation_id": correlation_id, "payload": {"check_id": "process-liveness", "outcome": outcome}}
