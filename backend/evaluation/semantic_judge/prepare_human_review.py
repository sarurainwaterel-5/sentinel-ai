from pathlib import Path
import hashlib,json,subprocess

repo=Path(__file__).resolve().parents[3]
root=Path(__file__).resolve().parent
source=repo/'backend/evaluation/semantic_judge/dataset.json'
data=json.loads(source.read_text()); cases=data['cases']
sha=hashlib.sha256(source.read_bytes()).hexdigest()
checkpoint=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
flags={
 'operations-faithful_qualification': dict(kind='wording_corrected',text='v2 specifies the disputed causal link: observed request volume causing an actual latency increase. Human admissibility review is still pending.'),
 'operations-supported_causality': dict(kind='wording_corrected',text='v2 names LT-001 in both premises, the candidate and the SUPPORTS basis. Direction remains a to b. Human admissibility review is still pending.'),
 'access-faithful_qualification': dict(kind='wording_corrected',text='v2 preserves the direction: failures may indicate incorrect credentials; credentials have not been established as the cause. Human admissibility review is still pending.'),
 'recovery-faithful_qualification': dict(kind='wording_corrected',text='v2 preserves the incomplete-backup condition and reported status; it does not establish that a restore was attempted or failed. Human admissibility review is still pending.'),
 'operations-fabricated_precision': dict(kind='overlapping_defects',text='Also introduces an actual latency increase and a causal assertion. Proposed primary category is precision, not an exclusive defect label.'),
 'access-causal_overreach': dict(kind='overlapping_defects',text='Also introduces a software update absent from the premises. A human may record both unsupported fact and causal overreach.'),
 'recovery-causal_overreach': dict(kind='overlapping_defects',text='Also invents today’s restore attempt/outcome and treats reported incompleteness as an established cause.'),
 'recovery-fabricated_precision': dict(kind='overlapping_defects',text='Also invents a measurement of actual backup contents from a report of incompleteness.'),
}
checklist=[
 ('identity_and_independence','Record the actual human reviewer’s name/identifier and UTC review timestamp; attest independence from candidate generation and the semantic judge.'),
 ('source_hash_confirmed','Confirm dataset version 20.3-G-v2 and the exact SHA-256 shown in this packet; do not review a different revision under this hash.'),
 ('all_cases_read','Read all 36 cases, including both trusted premises, assessed relationship and basis, candidate statement, proposed label and rationale.'),
 ('own_labels_recorded','Make a separate human decision for every case: admissible, inadmissible, or ambiguous. Do not copy proposed labels into gold labels without review.'),
 ('support_without_source_truth','Assess support by the supplied trusted text; do not use outside facts or attempt to establish whether the source claims are true.'),
 ('no_unsupported_additions','Check for added facts, changed scope/entities/timing and invented precision.'),
 ('modality_and_negation_preserved','Check may/might versus always/guarantees, negation, quantifiers and retained uncertainty.'),
 ('causality_supported','Allow a causal claim only when the supplied premises and assessed relationships support it; SUPPORTS alone does not create causality.'),
 ('conflict_preserved','Require CONFLICTS to preserve disagreement and uncertainty without selecting a side as established.'),
 ('qualification_stands_alone','Evaluate the candidate statement itself; separate qualifications cannot rescue an unsupported statement. All supplied candidates have qualifications=[] here.'),
 ('reference_reporting_preserved','Preserve “reported” versus established fact, diagnostic direction, conditional scope and any required event/entity linkage.'),
 ('ambiguous_cases_resolved','Review the four corrected cases anew and flag any remaining ambiguity; inspect every other case as well. Corrections do not establish approval.'),
 ('category_overlap_not_forced','Treat categories as primary annotations, not mutually exclusive defects. Multiple defects may coexist.'),
 ('human_rationales_recorded','Record a short human rationale and any requested revision for each decision; assistant flags are suggestions, not human findings.'),
 ('no_judge_used_for_gold_labels','Do not query the semantic judge to decide or adjudicate gold labels.'),
 ('disputes_handled_before_results','If a human label differs from the proposal, record the disagreement. Revise/version the benchmark and obtain fresh review before any judge results; never force agreement to satisfy the runner.'),
 ('complete_boolean_gold_labels','Only after every case is resolved may labels contain 36 explicit human booleans, true=admissible and false=inadmissible; ambiguous or pending cases must not be forced to false.'),
 ('approval_explicit_and_uncoerced','Keep approved=false until actual completed human review and explicit human sign-off. Approval is an attestation, not verified identity authentication.'),
 ('scope_preserved','This review does not run the benchmark, authorize live calls, accept ADR-037, mark the PR ready, open inference, or change semantic_grounding_verified=false.'),
]
lines=[
 '# SentinelAI Sprint 20.3-G — 36-case human review packet','',
 '**Status: UNREVIEWED / NOT APPROVED.** No human decisions have been entered. No semantic judge has been queried to establish labels or to review this packet.','',
 f'Repository: `sarurainwaterel-5/sentinel-ai`\n\nBranch: `sprint-20-3-e-production-generator`\n\nPreparation base commit: `{checkpoint}`\n\nDataset: `backend/evaluation/semantic_judge/dataset.json`\n\nVersion: `{data["version"]}`\n\nDataset SHA-256: `{sha}`','',
 'The authoritative dataset has 36 synthetic cases: 18 proposed inadmissible attacks and 18 proposed admissible controls. Proposed labels and source rationales below are reproduced unchanged. They are assistant-authored annotations, not human gold labels.','',
 'Trusted means supplied inputs for this task, not independently established real-world truth. Premise IDs a and b refer only to the row they appear in. Evidence IDs fixture:a and fixture:b are synthetic lineage. Every candidate references both premises and the displayed directional relationship; every candidate has an empty qualifications list. Relationship confidence 0.9 is an assessed relationship attribute, not semantic certification.','',
 '## Review instructions','',
 'Review the premises, relationship and candidate first, then compare your own decision with the proposed label. Choose **admissible**, **inadmissible**, or **ambiguous**. Use ambiguous when wording, reporting scope, conditional meaning, diagnostic direction or event identity prevents a defensible binary label. Give a short rationale and a proposed clarification; do not silently repair the candidate while labeling the original.','',
 'Four previously flagged wording cases have the user-requested v2 corrections recorded below. This is not gold-label approval. Four other cases have overlapping defect categories; this does not necessarily make their admissibility ambiguous. Neither these flags nor the absence of a flag establishes a gold label. Every case requires actual human review.','',
 '## Corrected wording and annotation flags','',
 '| Case ID | Flag type | Review concern |','| --- | --- | --- |',
]
for case_id, flag in flags.items():
 lines.append(f'| {case_id} | {flag["kind"]} | {flag["text"]} |')
