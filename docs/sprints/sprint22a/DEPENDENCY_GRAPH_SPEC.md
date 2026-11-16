# Service dependency graph

Edges are scoped configuration records with tenant/application ownership, an edge identity, provider service, dependent service, relationship type, creation time and evidence/configuration reference. Both endpoint services must exist in the same authorized tenant and application.

Exact version-1 keys are `schema_version`, `tenant_id`, `application_id`, `dependency_id`, `source_service_id`, `dependent_service_id`, `relationship_type`, `created_at` and `evidence_ref`. Edge identity is `dependency_id`, not a service ID. An endpoint pair is unique within the owning tenant/application. Exact canonical replay of an existing dependency is idempotent; altered bytes under the same edge identity conflict. The default graph capacity is 1,024 edges per tenant/application, configurable only through trusted bounded resource limits.

Direction is explicit: `source_service_id` is the required provider; `dependent_service_id` is its consumer. Thus a database-to-API edge records that the API depends on the database. Supported relationship types are `REQUIRES` and `USES`. Neither type establishes that a provider caused a consumer's failure.

Before committing an edge, validate both endpoints, reject self-dependencies and detect whether adding the edge creates a directed cycle. Cyclic proposals are rejected as configuration conflicts, rather than silently discarding an edge or recursively traversing forever. Graph traversal and queries are bounded. Edge creation and its audit event share one transaction; referential constraints prevent orphan endpoints.

Graph records survive explicit store close/open and process restarts. Registry dependency references are derived from these records. Cross-tenant or cross-application references are denied even if the caller happens to have separate grants for both applications. Future shared dependencies require a separately reviewed model and authorization policy.

No dependency traversal starts collectors, schedules investigators, changes health states or declares incidents. Future investigators may cite edges as configured investigative context while distinguishing configuration claims from observed causal evidence.
