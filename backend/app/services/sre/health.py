"""Deterministic evidence evaluation; no IO, clock access, or remediation."""
from datetime import datetime, timezone
import re

HEALTH_STATES = ("HEALTHY", "DEGRADED", "UNHEALTHY", "UNKNOWN")


def _time(value):
    if not isinstance(value, str) or len(value) > 64:
        raise ValueError("invalid timestamp")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset().total_seconds() != 0:
        raise ValueError("UTC timestamp required")
    return parsed.astimezone(timezone.utc)


def evaluate_health(service, observations, *, evaluated_at):
    """Evaluate one authorized service snapshot with explicit caller-supplied UTC time.

    Caller must obtain service/observations from authorized durable storage. Evidence
    quality is a storage trust decision, never inferred from a source's self-label.
    """
    result = {"state": "UNKNOWN", "reason": "INVALID_INPUT", "evaluated_at": evaluated_at,
              "observation_ids": [], "execution_authority": "NONE"}
    try:
        now = _time(evaluated_at)
        if not isinstance(service, dict) or not isinstance(observations, (list, tuple)) or len(observations) > 10000:
            return result
        scope = tuple(service.get(k) for k in ("tenant_id", "application_id", "service_id"))
        if not all(isinstance(x, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}", x) for x in scope):
            return result
        if service.get("monitoring_enabled") is not True:
            return {**result, "reason": "MONITORING_DISABLED"}
        policy = service.get("health_policy", {})
        checks = policy.get("required_checks")
        age = policy.get("max_age_seconds")
        if (not isinstance(checks, list) or not checks or len(checks) > 32 or
                any(not isinstance(c, str) or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,127}", c) for c in checks) or
                len(set(checks)) != len(checks) or type(age) is not int or not 1 <= age <= 86400):
            return {**result, "reason": "INVALID_POLICY"}
        selected = []
        outcomes = []
        for check in checks:
            candidates = []
            for observation in observations:
                if not isinstance(observation, dict):
                    return result
                if tuple(observation.get(k) for k in ("tenant_id", "application_id", "service_id")) != scope:
                    return {**result, "reason": "SCOPE_MISMATCH"}
                if observation.get("observation_type") != "SERVICE_HEALTH":
                    continue
                payload = observation.get("payload", {})
                if not isinstance(payload, dict):
                    return result
                if payload.get("check_id") != check:
                    continue
                source_time = _time(observation.get("source_timestamp"))
                ingested = _time(observation.get("ingested_at"))
                if source_time > now or ingested > now or ingested < source_time:
                    return {**result, "reason": "INVALID_TEMPORAL_EVIDENCE"}
                candidates.append((source_time, observation))
            if not candidates:
                return {**result, "reason": "MISSING_EVIDENCE"}
            latest = max(t for t, _ in candidates)
            newest = [o for t, o in candidates if t == latest]
            if (now - latest).total_seconds() > age:
                return {**result, "reason": "STALE_EVIDENCE"}
            values = {o["payload"].get("outcome") for o in newest}
            if len(values) != 1:
                return {**result, "reason": "CONTRADICTORY_EVIDENCE"}
            outcome = values.pop()
            if outcome not in {"PASS", "PARTIAL", "FAIL", "COLLECTOR_ERROR"}:
                return result
            if any(o.get("data_quality") != "VALIDATED" or
                   not isinstance(o.get("source_id"), str) or not o.get("source_id") or
                   not re.fullmatch(r"sha256:[0-9a-f]{64}", str(o.get("evidence_ref", ""))) or
                   not isinstance(o.get("observation_id"), str) or not o.get("observation_id") for o in newest):
                return {**result, "reason": "UNVALIDATED_EVIDENCE"}
            if outcome == "COLLECTOR_ERROR":
                return {**result, "reason": "COLLECTOR_FAILURE"}
            outcomes.append(outcome)
            selected.extend(o["observation_id"] for o in newest)
        state = "UNHEALTHY" if "FAIL" in outcomes else "DEGRADED" if "PARTIAL" in outcomes else "HEALTHY"
        return {**result, "state": state, "reason": "CURRENT_VALID_EVIDENCE", "observation_ids": sorted(set(selected))}
    except (ValueError, TypeError, AttributeError, OverflowError):
        return result