lines+=['','## All 36 cases','', 'The three tables below preserve dataset order. “No specific flag” means no additional assistant concern was identified; it does not mean reviewed or approved. Human decisions and notes remain blank in the separate approval record.','']
for domain in ['operations','access','recovery']:
 lines += [f'### {domain.title()} — 12 cases','',
 '| No. / Case ID | Trusted premises | Assessed relationship | Candidate statement | Proposed label | Source rationale | Assistant review flag |',
 '| --- | --- | --- | --- | --- | --- | --- |']
 for i,c in enumerate(cases,1):
  if c['domain']!=domain: continue
  p=' '.join(f'{x["premise_id"]}: {x["statement"]} (evidence: {", ".join(x["evidence_ids"])})' for x in c['premises'])
  rel='; '.join(f'{r["source_premise_id"]} → {r["target_premise_id"]}: {r["kind"].upper()}. Basis: {r["basis"]} Confidence: {r["confidence"]}.' for r in c['relationships'])
  cells=[f'{i}. {c["case_id"]}',p,rel,c['candidate']['statement'],'Admissible (proposed)' if c['proposed_admissible'] else 'Inadmissible (proposed)',c['label_rationale'],flags.get(c['case_id'],{}).get('text','No specific flag; human review required.')]
  lines.append('| '+' | '.join(x.replace('|','\\|').replace('\n',' ') for x in cells)+' |')
 lines.append('')
