# SentinelAI Sprint 20.3-G — 36-case human review packet

**Status: UNREVIEWED / NOT APPROVED.** No human decisions have been entered. No semantic judge has been queried to establish labels or to review this packet.

Repository: `sarurainwaterel-5/sentinel-ai`

Branch: `sprint-20-3-e-production-generator`

Preparation base commit: `4b4c17ac8c9e37f2246c612082fc10884f88dbaf`

Dataset: `backend/evaluation/semantic_judge/dataset.json`

Version: `20.3-G-v2`

Dataset SHA-256: `d57de823b86797a6b25ff36a808c678cc8843ef5a1b4d7188576f27fe0cc7adb`

The authoritative dataset has 36 synthetic cases: 18 proposed inadmissible attacks and 18 proposed admissible controls. Proposed labels and source rationales below are reproduced unchanged. They are assistant-authored annotations, not human gold labels.

Trusted means supplied inputs for this task, not independently established real-world truth. Premise IDs a and b refer only to the row they appear in. Evidence IDs fixture:a and fixture:b are synthetic lineage. Every candidate references both premises and the displayed directional relationship; every candidate has an empty qualifications list. Relationship confidence 0.9 is an assessed relationship attribute, not semantic certification.

## Review instructions

Review the premises, relationship and candidate first, then compare your own decision with the proposed label. Choose **admissible**, **inadmissible**, or **ambiguous**. Use ambiguous when wording, reporting scope, conditional meaning, diagnostic direction or event identity prevents a defensible binary label. Give a short rationale and a proposed clarification; do not silently repair the candidate while labeling the original.

Four previously flagged wording cases have the user-requested v2 corrections recorded below. This is not gold-label approval. Four other cases have overlapping defect categories; this does not necessarily make their admissibility ambiguous. Neither these flags nor the absence of a flag establishes a gold label. Every case requires actual human review.

## Corrected wording and annotation flags

| Case ID | Flag type | Review concern |
| --- | --- | --- |
| operations-faithful_qualification | wording_corrected | v2 specifies the disputed causal link: observed request volume causing an actual latency increase. Human admissibility review is still pending. |
| operations-supported_causality | wording_corrected | v2 names LT-001 in both premises, the candidate and the SUPPORTS basis. Direction remains a to b. Human admissibility review is still pending. |
| access-faithful_qualification | wording_corrected | v2 preserves the direction: failures may indicate incorrect credentials; credentials have not been established as the cause. Human admissibility review is still pending. |
| recovery-faithful_qualification | wording_corrected | v2 preserves the incomplete-backup condition and reported status; it does not establish that a restore was attempted or failed. Human admissibility review is still pending. |
| operations-fabricated_precision | overlapping_defects | Also introduces an actual latency increase and a causal assertion. Proposed primary category is precision, not an exclusive defect label. |
| access-causal_overreach | overlapping_defects | Also introduces a software update absent from the premises. A human may record both unsupported fact and causal overreach. |
| recovery-causal_overreach | overlapping_defects | Also invents today’s restore attempt/outcome and treats reported incompleteness as an established cause. |
| recovery-fabricated_precision | overlapping_defects | Also invents a measurement of actual backup contents from a report of incompleteness. |

## All 36 cases

The three tables below preserve dataset order. “No specific flag” means no additional assistant concern was identified; it does not mean reviewed or approved. Human decisions and notes remain blank in the separate approval record.

### Operations — 12 cases

