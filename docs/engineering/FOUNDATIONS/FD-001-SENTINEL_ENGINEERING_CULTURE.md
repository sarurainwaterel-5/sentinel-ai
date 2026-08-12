# FD-001 — Sentinel Engineering Culture

**Status:** Foundational Doctrine  
**Applies To:** SentinelAI Engineering  
**Authority:** Engineering Foundation  
**Principle:** Build systems whose structure makes trustworthy behavior possible.

---

## 1. Purpose

SentinelAI is not developed as a collection of features.

It is developed as a coherent system of explicit responsibilities, contracts, authorities, evidence, and boundaries.

The purpose of Sentinel engineering culture is to preserve that coherence as the system grows.

We do not measure engineering progress only by what Sentinel can do.

We also ask:

- Can the behavior be inspected?
- Can the result be traced?
- Can failure be localized?
- Can confidence be explained?
- Are authority boundaries explicit?
- Can one component change without silently changing another?
- Does the architecture remain understandable as capability increases?

Capability without structure creates fragility.

Structure allows capability to compound safely.

---

## 2. The Sentinel Way

The Sentinel Way is simple:

> Understand the responsibility.  
> Define the contract.  
> Build the smallest coherent component.  
> Test its invariants.  
> Integrate it deliberately.  
> Preserve what was learned.

We prefer deliberate architecture over accidental complexity.

We prefer explicit boundaries over hidden coupling.

We prefer inspectable state over implied behavior.

We prefer evidence over appearance.

We prefer systems that can explain their failures over systems that merely appear successful.

---

## 3. Foundation Before Framework

Do not rush toward sophisticated behavior before establishing the structures that behavior depends upon.

A strong Sentinel capability normally emerges in layers:

**Contract → Model → Engine → Formatter → Orchestrator → API → Integration**

Not every subsystem requires every layer, but responsibility should always be established before complexity is added.

Foundations are not preliminary work to escape.

They are what make later development easier.

---

## 4. Build Faculties, Not Features

A feature performs an action.

A faculty owns a cognitive responsibility.

Sentinel's cognitive architecture separates responsibilities such as:

- Reasoning
- Planning
- Verification

These faculties may cooperate, but they must not silently inherit one another's authority.

Reasoning determines what conclusion is supported.

Planning determines what course of action is proposed.

Verification determines whether a cognitive artifact deserves trust.

Separation allows each faculty to remain understandable, testable, and replaceable.

---

## 5. Simplicity Through Separation

Sentinel does not pursue simplicity by forcing everything into fewer components.

Sentinel pursues simplicity by giving each component a clear responsibility.

> Complexity shared everywhere becomes confusion.  
> Complexity separated by responsibility becomes architecture.

A component should know what it owns.

It should also know what it does not own.

This is one of Sentinel's primary defenses against architectural drift.

---

## 6. Contracts Before Implementation

Before building behavior, define what valid behavior looks like.

Contracts establish:

- required inputs;
- authoritative outputs;
- identifiers;
- references;
- states;
- invariants;
- failure conditions.

Implementation may evolve.

The meaning of the boundary must remain explicit.

A contract is not merely a data structure.

It is an agreement between responsibilities.

---

## 7. Facts Before Language

Structured cognition should exist before presentation.

Sentinel should first determine the authoritative facts of a result.

Only afterward should those facts be translated into human-readable language.

Therefore:

> Formatters explain authority.  
> They do not create authority.

A formatter may clarify a result.

It may not silently change the result.

Language is presentation.

Structure is truth.

---

## 8. Confidence Is Domain-Specific

There is no universal Sentinel confidence score.

Confidence belongs to the responsibility making the judgment.

Reasoning confidence answers whether a conclusion is sufficiently supported.

Planning confidence answers whether a proposed plan is viable and sufficiently specified.

Verification confidence answers whether the verification judgment itself is reliable and complete.

These values must not be collapsed into one ambiguous number.

A system may legitimately have:

- insufficient basis for a conclusion;
- and high confidence that the basis is insufficient.

That is not contradiction.

That is calibrated uncertainty.

---

## 9. Observable Cognition

Important cognitive operations should leave inspectable artifacts.

Where appropriate, Sentinel should expose:

- evidence;
- standards;
- checks;
- dependencies;
- assumptions;
- findings;
- risks;
- coverage;
- confidence factors;
- conditions;
- high-level traces.

These records exist so behavior can be audited without exposing private chain-of-thought.

Sentinel should not require trust in invisible cognition when inspectable structure can provide evidence instead.

---

## 10. Verification Before Expansion

A new capability is not complete merely because it produces output.

Before expanding it, verify:

- its contracts;
- its invariants;
- its failure states;
- its integration boundary;
- its authority;
- its observability.

Expansion should occur from stable ground.

This reduces the cost of every later sprint.

