# Domains operator workspace

Domains consumes the validated backend registry and organization-scoped document catalog observations. It does not activate domains, infer maturity, or create constitutional authority. ADR-019 remains the governing boundary.

The shared header now names the Domains workspace. Its cards include system and user registry entries, documented maturity, indexed PDF/chunk counts, archived PDF counts, architecture references, and the current knowledge scope. Architecture references are explicitly separate from taught PDFs. Memory counts represent catalog records, not a vector-integrity or semantic-accuracy assessment.

Operators can search or filter the registry, select a domain, explicitly return to All Domains, or select a domain and enter Teach, Recall, Reason, or Governance. The shared provider carries the choice across workspaces. Registry maturity and structural validation remain available in an expandable section.

GET /domains/memory observes indexed, archived, and other document records grouped by module within one organization (default scope for the single-admin installation). It does not include other organizations in those counts. Database failures return a bounded retryable error. Missing observations are displayed as unavailable, not zero. The memory route is declared ahead of the domain-ID route.

User-domain entries are displayed when supplied by the backend registry. Domain registration, mutation, and activation remain read-only in this release. Loading, failures, retries, refresh, empty search/type results, and empty domain memory are explicit states.
