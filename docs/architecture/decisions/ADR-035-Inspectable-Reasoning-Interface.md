# ADR-035 — Inspectable Reasoning Interface

## Status

Accepted

## Date

2026-08-23

## Context

SentinelAI possesses a structured reasoning architecture capable of
retrieving evidence, producing bounded inferences, assessing confidence,
and evaluating constitutional coherence.

A conventional AI interface could flatten those outputs into a single
natural-language answer.

That design is rejected.

A single answer obscures distinctions that are architecturally and
epistemically important.

For example:

- evidentiary confidence is not constitutional coherence,
- uncertainty is not a limitation,
- a limitation is not missing information,
- retrieved evidence is not itself a conclusion,
- constitutional admissibility is not execution authority,
- and a recommendation is not permission to act.

If these concepts are collapsed during presentation, Sentinel may
internally preserve correct cognitive boundaries while presenting those
boundaries inaccurately to the operator.

The interface is therefore part of the cognitive safety architecture.

---

## Decision

SentinelAI SHALL expose structured reasoning through an inspectable
cognitive interface.

The accepted high-level sequence is:

```text
Reasoning Mission
      ↓
Retrieval
      ↓
Evidence Analysis
      ↓
Inference
      ↓
Confidence Assessment
      ↓
Supported Judgment
      ↓
Constitutional Coherence
      ↓
Inspectable Cognitive Presentation

Presentation SHALL preserve the semantic boundaries produced by the
underlying cognitive faculties.

The interface SHALL NOT flatten those boundaries into a single
undifferentiated AI response.

Decision Principles
1. Judgment Is Not Evidence

A conclusion represents a bounded inference from available evidence.

Evidence remains independently inspectable.

The interface SHALL preserve enough provenance for an operator to
examine the material supporting the judgment.

A rendered conclusion SHALL NOT become its own evidence merely because
it appears prominently in the interface.

2. Confidence Is an Independent Cognitive Judgment

Confidence represents the strength of evidentiary support for the
current conclusion.

Confidence SHALL remain independently represented.

The interface SHALL NOT infer confidence from:

constitutional coherence,
visual prominence,
source count alone,
retrieval relevance alone,
or the existence of a conclusion.

Confidence may be low while constitutional coherence remains high.

3. Constitutional Coherence Is Not Confidence

Constitutional coherence evaluates compatibility with SentinelAI's
governing principles.

It does not evaluate evidentiary strength.

The following combination is valid:

confidence = low
constitutional_coherence = high

The following combination is also conceptually valid:

confidence = high
constitutional_coherence = low

The interface SHALL preserve these judgments independently.

4. Limitations, Uncertainty, and Missing Information Are Distinct

SentinelAI SHALL preserve three separate uncertainty concepts.

Limitations
    ↓
Constraints on the current judgment.


Uncertainty
    ↓
Reasons confidence remains bounded.


Missing Information
    ↓
Absent evidence that would materially improve the judgment.

These concepts may refer to related evidence conditions.

They SHALL NOT be treated as semantic aliases.

The reasoning architecture SHOULD derive each according to its own
meaning rather than copying one list into multiple output fields.

5. Evidence Provenance Must Be Inspectable

Reasoning evidence SHALL remain traceable to its source representation.

The interface SHOULD expose useful provenance including, where
available:

document identity,
module,
topic,
chunk position,
retrieval relevance,
evidence text,
and descriptive metadata.

The interface MAY summarize or collapse evidence for readability.

It SHALL NOT remove the operator's ability to inspect the underlying
source representation when that representation is available.

6. Reasoning Trace Is Operational Observability

SentinelAI MAY expose a user-safe reasoning trace representing explicit
stages produced by its reasoning architecture.

Such a trace is intended to communicate system behavior and cognitive
workflow.

It SHALL NOT claim to expose hidden model chain-of-thought.

Inspectable reasoning architecture and private model cognition remain
distinct concepts.

7. Presentation Has No Cognitive Authority

Frontend components may:

submit structured reasoning missions,
display results,
organize cognitive information,
expose provenance,
visualize confidence,
visualize constitutional coherence,
and progressively disclose detail.

Frontend components SHALL NOT:

perform authoritative inference,
manufacture missing evidence,
recalculate confidence,
alter constitutional judgments,
repair unsupported conclusions,
or convert recommendations into execution authority.

The frontend presents cognition.

It does not become the source of cognition.

8. Domain Scope Must Remain Explicit

Reasoning missions MAY be scoped to an active operational Domain.

Domain context SHALL be passed into the reasoning request rather than
implemented as frontend-only filtering of already-produced cognition.

A cross-domain mission SHALL remain possible without manufacturing an
artificial Domain constraint.

9. Responsive Design Must Preserve Cognitive Hierarchy

Responsive presentation SHALL preserve the semantic order of cognition.

At reduced viewport widths, layout may change from horizontal to
vertical.

The meaning and relative hierarchy of:

judgment,
confidence,
governance,
evidence,
reasoning trace,
uncertainty,
and next action

SHALL remain intact.

Responsive design is therefore a reflow of cognition, not a reduction
of cognition.

Accepted Presentation Model

The canonical Reason cockpit model is:

MISSION
   ↓
JUDGMENT
   ↓
CONFIDENCE ←→ GOVERNANCE
   ↓
EVIDENCE
   ↓
REASONING TRACE
   ↓
UNCERTAINTY
   ↓
NEXT ACTION

This model establishes presentation hierarchy without granting the
interface additional cognitive authority.

Consequences
Positive

The decision provides:

inspectable reasoning,
explicit provenance,
clearer uncertainty semantics,
separation of confidence and governance,
improved operator trust calibration,
reusable cognitive presentation patterns,
stronger regression contracts,
and a foundation for future Sentinel cognitive workspaces.
Costs

The decision requires:

more structured frontend components,
stronger backend response contracts,
explicit semantic testing,
careful handling of empty and insufficient-evidence states,
and additional interface complexity compared with a conventional chat
response.

These costs are accepted.

The complexity already exists in Sentinel's cognition.

The interface should expose that complexity coherently rather than hide
it inaccurately.

Rejected Alternatives
Single Natural-Language Answer

Rejected because it hides evidence structure, uncertainty, provenance,
and governance distinctions.

Frontend-Derived Confidence

Rejected because presentation code must not acquire confidence authority.

Combined Confidence and Governance Score

Rejected because evidentiary support and constitutional coherence answer
different questions.

Shared Limitations / Missing-Information List

Rejected because current judgment constraints and absent evidence have
different semantics.

Hidden Evidence

Rejected because conclusions without inspectable provenance weaken
operator verification.

Architectural Invariant

The following invariant governs SentinelAI reasoning interfaces:

Supported judgment, evidence provenance, evidentiary confidence,
uncertainty, limitations, missing information, alternatives, and
constitutional coherence are independently meaningful cognitive
concepts and SHALL remain independently inspectable.

Relationship to Existing Architecture

This decision extends SentinelAI's existing principles of bounded
cognition, observable cognition, structured intelligence contracts, and
constitutional separation of authority.

It does not replace the Reasoning Engine, Confidence Engine, retrieval
architecture, or constitutional reasoning architecture.

It defines how their outputs may be responsibly exposed to a human
operator.

Future Application

The inspectable-cognition pattern established here SHOULD inform future
SentinelAI cognitive workspaces where equivalent distinctions exist.

Reuse SHOULD occur at the architectural-principle level.

Future faculties SHALL NOT be forced into Reason-specific semantics when
their cognitive contracts differ.

Closing Principle

The interface may clarify cognition.

It may not collapse, exaggerate, or silently rewrite cognition.


