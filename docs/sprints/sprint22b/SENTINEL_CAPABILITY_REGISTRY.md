# Sentinel capability registry

The registry currently contains 12 capability records and 19 reviewed source records. The versioned machine-readable source is `backend/app/services/companion/capability_registry.json`, itself hash-pinned in self_knowledge.py. Each capability includes identifier, name, curated description, owning subsystem, implementation status, authorization status, evidence references, verification status, dependencies, limitations and last verified version.

Implementation statuses are IMPLEMENTED, EXPERIMENTAL, PLANNED, DISABLED and UNKNOWN. Authorization is separate: an implemented function can remain offline-only or denied. The displayed authorization is a policy ceiling; actual access still requires the request's issued principal and explicit scope grant.

The initial registry covers the 22A service/observation store, pure health policy, local one-shot adapter, dependencies/manual incidents, authentication, offline coordinator, disabled governed release, self-ontology, integrations and restrictions. SQLite operational evidence is distinguished from regular application SQLAlchemy infrastructure. External collectors are not active. One-shot process-callable liveness does not establish daemon readiness. Remediation, deployment, broker and trading execution remain denied.

The new 22B conversation and incident investigation records are explicitly EXPERIMENTAL and described in the implementation report; it is not promoted to live-model capability by its deterministic tests. Registry evidence reflects exact reviewed versions, not a claim that an old baseline commit contains all current changes.
