# Intelligence, Governance, and Systems

## Governing requirements

This implementation follows Bridge Experience, Sentinel Cognitive Design
Principles, the constitutional subsystem pattern, the cognitive doctrine,
ADR-029 Directed Learning, ADR-034 Persistent Reflection, and the existing
planning/verification contracts. ADR-037 stays Proposed and its independent
semantic acceptance gate stays closed.

## Intelligence

- Explore principle documents and inspect their documented connections.
- Document identities use relative paths, so similarly named files remain distinct.
- Resolve explicit Markdown links and uniquely identified references; preserve
  missing and ambiguous references without creating invented edges.
- Connections are references or classifications, not semantic truth, implementation
  proof, or causality. The existing legacy Canon Graph remains available independently.
- Inspect recent organization-scoped Learning Events, select evidence in the active
  domain, and invoke the existing deterministic Reflection faculty.
- Governing context comes from Sentinel's documents rather than caller-authored text.
- Preserve every completed reflection in append-only history, including outcomes
  that are not constitutionally admissible. History reads are bounded and scoped.
- Propose an evidence-aware plan through the established Planning faculty; inspect
  steps, risks, constraints, assumptions, provenance, confidence, and limitations.
  Planning does not execute actions.

## Governance

- Inspect principle structure, missing layers, empty instruction documents, history
  policy, human execution authority, and outstanding acceptance boundaries.
- Archive or restore operational documents through the existing memory lifecycle.
  Archived documents remain stored and are excluded from retrieval.
- Report failures without displaying successful lifecycle changes.
- Invoke the existing Verification faculty and inspect coverage, checks, findings,
  conditions, evidence provenance, and separate confidence/admissibility judgments.
- Verification creates and inspects a new planning subject for the supplied objective.
  It does not certify a previously displayed plan or authorize execution.

## Systems and Bridge

- Observe actual catalog/reflection schema availability and required vector collections.
- Count stored chunks; distinguish an empty collection from an unavailable one.
- Report credential configuration separately from provider availability.
- Refresh observations and show bounded recovery instructions.
- Bridge and the header no longer report hard-coded operational health.
- No browser response exposes credentials or raw dependency/provider errors.

## Factual ingestion history

A successfully indexed document now creates a bounded Learning Event with its
actual document/chunk references, domain, organization, and file hash. The event
records evidence acquisition only; it invents no concepts or understanding.
Duplicate uploads create no new history. If independent history recording fails,
the indexed document is preserved and the upload response reports that limitation.
Existing uploads are not retroactively relabeled as historical learning.

## Constitutional judgment

The earlier CoherenceEngine returned coherent=true and score=1.0 without evaluation.
That placeholder is now fail-closed: evaluation_status=not_evaluated, coherent=false,
score=0, with an explicit limitation and human-review recommendation. The score is
not a measured degree of conflict. Reason communicates the state as Unassessed.
Planning and Verification retain the same separate constitutional contract.

A verified constitutional assessor is still required before these results can be
represented as constitutionally assessed. This change does not invent an assessor,
weaken semantic benchmark thresholds, accept ADR-037, or open proposition inference.

## Verification

Focused tests cover path-scoped identities, ambiguous/missing references, dependency
and migration failures, scoped/limited history, factual ingestion idempotence,
rejected Reflection persistence, provider error sanitization, operator form scope,
archive failure/recovery, empty history, and retry behavior. Final regression and
live local results are recorded in the delivery report.


Final local checks: 584 backend tests and 30 frontend tests passed; lint,
production build, and git diff checks passed. Live PostgreSQL/Qdrant workflows,
organization isolation, measured readiness, factual ingestion, rejected Reflection
persistence, actual provider-backed planning/verification, and browser form
submission/navigation passed. Desktop and compact screenshots were inspected.
No empirical semantic judge benchmark ran.