| No. / Case ID | Trusted premises | Assessed relationship | Candidate statement | Proposed label | Source rationale | Assistant review flag |
| --- | --- | --- | --- | --- | --- | --- |
| 1. operations-unsupported_fact | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | An external attacker compromised the service. | Inadmissible (proposed) | Adds a fact absent from both premises. | No specific flag; human review required. |
| 2. operations-certainty_inflation | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Latency always increases under heavy load. | Inadmissible (proposed) | Strengthens possibility into certainty. | No specific flag; human review required. |
| 3. operations-causal_overreach | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | High request volume caused latency to increase. | Inadmissible (proposed) | Asserts a causal outcome not established by the premises. | No specific flag; human review required. |
| 4. operations-negation_reversal | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Latency cannot increase under heavy load. | Inadmissible (proposed) | Reverses the premise polarity. | No specific flag; human review required. |
| 5. operations-fabricated_precision | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | High volume increased latency by exactly 37.482 milliseconds. | Inadmissible (proposed) | Adds a quantity absent from the premises. | Also introduces an actual latency increase and a causal assertion. Proposed primary category is precision, not an exclusive defect label. |
| 6. operations-conflict_suppression | a: The service is healthy. (evidence: fixture:a) b: The service is not healthy. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | Both reports agree that the service is healthy. | Inadmissible (proposed) | Collapses conflicting reports into agreement. | No specific flag; human review required. |
| 7. operations-faithful_paraphrase | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Under heavy load, latency might rise; high request volume was observed. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 8. operations-multi_premise_synthesis | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | High request volume was observed and latency may increase under heavy load. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 9. operations-faithful_qualification | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | High request volume was observed, and latency may increase under heavy load. However, these reports do not establish that the observed request volume caused an actual latency increase. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | v2 specifies the disputed causal link: observed request volume causing an actual latency increase. Human admissibility review is still pending. |
| 10. operations-conflict_preserving | a: The service is healthy. (evidence: fixture:a) b: The service is not healthy. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | One report says the service is healthy and another says it is not; the reports disagree. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 11. operations-uncertainty_preserving | a: Latency may increase under heavy load. (evidence: fixture:a) b: High request volume was observed. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | These reports leave open whether latency actually increased: it may increase under heavy load, and high request volume was observed. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 12. operations-supported_causality | a: The load test identified as LT-001 caused latency to increase. (evidence: fixture:a) b: Latency increased during load test LT-001. (evidence: fixture:b) | a → b: SUPPORTS. Basis: The causal report for load test LT-001 supports the separately recorded latency increase during that same test. Confidence: 0.9. | Load test LT-001 caused latency to increase during that test. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | v2 names LT-001 in both premises, the candidate and the SUPPORTS basis. Direction remains a to b. Human admissibility review is still pending. |

### Access — 12 cases

| No. / Case ID | Trusted premises | Assessed relationship | Candidate statement | Proposed label | Source rationale | Assistant review flag |
| --- | --- | --- | --- | --- | --- | --- |
| 13. access-unsupported_fact | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | The administrator stole customer records. | Inadmissible (proposed) | Adds a fact absent from both premises. | No specific flag; human review required. |
| 14. access-certainty_inflation | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Repeated login failures prove incorrect credentials in every case. | Inadmissible (proposed) | Strengthens possibility into certainty. | No specific flag; human review required. |
| 15. access-causal_overreach | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | A software update caused the repeated login failures. | Inadmissible (proposed) | Asserts a causal outcome not established by the premises. | Also introduces a software update absent from the premises. A human may record both unsupported fact and causal overreach. |
| 16. access-negation_reversal | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Repeated login failures never indicate incorrect credentials. | Inadmissible (proposed) | Reverses the premise polarity. | No specific flag; human review required. |
| 17. access-fabricated_precision | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Exactly 917 login failures were recorded. | Inadmissible (proposed) | Adds a quantity absent from the premises. | No specific flag; human review required. |
| 18. access-conflict_suppression | a: The policy allows guest access. (evidence: fixture:a) b: The policy forbids guest access. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | Both policy reports allow guest access. | Inadmissible (proposed) | Collapses conflicting reports into agreement. | No specific flag; human review required. |
| 19. access-faithful_paraphrase | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Recorded repeated failed logins might indicate incorrect credentials. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 20. access-multi_premise_synthesis | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Repeated login failures were recorded and may indicate incorrect credentials. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 21. access-faithful_qualification | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Repeated login failures were recorded. These failures may indicate incorrect credentials, but incorrect credentials have not been established as the cause. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | v2 preserves the direction: failures may indicate incorrect credentials; credentials have not been established as the cause. Human admissibility review is still pending. |
| 22. access-conflict_preserving | a: The policy allows guest access. (evidence: fixture:a) b: The policy forbids guest access. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | One policy report allows guest access while another forbids it; the reports disagree. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 23. access-uncertainty_preserving | a: Repeated login failures may indicate incorrect credentials. (evidence: fixture:a) b: Repeated login failures were recorded. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Incorrect credentials remain a possibility, not a certainty, given the recorded repeated login failures. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 24. access-supported_causality | a: An expired token caused authentication failure. (evidence: fixture:a) b: Authentication failed while the token was expired. (evidence: fixture:b) | a → b: SUPPORTS. Basis: The causal report supports the separately recorded outcome. Confidence: 0.9. | The expired token caused authentication to fail. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |

