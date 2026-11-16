# Deterministic health evaluation

`evaluate_health(service, observations, evaluated_at=...)` is a pure evaluator: callers provide an authorized service snapshot, bounded authorized observations and an explicit UTC evaluation time. It performs no I/O, wall-clock reads, scheduling or remediation.

A health policy supplies distinct required check IDs and an explicit positive freshness limit. The supported local freshness bound is 1–86,400 seconds; there is no implicit production threshold. A disabled service returns `UNKNOWN`. Missing or malformed registration/policy input cannot establish health.

For each required check, select the newest source timestamp among matching service-health observations. Do not select an older success merely because newer evidence is unvalidated, failed or contradictory. Evidence from another tenant/application/service invalidates the input. Source and ingestion timestamps must be valid UTC, source time must not exceed ingestion time, and neither may exceed the evaluation time.

| Condition | Result |
|---|---|
| Every required check has fresh validated `PASS` evidence | `HEALTHY` |
| All checks are evaluable, at least one `PARTIAL`, none `FAIL` | `DEGRADED` |
| All checks are evaluable, at least one `FAIL` | `UNHEALTHY` |
| Required evidence absent, stale, unvalidated, malformed or conflicting | `UNKNOWN` |
| Newest observation is `COLLECTOR_ERROR` | `UNKNOWN` |

Freshness is measured from source time. Evidence exactly at the configured age boundary remains current; older evidence is stale. Equal-source-time observations with different outcomes are contradictory. Matching observations at the newest timestamp must all be validated with valid source identities and SHA-256 evidence references.

If any required check cannot be evaluated reliably, the overall result is `UNKNOWN`, even if another check reports failure. This conservative rule avoids asserting complete service functionality from incomplete evidence. A collector failure is a failure to establish application state, not confirmation that the application failed.

Results include the state, bounded reason code, evaluation time and selected observation IDs for successful classifications. Execution authority is always `NONE`. Dependencies provide context only and do not propagate failures into another service's health. Local `process-liveness` success asserts only that the known function was callable; it establishes no downstream readiness or empirical semantic acceptance.
