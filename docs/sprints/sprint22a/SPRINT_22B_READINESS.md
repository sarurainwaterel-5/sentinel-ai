# Sprint 22B readiness

The next recommended sprint is evidence-grounded, recommendation-only incident investigation. Sprint 22A supplies scoped durable observations, deterministic health, dependency context and manually created incident drafts; it does not activate investigators or infer root causes.

## Stable integration boundaries

| Future component | Permitted input/output contract |
|---|---|
| Incident Investigator | Authorized bounded incident/evidence package; hypotheses citing exact observation/evidence references |
| Operational Memory | Verified incident outcomes with scope, versioned provenance and explicit verification authority |
| Recovery Planner | Cited investigation findings; proposed procedures requiring separate authorization |
| Independent Verifier | Bound evidence and hypotheses; explicit support, contradiction or uncertainty findings |
| Sentinel Supervisor | Explicit workflow authority and governed coordination; no implicit execution grant |

Evidence packages must preserve exact tenant/application/service scope, observation IDs, source and ingestion times, validation status, evidence digests and configured dependency references. Canonical package hashing binds the supplied version; it does not prove semantic correctness. Package creation is a bounded authorized read, not permission to launch a model or agent.

The current `investigation_package` is deliberately smaller than that future contract: it returns the service configuration, exact tenant/application, newest 100 immutable `source_claims` in ascending source-time/ID order, the scoped `audit_head`, `capabilities_active: false` and governance constants, with an outer canonical SHA-256 digest. It does not attach validation records, incident state or dependency edges; those are separate authorized queries. Future composition must bind these additional snapshots explicitly rather than interpreting this package as a complete investigation or upgrading source claims to facts.

The current manual incident record has exactly `schema_version`, `tenant_id`, `application_id`, `service_id`, `incident_id`, `initial_observation_ids`, `evidence_refs`, `status`, `created_at` and `updated_at`. Only `DRAFT` creation is supported. It requires 1–100 unique initial observation references belonging to the same service and 1–100 valid evidence references; creation and update timestamps are equal on creation. It does not implement investigation transitions or automatic incident declaration. Exact canonical replay is idempotent, while altered bytes under an existing incident identity conflict.

## Required before activating investigation

1. Define a separately approved incident workflow and operator permissions. Do not turn arbitrary observations into incidents automatically.
2. Preserve Sprint 21-F coordinator behavior and use an explicitly reviewed composition adapter; do not add a competing scheduler. Existing offline answer fixtures are not production orchestration.
3. Define evidence sufficiency and hypothesis/citation contracts, including contradictory, unavailable, stale and source-claim-only data. Recheck authorization and evidence versions at publication.
4. Establish independent semantic evaluation and owner acceptance. ADR-037 remains Proposed; synthetic checks cannot close the proposition-to-inference boundary.
5. Verify investigator/verifier independence, provider budgets, cancellation, time limits and no-action behavior. No model provider should be called merely because an incident draft exists.
6. Define memory verification, correction, revocation, retention and deletion policies before treating prior outcomes as trusted operational knowledge.
7. Keep recovery procedures as proposals. Any execution capability needs separate authorization, safety review and a future scope decision.

External application collectors, production credentials, multi-application supervisory access, shared infrastructure relationships and production persistence deployment are future integrations requiring explicit approval. No production access to Sentinel Trading AI, Mozart Clip, Legacy Partners or Padoukiquoy Nation member portal has been established by this sprint.