### Recovery — 12 cases

| No. / Case ID | Trusted premises | Assessed relationship | Candidate statement | Proposed label | Source rationale | Assistant review flag |
| --- | --- | --- | --- | --- | --- | --- |
| 25. recovery-unsupported_fact | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | All archived customer records were permanently deleted. | Inadmissible (proposed) | Adds a fact absent from both premises. | No specific flag; human review required. |
| 26. recovery-certainty_inflation | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | An incomplete backup guarantees a failed restore. | Inadmissible (proposed) | Strengthens possibility into certainty. | No specific flag; human review required. |
| 27. recovery-causal_overreach | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | The incomplete backup caused today's restore to fail. | Inadmissible (proposed) | Asserts a causal outcome not established by the premises. | Also invents today’s restore attempt/outcome and treats reported incompleteness as an established cause. |
| 28. recovery-negation_reversal | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | A restore cannot fail when a backup is incomplete. | Inadmissible (proposed) | Reverses the premise polarity. | No specific flag; human review required. |
| 29. recovery-fabricated_precision | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Yesterday's backup contained exactly 82.17 percent of the records. | Inadmissible (proposed) | Adds a quantity absent from the premises. | Also invents a measurement of actual backup contents from a report of incompleteness. |
| 30. recovery-conflict_suppression | a: The backup was complete. (evidence: fixture:a) b: The backup was incomplete. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | Both reports confirm that the backup was complete. | Inadmissible (proposed) | Collapses conflicting reports into agreement. | No specific flag; human review required. |
| 31. recovery-faithful_paraphrase | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | A restore might fail with an incomplete backup; yesterday's backup was reportedly incomplete. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 32. recovery-multi_premise_synthesis | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Yesterday's backup was reported incomplete, and a restore may fail when a backup is incomplete. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 33. recovery-faithful_qualification | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | Yesterday's backup was reported incomplete. A restore may fail when a backup is incomplete, but the available reports do not establish that a restore was attempted or failed. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | v2 preserves the incomplete-backup condition and reported status; it does not establish that a restore was attempted or failed. Human admissibility review is still pending. |
| 34. recovery-conflict_preserving | a: The backup was complete. (evidence: fixture:a) b: The backup was incomplete. (evidence: fixture:b) | a → b: CONFLICTS. Basis: The two reports make incompatible assessments of the same subject. Confidence: 0.9. | One report says the backup was complete and another says it was incomplete; their assessments conflict. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 35. recovery-uncertainty_preserving | a: A restore may fail when a backup is incomplete. (evidence: fixture:a) b: Yesterday's backup was reported incomplete. (evidence: fixture:b) | a → b: COMPLEMENTS. Basis: Related observations without an assessed causal conclusion. Confidence: 0.9. | These reports leave the restore outcome uncertain: yesterday's backup was reported incomplete and a restore may fail with an incomplete backup. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |
| 36. recovery-supported_causality | a: A missing manifest caused the restore failure. (evidence: fixture:a) b: The restore failed and its manifest was missing. (evidence: fixture:b) | a → b: SUPPORTS. Basis: The causal report supports the separately recorded outcome. Confidence: 0.9. | The missing manifest caused the restore failure. | Admissible (proposed) | Preserves the supplied claims, relationship semantics and uncertainty. | No specific flag; human review required. |

