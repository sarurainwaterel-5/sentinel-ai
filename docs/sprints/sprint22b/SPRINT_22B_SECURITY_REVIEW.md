# Sprint 22B security review

Local/offline development only. Production authorization denied. The existing frozen governed-answer files and ADR-037 are preserved. No execution tools, provider SDK clients, automatic remediation, broker access, deployment or external collectors are added.

Control review: issued principal handles and catalog epochs are rechecked at request entry, retrieval, persistence and publication. A new authentication session is required per HTTP request because the existing session is deliberately single-use. Companion grants separately authorize read, converse, inspect, investigate and delete. Owner/scope bindings protect history. Client JSON cannot set owner, scope, permission or provider. The API rejects extra fields and bounds turn text and request bodies.

Repository evidence is fixed-allowlist, no-symlink, byte-bounded and hash/AST checked. Returned text is curated, never arbitrary code/configuration. User prose cannot choose files, invoke tools or modify the registry. React renders escaped text and plain citation paths, with no arbitrary evidence navigation. Model prose stays withheld, including attempted injected providers.

Conversation hashes and audit chains detect accidental alteration, missing rows and divergent records. They cannot establish semantic truth or resist a privileged local owner rewriting the whole unanchored store. Common secret-shaped messages are refused; arbitrary sensitive prose cannot be recognized completely. Private database permissions, bounded retention and deletion limit exposure.

Incident verifier independently enforces supported hypothesis predicates, citations, contradictions, temporal scope and a closed causal policy. Validation receipts establish reviewed record provenance, not observed-event truth. All causal root causes remain withheld.

Limitations: no independent live-model semantic evaluation, no production transport assessment, no distributed concurrency guarantee, no autonomous background retention worker, no token streaming and browser abort does not guarantee server rollback. Full test results are recorded in the implementation report.

Independent integration review identified pre-limit body buffering and loss of topic on repeated follow-ups. Both were corrected with streamed cumulative limits and substantive-topic retention, plus regression cases. The reviewer confirmed all 19 source pins and found no further material authorization, ownership or citation defects. This review does not constitute live semantic or production acceptance.
