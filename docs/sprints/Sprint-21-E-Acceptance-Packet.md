# Sprint 21-E — Acceptance packet

**Packet prepared; production release blocked.** This milestone approval authorized
preparation only, not live semantic benchmark execution or release. Implementation
baseline: `837b94f61ed6ff82f9e158e008f7c94fec4ae906` on
`codex/sprint-21-b-contracts`. Verified Sprint 20.3 checkpoint:
`213fb04125b189adc2fc770f157e4e454b559644`.

## Contents and use

- [Version-bound manifest](../../backend/evaluation/governed_answers/release_manifest.json):
  implementation commit and SHA-256 bindings for answer contracts, provenance,
  coordinator/renderer, API/UI, existing semantic gates, protected governance
  artifacts and proposed review inputs. It records blockers and previous offline
  results; it contains no approval or empirical result.
- [Proposed answer cases](../../backend/evaluation/governed_answers/answer_cases.proposed.json):
  13 synthetic questions, source passages, premises, relationships and candidates.
  Six faithful controls cover paraphrase, multi-premise synthesis, qualifications,
  preserved conflict, uncertainty and explicit causality. Six attack cases cover
  unsupported facts, certainty inflation, causal overreach, negation reversal,
  invented precision and suppressed conflict. A thirteenth case deliberately
  pairs a premise-admissible statement with an unanswered question.
- [Proposed supplemental criteria](../../backend/evaluation/governed_answers/answer_acceptance.proposed.json):
  zero unsupported published claims, wrong/missing citations, suppressed known
  conflicts, false-ready states or out-of-scope disclosures; reviewed positive
  controls, all fail-closed cases, relevance and integration acceptance required.
  These criteria are assistant proposals pending human review, not accepted policy
  or passing measurements. Original 20.3-G policy is copied for reference only;
  the authoritative existing policy file remains unchanged.
- [Blank answer review template](../../backend/evaluation/governed_answers/answer_review.template.json):
  review each question and both sources; record statement admissibility, question
  relevance, conflict/uncertainty preservation, citation completeness, rationale
  and requested revisions. Approval fields and all case decisions remain blank.
  Approval of milestone work is not approval of labels or production release.
- [Offline integrity inspector](../../backend/evaluation/governed_answers/inspect_packet.py):
  stdlib-only hash/disabled-invariant inspection; no application imports, providers,
  credentials or network. A successful exit means packet integrity only, with
  `release_authorized=false`. Runtime does not consume this draft manifest.

Run the integrity inspector from backend with
`python -m evaluation.governed_answers.inspect_packet`. This is **not** the semantic
benchmark runner. Code/policy/review-input changes invalidate hashes and require a
fresh packet/review. Hashes demonstrate content consistency, not authenticated
reviewer identity, source truth or semantic entailment.

## Evidence inventory

| Gate | Available evidence | Status |
|---|---|---|
| Contract/provenance and fail-closed enforcement | 21-B/C scripted tests; preserved false grounding and closed inference | Offline passes recorded |
| Disabled API/readiness, UI and citations | 21-D: 296 reasoning/route tests, 83 frontend tests, 30 repeated affected tests; lint/build; isolated browser HTTP 503 and fixture checks | Offline passes recorded |
| Packet binding and proposal integrity | New 21-E stdlib inspection and offline tests | Integrity only; does not unlock release |
| Human gold labels for original 20.3-G dataset | Named approved record, matching v2 dataset hash, complete 36 labels | Approval attestation exists |
| Actual independent judge decisions | Saved preflight: not_executed, zero trials, null metrics; no committed empirical report | Missing |
| Final Sprint 20.3-G acceptance | No passing empirical report/final acceptance available | Pending |
| Answer-case labels and supplemental policy | 13 assistant-authored proposals, unapproved review template | Pending human review |
| Query relevance | Existing semantic judge does not receive the question | Not established for production |
| Authenticated retrieval/catalog/race composition | Current answer route is intentionally disabled before retrieval | Not implemented for answering |
| Production generation/assessment wiring and budgets | Offline injected coordinator only; no production factory | Not implemented |
| Production enablement/answer presentation acceptance | Readiness and public answer contracts remain literally disabled | Not authorized |

The 21-D counts are retained historical evidence, not newly rerun 21-E measurements.
All scripted judge decisions are explicitly non-empirical. The new packet does not
execute any answer-quality benchmark or claim actual semantic accuracy.

## Exact 20.3-G dependencies

1. Retain the existing approved named human record and matching dataset hash.
   Saved preflight/README wording predates that approval; its human-review-missing
   blocker is stale. The existing runner's default `human_review.json` is absent;
   a later authorized run must explicitly select the approved named record.
2. Obtain separate authorization for secure, dedicated assessor configuration
   and live execution. No credentials/model were inspected or introduced here.
   Preserve the existing independent client, explicit model, 30-second timeout,
   zero SDK retries, no generation-client or ambient key fallback, and no gold
   labels/rationales in judge requests.
3. Perform all 36 cases three times with the existing frozen policy and seed.
   Retain a complete actual-API report binding dataset, policy, review, prompt,
   verdict schema, runner, implementation commit and model/configuration.
4. Meet every original threshold: zero false accepts, false reject rate ≤10%,
   accuracy ≥95%, decision stability 100%, zero operational errors, complete
   coverage and accepted controls in every positive category. Error-on-rejection
   is an operational error, not a correct semantic classification.
5. Review failures and conduct final human acceptance. Disputes or changes must
   follow existing version/holdout/review governance before outcomes are used;
   never weaken thresholds or retroactively tune acceptance.

Passing G does not automatically accept ADR-037, set grounding to true, open
Proposition → Inference or authorize deployment. Those boundaries remain unchanged.

## Additional answer-release dependencies

- Review the proposed cases/criteria before evaluation; resolve ambiguous cases
  without looking at outcomes or forcing agreement with proposed labels.
- Establish question relevance, whole-context relationship/conflict coverage and
  complete citations for the explicitly bounded answer scope. The existing judge
  is an admissibility gate, not a question-relevance assessor or source-truth judge.
- Separately approve and implement authenticated retrieval/catalog eligibility,
  archive/update-race handling, independent provider composition, operational
  budgets and version-bound release-gate consumption. No enable flag can be a
  substitute for acceptance evidence.
- Obtain explicit human acceptance of attributed answer presentation and its
  scope/limits. Source reports and scripted previews cannot satisfy that gate.
- Keep new behavior disabled until every release gate passes. Deployment remains
  a separate action and is not included in this milestone.

## Handoff decision

The acceptance **packet** can be reviewed now. Sprint 21 production acceptance
cannot be declared complete on present evidence. The safe next action is review
of the answer fixtures and criteria, followed by separately scoped approval for
remaining integration work and, when ready, the existing 20.3-G evaluation.
No automatic next milestone, benchmark, credential change, enablement or deployment
is triggered by packet preparation.
