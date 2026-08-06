ADR-016: Introduce Planning Verification as an Independent Cognitive Faculty

Status

Accepted

Context

Planning recommends a course of action.

However, planning alone cannot determine whether a proposed plan is:

structurally coherent,
traceable to evidence,
complete,
compliant with declared operational boundaries.

Earlier architectural discussions considered embedding these responsibilities inside the Planning Engine or Planning Confidence Engine.

Doing so would have mixed planning and governance responsibilities, violating Sentinel's principle of one responsibility per engine.

Decision

Introduce an independent Planning Verification Faculty composed of specialized deterministic verification engines.

The faculty contains four independent specialists:

StructuralIntegrityVerifier
TraceabilityVerifier
CompletenessVerifier
ConstraintVerifier

Each specialist evaluates exactly one aspect of a PlanningResult.

No specialist modifies the planning subject.

Verification remains read-only.

Planning remains responsible only for proposing plans.

Verification becomes responsible only for evaluating plans.

Consequences

Positive:

Preserves strict separation of responsibilities.
Enables independent testing of each verification concern.
Allows future verification specialists without modifying planning.
Establishes a reusable faculty pattern for future cognitive domains.
Enables a dedicated VerificationConfidenceEngine.

Trade-offs:

Introduces additional components.
Requires orchestration across multiple verification specialists.

These trade-offs are accepted in exchange for architectural clarity.

Principles Reinforced
One Responsibility Per Engine
Deterministic Before Generative
Observable Cognition
Verification Before Expansion