---

## 11. Explainable Failure

Failure is part of intelligent systems.

Opaque failure is not acceptable engineering when meaningful diagnosis is possible.

Sentinel therefore adopts the principle:

> **A failure that explains itself is more valuable than a success that cannot justify itself.**

A trustworthy failure should, where possible, expose:

1. what failed;
2. where the failure occurred;
3. why the result cannot currently be trusted;
4. the confidence associated with that diagnosis;
5. what conditions are required for reconsideration.

Failure should become information.

Information should become understanding.

Understanding may inform remediation.

But diagnosis does not automatically grant repair authority.

---

## 12. Diagnosis Is Not Authority to Repair

Sentinel may identify defects in its own cognitive outputs.

Sentinel may identify missing evidence.

Sentinel may identify broken traceability.

Sentinel may specify remediation conditions.

None of these observations automatically authorize Sentinel to modify itself or silently rewrite an authoritative artifact.

The safe pattern is:

**Detect → Diagnose → Propose → Approve → Repair/Rerun → Re-verify**

Authority boundaries remain intact throughout the loop.

Self-observation and self-modification are different capabilities.

Sentinel engineering must preserve that distinction.

---

## 13. Human Authority Must Remain Explicit

Human approval is not an inconvenience to be engineered away.

Where consequences justify oversight, approval is part of the architecture.

Components should explicitly represent when human authorization is required rather than relying upon convention or assumption.

Autonomy should be granted intentionally, not acquired accidentally through coupling.

---

## 14. Test Invariants, Not Just Examples

Example-based tests prove that one scenario worked.

Invariant tests protect what must always remain true.

Sentinel testing should therefore protect structural guarantees such as:

- identifier uniqueness;
- valid references;
- status consistency;
- confidence bounds;
- authority boundaries;
- coverage integrity;
- traceability.

Regression tests should preserve meaningful failures as well as successful outcomes.

A system that only tests happy paths eventually learns to hide its weaknesses.

---

## 15. Preserve Valuable Failures

When a defect exposes an important architectural truth, preserve the lesson.

Do not erase useful failures simply because the immediate bug has been fixed.

Turn them into:

- regression tests;
- ADRs;
- foundation doctrine;
- architecture documentation;
- stronger contracts.

A bug can become permanent engineering knowledge.

That is how a system becomes more mature after failure rather than merely returning to operation.

---

## 16. Evidence Before Confidence

Confidence must follow evidence.

It must never substitute for evidence.

A high confidence score cannot repair:

- missing provenance;
- unsupported reasoning;
- incomplete verification;
- broken references;
- unknown assumptions.

Confidence describes the quality of a judgment under available conditions.

It does not manufacture the conditions required to justify that judgment.

---

## 17. Preserve the Authoritative Artifact

Each cognitive stage should have an authoritative structured result.

Downstream components may:

- inspect it;
- summarize it;
- explain it;
- verify it;
- reference it.

They may not silently mutate its meaning.

When revision is necessary, revision should produce a new inspectable state rather than rewriting history invisibly.

Traceability requires preservation.

---

## 18. Prefer Coherence Over Cleverness

Sentinel engineering does not optimize for impressive code.

It optimizes for coherent systems.

Choose the implementation that makes responsibility easiest to understand.

Choose explicit code when abstraction would hide authority.

Choose reusable abstractions when repetition obscures a stable concept.

Do not introduce complexity merely because the architecture could support it.

Every abstraction must earn its place.

---

## 19. Documentation Is Part of the Architecture

Architecture that exists only in the developers' heads does not reliably survive growth.

Important decisions should be preserved through:

- ADRs;
- sprint records;
- foundation doctrine;
- contracts;
- tests;
- architecture diagrams where useful.

Documentation is not paperwork performed after engineering.

It is how engineering intent survives future engineering.

---

## 20. Milestones Should Leave the Repository Stronger

A completed sprint should leave behind more than working code.

Where appropriate, it should leave:

- tested behavior;
- documented decisions;
- updated architectural understanding;
- regression protection;
- a clean commit boundary.

The repository should tell the story of how Sentinel became what it is.

---

# The Sentinel Engineering Creed

We build foundations before complexity.

We separate responsibilities before combining capabilities.

We define contracts before trusting implementations.

We preserve evidence before assigning confidence.

We distinguish cognition from communication.

We distinguish diagnosis from authority.

We verify before we certify.

We make uncertainty visible.

We make failure explainable.

We preserve lessons discovered through failure.

We do not confuse capability with trustworthiness.

We do not hide complexity behind language.

We do not allow convenience to silently redefine authority.

We build systems that can show why they deserve trust.

And when they do not deserve trust,

**they must be able to tell us why.**

---

**Sentinel Engineering**

*Structure creates clarity.  
Clarity creates trust.  
Trust must be earned.*
