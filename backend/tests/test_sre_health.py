"""Offline deterministic health and local signal tests."""
import copy
import unittest
from unittest.mock import patch
from app.services.sre.health import evaluate_health
from app.services.sre.local_adapter import collect_local_observation
from app.services.sre.local_health import sentinel_process_liveness

NOW = "2026-11-16T12:00:00Z"


def service():
    return {"tenant_id": "rain", "application_id": "sentinel-ai", "service_id": "sentinel-api",
            "environment": "development", "monitoring_enabled": True,
            "health_policy": {"required_checks": ["process-liveness"], "max_age_seconds": 60}}


def obs(outcome="PASS", **updates):
    result = collect_local_observation(service(), observed_at=NOW, observation_id="obs-1", correlation_id="cor-1")
    result["data_quality"] = "VALIDATED"  # fixture simulates trusted storage decision
    result["payload"]["outcome"] = outcome
    result.update(updates)
    return result


class HealthTests(unittest.TestCase):
    def evaluate(self, observations, svc=None, at=NOW):
        return evaluate_health(service() if svc is None else svc, observations, evaluated_at=at)

    def test_healthy(self): self.assertEqual(self.evaluate([obs()])["state"], "HEALTHY")
    def test_degraded(self): self.assertEqual(self.evaluate([obs("PARTIAL")])["state"], "DEGRADED")
    def test_unhealthy(self): self.assertEqual(self.evaluate([obs("FAIL")])["state"], "UNHEALTHY")
    def test_missing(self): self.assertEqual(self.evaluate([])["reason"], "MISSING_EVIDENCE")
    def test_unregistered(self): self.assertEqual(self.evaluate([obs()], {})["state"], "UNKNOWN")
    def test_disabled(self):
        s = service(); s["monitoring_enabled"] = False
        self.assertEqual(self.evaluate([obs()], s)["reason"], "MONITORING_DISABLED")
    def test_stale(self):
        self.assertEqual(self.evaluate([obs()], at="2026-11-16T12:01:01Z")["reason"], "STALE_EVIDENCE")
    def test_freshness_boundary(self):
        self.assertEqual(self.evaluate([obs()], at="2026-11-16T12:01:00Z")["state"], "HEALTHY")
    def test_conflicting_same_timestamp(self):
        self.assertEqual(self.evaluate([obs(), obs("FAIL", observation_id="obs-2")])["reason"], "CONTRADICTORY_EVIDENCE")
    def test_recent_failure_wins(self):
        older = obs(source_timestamp="2026-11-16T11:59:50Z", observation_id="old")
        self.assertEqual(self.evaluate([older, obs("FAIL")])["state"], "UNHEALTHY")
    def test_collector_failure(self): self.assertEqual(self.evaluate([obs("COLLECTOR_ERROR")])["reason"], "COLLECTOR_FAILURE")
    def test_claim_not_validated(self): self.assertEqual(self.evaluate([obs(data_quality="SOURCE_CLAIM")])["state"], "UNKNOWN")
    def test_new_claim_cannot_fallback_to_old_valid(self):
        old = obs(source_timestamp="2026-11-16T11:59:50Z", observation_id="old")
        self.assertEqual(self.evaluate([old, obs(data_quality="SOURCE_CLAIM")])["reason"], "UNVALIDATED_EVIDENCE")
    def test_missing_evidence_hash(self): self.assertEqual(self.evaluate([obs(evidence_ref=None)])["state"], "UNKNOWN")
    def test_cross_tenant(self): self.assertEqual(self.evaluate([obs(tenant_id="other")])["reason"], "SCOPE_MISMATCH")
    def test_cross_application(self): self.assertEqual(self.evaluate([obs(application_id="other")])["reason"], "SCOPE_MISMATCH")
    def test_cross_service(self): self.assertEqual(self.evaluate([obs(service_id="other")])["reason"], "SCOPE_MISMATCH")
    def test_future_source(self):
        self.assertEqual(self.evaluate([obs(source_timestamp="2026-11-16T12:00:01Z")])["state"], "UNKNOWN")
    def test_future_ingestion(self):
        self.assertEqual(self.evaluate([obs(ingested_at="2026-11-16T12:00:01Z")])["state"], "UNKNOWN")
    def test_invalid_chronology(self):
        self.assertEqual(self.evaluate([obs(ingested_at="2026-11-16T11:59:59Z")])["state"], "UNKNOWN")
    def test_naive_time(self): self.assertEqual(self.evaluate([obs()], at="2026-11-16T12:00:00")["state"], "UNKNOWN")
    def test_no_implicit_threshold(self):
        s = service(); del s["health_policy"]["max_age_seconds"]
        self.assertEqual(self.evaluate([obs()], s)["reason"], "INVALID_POLICY")
    def test_bool_is_not_threshold(self):
        s = service(); s["health_policy"]["max_age_seconds"] = True
        self.assertEqual(self.evaluate([obs()], s)["reason"], "INVALID_POLICY")
    def test_missing_required_check(self):
        s = service(); s["health_policy"]["required_checks"].append("storage")
        self.assertEqual(self.evaluate([obs()], s)["reason"], "MISSING_EVIDENCE")
    def test_input_order_deterministic(self):
        a = obs(source_timestamp="2026-11-16T11:59:50Z", observation_id="old")
        b = obs("FAIL")
        self.assertEqual(self.evaluate([a,b]), self.evaluate([b,a]))
    def test_no_input_mutation(self):
        s = service(); observations = [obs()]; before = copy.deepcopy((s, observations))
        self.evaluate(observations, s)
        self.assertEqual((s, observations), before)
    def test_bounded_history(self): self.assertEqual(self.evaluate([obs()] * 10001)["state"], "UNKNOWN")
    def test_malformed(self): self.assertEqual(self.evaluate([None])["state"], "UNKNOWN")
    def test_local_signal_compatibility(self):
        self.assertEqual(sentinel_process_liveness(), {"status":"healthy", "service":"SentinelAI"})
    def test_adapter_is_claim_and_deterministic(self):
        args = dict(observed_at=NOW, observation_id="local-1", correlation_id="cor-1")
        a = collect_local_observation(service(), **args)
        self.assertEqual(a, collect_local_observation(service(), **args))
        self.assertEqual(a["data_quality"], "SOURCE_CLAIM")
        self.assertEqual(self.evaluate([a])["state"], "UNKNOWN")
    def test_external_disabled(self):
        for field, value in [("application_id", "trading"), ("environment", "production"), ("service_id", "other"), ("monitoring_enabled", False)]:
            s = service(); s[field] = value
            with self.assertRaises(ValueError):
                collect_local_observation(s, observed_at=NOW, observation_id="id", correlation_id="cor")
    def test_safe_payload(self):
        s = service(); s["password"] = "DO_NOT_COPY"
        self.assertNotIn("DO_NOT_COPY", str(collect_local_observation(s, observed_at=NOW, observation_id="id", correlation_id="cor")))
    def test_unexpected_signal_is_collector_error(self):
        with patch("app.services.sre.local_adapter.sentinel_process_liveness", return_value={"status":"changed"}):
            self.assertEqual(collect_local_observation(service(), observed_at=NOW, observation_id="id", correlation_id="cor")["payload"]["outcome"], "COLLECTOR_ERROR")
    def test_collector_exception_is_safe(self):
        with patch("app.services.sre.local_adapter.sentinel_process_liveness", side_effect=RuntimeError("SECRET")):
            value = collect_local_observation(service(), observed_at=NOW, observation_id="id", correlation_id="cor")
            self.assertEqual(value["payload"]["outcome"], "COLLECTOR_ERROR")
            self.assertNotIn("SECRET", str(value))
    def test_no_network(self):
        with patch("socket.socket", side_effect=AssertionError("network forbidden")):
            collect_local_observation(service(), observed_at=NOW, observation_id="id", correlation_id="cor")

if __name__ == "__main__": unittest.main()