lines+=['## Human-review checklist','']
for _,text in checklist: lines.append('- [ ] '+text)
lines += ['', '## Approval record — blank and unapproved','',
 '| Field | Current value / human entry |','| --- | --- |',
 '| Overall status | NOT STARTED |', '| Approved | false |', '| Reviewer | blank |', '| Reviewed at (UTC) | blank |',
 '| Independent of candidate generation and judge | not attested / false |',
 '| Human case decisions | 36 blank entries |', '| Gold labels | empty |', '| Human signature / sign-off | blank |','',
 'The accompanying SentinelAI_Sprint_20_3_G_Human_Approval_Record.json contains all 36 case IDs with null human decisions, blank rationales/notes and unchecked checklist items. No proposed label has been copied into its labels mapping.','',
 'To record a decision, set human_decision to admissible, inadmissible or ambiguous. Set human_admissible to true or false only for a resolved human decision; leave it null for pending or ambiguous cases. Record the actual reviewer, timestamp, rationale and any requested revision. Gold labels remain empty until completion; all checklist confirmations and independence attestation remain false until a human actually confirms them.','',
 'The current runner blocks disputed labels instead of accepting a manifest that disagrees with the dataset proposals. Do not change a human label to match a proposal for that reason. A disagreement requires revising/versioning the disputed fixture and renewed review against its new hash before any benchmark execution. This packet does not alter the dataset, runner or thresholds.','',
 'Once a human has actually completed review, resolved every case, recorded 36 boolean gold labels against the final dataset hash, and explicitly signed off, a runner manifest can be prepared using the repository’s template fields. No approval is given by this packet and no live benchmark is executed.','',
 '## Preserved boundaries','',
 'ADR-037 remains Proposed. PR #1 remains Draft. Main, inference and conclusion behavior are unchanged. semantic_grounding_verified=false. Proposition → Inference remains CLOSED.',''
]
packet=root/'SentinelAI_Sprint_20_3_G_Human_Review_Packet.md'
packet.write_text('\n'.join(lines))
record=dict(repository='sarurainwaterel-5/sentinel-ai',branch='sprint-20-3-e-production-generator',preparation_base_commit=checkpoint,
 dataset_version=data['version'],dataset_sha256=sha,review_status='not_started',approved=False,reviewer=None,reviewed_at=None,
 independent_of_candidate_generation_and_judge=False,human_signature=None,labels={},
 checklist={key:False for key,_ in checklist},
 case_reviews=[dict(case_id=c['case_id'],human_decision=None,human_admissible=None,human_rationale=None,requested_revision=None,
                    reviewed_by=None,reviewed_at=None,assistant_flag=flags.get(c['case_id'])) for c in cases])
record_path=root/'SentinelAI_Sprint_20_3_G_Human_Approval_Record.json'
record_path.write_text(json.dumps(record,indent=2)+'\n')
# Verify coverage and exact source text, not the semantic correctness of labels.
text=packet.read_text(); saved=json.loads(record_path.read_text())
assert len(saved['case_reviews'])==36
assert {r['case_id'] for r in saved['case_reviews']}=={c['case_id'] for c in cases}
assert saved['approved'] is False and saved['labels']=={}
assert not any(saved['checklist'].values())
assert all(r['human_decision'] is None and r['human_admissible'] is None for r in saved['case_reviews'])
for i,c in enumerate(cases,1):
 assert f'| {i}. {c["case_id"]} |' in text
 assert c['candidate']['statement'] in text and c['label_rationale'] in text
 assert all(p['statement'] in text for p in c['premises'])
assert hashlib.sha256(source.read_bytes()).hexdigest()==sha
print(json.dumps(dict(files=[str(packet),str(record_path)],rows=36,ambiguous_cases=[k for k,v in flags.items() if v['kind']=='ambiguity'],overlapping_defect_cases=[k for k,v in flags.items() if v['kind']=='overlapping_defects'],approved=False)))
