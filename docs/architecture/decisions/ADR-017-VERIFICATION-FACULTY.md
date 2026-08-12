# ADR-017 — Verification Faculty

**Status:** Accepted  
**Date:** 2026-08-11  
**Decision:** Establish Verification as an independent cognitive faculty within SentinelAI.

## Context

SentinelAI already possessed Reasoning and Planning faculties capable of producing structured conclusions and proposed courses of action.

Those capabilities created a new architectural requirement:

A result must not be considered trustworthy merely because Sentinel can produce it.

Sentinel requires an independent faculty capable of inspecting cognitive artifacts without silently changing them, determining whether their claims are sufficiently supported, measuring verification coverage, identifying structural or evidentiary failures, and communicating the conditions required for resolution.

Verification therefore cannot be reduced to formatting, exception handling, confidence scoring, or another stage inside Reasoning or Planning.

It requires its own authority boundary.

## Decision

SentinelAI will implement Verification as an independent cognitive faculty.

The Verification Faculty:

- receives an authoritative subject for inspection;
- applies explicit verification standards and checks;
- records findings without modifying the subject;
- measures verification coverage;
- calculates verification confidence independently from reasoning or planning confidence;
- produces explicit verification status;
- exposes unresolved conditions and remediation requirements;
- preserves inspectable verification traces;
- communicates results through a formatter that may explain, but not alter, the authoritative verification result.

The Verification Faculty does not execute repairs.

Detection and remediation remain separate responsibilities.

## Architectural Principle

Verification answers a different question from Reasoning and Planning.

Reasoning asks:

> What conclusion is supported?

Planning asks:

> What should be done?

Verification asks:

> Does this result deserve trust, and on what basis?

These authorities must remain separate.

## Verification Confidence

Verification confidence represents confidence in the quality and completeness of the verification judgment.

It does not represent confidence in the verified subject.

Therefore a result may legitimately contain:

- low confidence in an underlying conclusion;
- an `insufficient_basis` verification status;
- and simultaneously high verification confidence.

This distinction is intentional.

Sentinel must be capable of being highly confident that available evidence is insufficient.

## Structural Guarantees

Verification results enforce structural integrity across:

- standards;
- checks;
- findings;
- coverage;
- status;
- confidence;
- traceability relationships.

Identifiers must remain unique.

Checks must reference known standards.

Findings must reference known checks.

Coverage declarations must correspond to actual checks performed.

A `verified` result cannot contain failed checks or blocking findings.

A `requires_revision` result must contain evidence justifying revision.

These invariants prevent contradictory verification records from becoming authoritative.

## Communication Boundary

The Verification Formatter is subordinate to the authoritative `VerificationResult`.

It may explain:

- status;
- findings;
- coverage;
- confidence;
- conditions;
- implications.

It may not alter them.

Communication is interpretation of authority, not replacement of authority.

## Failure Diagnosis

Verification failures must be inspectable.

Where possible, Sentinel should identify:

1. what failed;
2. where the failure occurred;
3. why the result cannot currently be trusted;
4. how confident Verification is in that diagnosis;
5. what conditions must become true before the result can be reconsidered.

This creates diagnostic self-observation without granting autonomous self-modification authority.

## Human Authority Boundary

Verification may diagnose failure and specify remediation conditions.

Verification may not silently repair cognitive artifacts or modify Sentinel's governing architecture.

Future repair loops must preserve explicit authority boundaries and human approval where required.

The intended pattern is:

Detect → Diagnose → Propose Remediation → Human Approval → Repair/Rerun → Re-verify

## Mission 001

Sprint 17's first end-to-end Verification mission produced:

- Status: `insufficient_basis`
- Verification confidence: `0.974` (`high`)
- Requested categories: 4
- Completed categories: 4
- Checks: 27
- Passed: 14
- Failed: 1
- Unverifiable: 2
- Not applicable: 10

Blocking findings included:

- Reasoning basis unavailable
- Strategy lacks reasoning support
- Strategy-to-conclusion trace is broken

Sentinel then exposed explicit remediation conditions for restoring reasoning and strategy traceability.

The mission demonstrated that Verification could distinguish confidence in its diagnosis from confidence in the underlying cognitive artifact.

Mission 001 is preserved as the canonical `INSUFFICIENT_BASIS` regression scenario.

## Consequences

### Positive

Sentinel gains:

- independent cognitive quality control;
- inspectable failure diagnosis;
- explicit verification coverage;
- domain-specific verification confidence;
- stronger provenance enforcement;
- safe failure states;
- machine-readable remediation conditions;
- a foundation for supervised cognitive repair loops.

### Costs

The architecture introduces additional:

- models;
- contracts;
- specialist components;
- orchestration;
- tests;
- cognitive latency.

These costs are accepted because Verification is an authority boundary rather than a convenience feature.

## Engineering Principle

> A failure that explains itself is more valuable than a success that cannot justify itself.

This principle becomes part of Sentinel engineering culture.

## Outcome

Accepted.

Verification becomes a first-class SentinelAI cognitive faculty alongside Reasoning and Planning.