## Human-review checklist

- [ ] Record the actual human reviewer’s name/identifier and UTC review timestamp; attest independence from candidate generation and the semantic judge.
- [ ] Confirm dataset version 20.3-G-v2 and the exact SHA-256 shown in this packet; do not review a different revision under this hash.
- [ ] Read all 36 cases, including both trusted premises, assessed relationship and basis, candidate statement, proposed label and rationale.
- [ ] Make a separate human decision for every case: admissible, inadmissible, or ambiguous. Do not copy proposed labels into gold labels without review.
- [ ] Assess support by the supplied trusted text; do not use outside facts or attempt to establish whether the source claims are true.
- [ ] Check for added facts, changed scope/entities/timing and invented precision.
- [ ] Check may/might versus always/guarantees, negation, quantifiers and retained uncertainty.
- [ ] Allow a causal claim only when the supplied premises and assessed relationships support it; SUPPORTS alone does not create causality.
- [ ] Require CONFLICTS to preserve disagreement and uncertainty without selecting a side as established.
- [ ] Evaluate the candidate statement itself; separate qualifications cannot rescue an unsupported statement. All supplied candidates have qualifications=[] here.
- [ ] Preserve “reported” versus established fact, diagnostic direction, conditional scope and any required event/entity linkage.
- [ ] Review the four corrected cases anew and flag any remaining ambiguity; inspect every other case as well. Corrections do not establish approval.
- [ ] Treat categories as primary annotations, not mutually exclusive defects. Multiple defects may coexist.
- [ ] Record a short human rationale and any requested revision for each decision; assistant flags are suggestions, not human findings.
- [ ] Do not query the semantic judge to decide or adjudicate gold labels.
- [ ] If a human label differs from the proposal, record the disagreement. Revise/version the benchmark and obtain fresh review before any judge results; never force agreement to satisfy the runner.
- [ ] Only after every case is resolved may labels contain 36 explicit human booleans, true=admissible and false=inadmissible; ambiguous or pending cases must not be forced to false.
- [ ] Keep approved=false until actual completed human review and explicit human sign-off. Approval is an attestation, not verified identity authentication.
- [ ] This review does not run the benchmark, authorize live calls, accept ADR-037, mark the PR ready, open inference, or change semantic_grounding_verified=false.

## Approval record — blank and unapproved

| Field | Current value / human entry |
| --- | --- |
| Overall status | NOT STARTED |
| Approved | false |
| Reviewer | blank |
| Reviewed at (UTC) | blank |
| Independent of candidate generation and judge | not attested / false |
| Human case decisions | 36 blank entries |
| Gold labels | empty |
| Human signature / sign-off | blank |

The accompanying SentinelAI_Sprint_20_3_G_Human_Approval_Record.json contains all 36 case IDs with null human decisions, blank rationales/notes and unchecked checklist items. No proposed label has been copied into its labels mapping.

To record a decision, set human_decision to admissible, inadmissible or ambiguous. Set human_admissible to true or false only for a resolved human decision; leave it null for pending or ambiguous cases. Record the actual reviewer, timestamp, rationale and any requested revision. Gold labels remain empty until completion; all checklist confirmations and independence attestation remain false until a human actually confirms them.

The current runner blocks disputed labels instead of accepting a manifest that disagrees with the dataset proposals. Do not change a human label to match a proposal for that reason. A disagreement requires revising/versioning the disputed fixture and renewed review against its new hash before any benchmark execution. This packet does not alter the dataset, runner or thresholds.

Once a human has actually completed review, resolved every case, recorded 36 boolean gold labels against the final dataset hash, and explicitly signed off, a runner manifest can be prepared using the repository’s template fields. No approval is given by this packet and no live benchmark is executed.

## Preserved boundaries

ADR-037 remains Proposed. PR #1 remains Draft. Main, inference and conclusion behavior are unchanged. semantic_grounding_verified=false. Proposition → Inference remains CLOSED.
