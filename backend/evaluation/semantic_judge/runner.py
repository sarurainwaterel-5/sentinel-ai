"""Pre-registered, human-reviewed empirical evaluation of the real judge gate.

The CLI has no scripted-provider option. Test injection is explicitly labeled
unit_test and can never yield empirical acceptance. Labels never enter requests.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import subprocess
import sys
import time

from app.services.cognition.reasoning.models import CandidateProposition, Premise, PremiseRelationship
from app.services.cognition.reasoning.proposition_grounding_validator import PropositionGroundingValidator
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.cognition.reasoning.statement_admissibility_validator import FreeFormStatementAdmissibilityValidator
from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider

ROOT = Path(__file__).parent


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(dataset_path, policy_path, review_path):
    dataset = json.loads(dataset_path.read_text())
    policy = json.loads(policy_path.read_text())
    cases = dataset['cases']
    ids = [c['case_id'] for c in cases]
    if len(set(ids)) != len(ids) or len(cases) != policy['expected_cases']:
        raise ValueError('Invalid dataset size or duplicate case IDs.')
    if policy['repetitions'] < 3:
        raise ValueError('Stability requires at least three repetitions.')
    for case in cases:
        if type(case['proposed_admissible']) is not bool:
            raise ValueError('Labels must be explicit booleans.')
        candidate = CandidateProposition.model_validate(case['candidate'])
        if set(candidate.premise_ids) != {p['premise_id'] for p in case['premises']}:
            raise ValueError('Each benchmark candidate must cover all supplied premises.')
        if any(r['kind'] not in {'supports', 'complements', 'conflicts'} for r in case['relationships']):
            raise ValueError('Only semantically judgeable relationships belong in this benchmark.')
        result = PropositionGroundingValidator().validate(
            candidate=candidate,
            premises=[Premise.model_validate(p) for p in case['premises']],
            relationships=[PremiseRelationship.model_validate(r) for r in case['relationships']],
        )
        if not result.structurally_valid:
            raise ValueError('Semantic benchmark must contain structurally valid candidates.')
    counts = Counter(c['proposed_admissible'] for c in cases)
    if counts[True] != policy['expected_admissible'] or counts[False] != policy['expected_inadmissible']:
        raise ValueError('Dataset class balance differs from pre-registration.')
    for label, groups in [(False, policy['negative_categories']), (True, policy['positive_categories'])]:
        if {c['category'] for c in cases if c['proposed_admissible'] == label} != set(groups):
            raise ValueError('Required semantic categories are missing or mislabeled.')
    review = json.loads(review_path.read_text()) if review_path.exists() else None
    blockers = []
    labels = None
    if review is None:
        blockers.append('human_review_missing')
    elif (review.get('approved') is not True or not review.get('reviewer')
          or not review.get('reviewed_at')
          or review.get('independent_of_candidate_generation_and_judge') is not True):
        blockers.append('independent_human_review_unapproved')
    elif review.get('dataset_sha256') != digest(dataset_path):
        blockers.append('human_review_dataset_hash_mismatch')
    elif (set(review.get('labels', {})) != set(ids)
          or any(type(v) is not bool for v in review['labels'].values())):
        blockers.append('human_review_labels_incomplete')
    elif any(review['labels'][c['case_id']] != c['proposed_admissible'] for c in cases):
        # Do not force agreement with assistant proposals. Disputes require a
        # revised benchmark and new review BEFORE examining judge outcomes.
        blockers.append('disputed_labels_require_dataset_revision_before_evaluation')
    else:
        labels = review['labels']
    return cases, policy, labels, blockers


def _matrix(rows, labels):
    matrix = dict(true_accepts=0, false_accepts=0, false_rejects=0, true_rejects=0)
    for row in rows:
        gold = labels[row['case_id']]
        name = ('true_accepts' if gold else 'false_accepts') if row['admissible'] else ('false_rejects' if gold else 'true_rejects')
        matrix[name] += 1
    return matrix


def summarize(cases, labels, rows, policy):
    valid = [r for r in rows if not r['operational_error']]
    matrix = _matrix(valid, labels)
    total = len(valid)
    positive = matrix['true_accepts'] + matrix['false_rejects']
    negative = matrix['true_rejects'] + matrix['false_accepts']
    by_case = defaultdict(list)
    for row in rows:
        by_case[row['case_id']].append(row)
    complete = len(rows) == len(cases) * policy['repetitions'] and all(
        len(by_case[c['case_id']]) == policy['repetitions'] for c in cases)
    stable = sum(len(by_case[c['case_id']]) == policy['repetitions']
                 and not any(r['operational_error'] for r in by_case[c['case_id']])
                 and len({r['admissible'] for r in by_case[c['case_id']]}) == 1 for c in cases)
    stability = stable / len(cases)
    reason_stable = sum(len(by_case[c['case_id']]) == policy['repetitions']
                        and not any(r['operational_error'] for r in by_case[c['case_id']])
                        and len({tuple(sorted(r.get('rejection_reasons', [])))
                                 for r in by_case[c['case_id']]}) == 1 for c in cases)
    accuracy = (matrix['true_accepts'] + matrix['true_rejects']) / total if total else None
    false_reject_rate = matrix['false_rejects'] / positive if positive else None
    categories = {}
    for category in sorted({c['category'] for c in cases}):
        ids = {c['case_id'] for c in cases if c['category'] == category}
        group = [r for r in rows if r['case_id'] in ids]
        categories[category] = dict(cases=len(ids), trials=len(group),
            operational_errors=sum(r['operational_error'] for r in group),
            confusion_matrix=_matrix([r for r in group if not r['operational_error']], labels))
    positive_coverage = all(sum(all(r['admissible'] and not r['operational_error'] for r in by_case[c['case_id']])
        and len(by_case[c['case_id']]) == policy['repetitions'] for c in cases if c['category'] == category)
        >= policy['min_accepted_cases_per_positive_category'] for category in policy['positive_categories'])
    errors = sum(r['operational_error'] for r in rows)
    passed = (complete and errors <= policy['max_operational_errors']
              and matrix['false_accepts'] <= policy['max_false_accepts']
              and false_reject_rate is not None and false_reject_rate <= policy['max_false_reject_rate']
              and accuracy is not None and accuracy >= policy['min_accuracy']
              and stability >= policy['min_decision_stability'] and positive_coverage)
    return dict(confusion_matrix=matrix, fail_closed_decision_matrix=_matrix(rows, labels),
        accuracy=accuracy, false_accept_rate=matrix['false_accepts'] / negative if negative else None,
        false_reject_rate=false_reject_rate, operational_errors=errors,
        classification_coverage=total / len(rows) if rows else 0,
        stable_cases=stable, decision_stability=stability, complete=complete,
        reason_stable_cases=reason_stable, reason_stability=reason_stable / len(cases),
        category_results=categories, criteria_passed=passed,
        false_accept_cases=sorted({r['case_id'] for r in valid if r['admissible'] and not labels[r['case_id']]}),
        false_reject_cases=sorted({r['case_id'] for r in valid if not r['admissible'] and labels[r['case_id']]}))


def run_trials(cases, labels, policy, provider, *, execution_source='unit_test', checkpoint=None):
    """Injected test providers never establish actual_api evidence via default."""
    validator = FreeFormStatementAdmissibilityValidator(provider=provider)
    rows = []
    for repetition in range(policy['repetitions']):
        ordered = list(cases)
        random.Random(policy['order_seed'] + repetition).shuffle(ordered)
        for case in ordered:
            start = time.monotonic()
            result = validator.validate(
                candidate=CandidateProposition.model_validate(case['candidate']),
                premises=[Premise.model_validate(p) for p in case['premises']],
                relationships=[PremiseRelationship.model_validate(r) for r in case['relationships']],
            )
            operational_error = any(r.startswith('semantic_judge_') for r in result.rejection_reasons)
            rows.append(dict(case_id=case['case_id'], repetition=repetition,
                admissible=result.admissible, rejection_reasons=list(result.rejection_reasons),
                scope=result.validation_scope, operational_error=operational_error,
                elapsed_seconds=round(time.monotonic() - start, 3)))
            if checkpoint:
                checkpoint(rows)
    metrics = summarize(cases, labels, rows, policy)
    return dict(execution_source=execution_source, trials=rows, metrics=metrics,
                empirical_acceptance=execution_source == 'actual_api' and metrics['criteria_passed'])


def _write(path, report):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset', type=Path, default=ROOT / 'dataset.json')
    parser.add_argument('--policy', type=Path, default=ROOT / 'acceptance.json')
    parser.add_argument('--review', type=Path, default=ROOT / 'human_review.json')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    cases, policy, labels, blockers = load_inputs(args.dataset, args.policy, args.review)
    key = os.environ.get('SEMANTIC_JUDGE_API_KEY')
    model = os.environ.get('SEMANTIC_JUDGE_MODEL')
    if not key or 'placeholder' in key.lower():
        blockers.append('SEMANTIC_JUDGE_API_KEY_missing_or_placeholder')
    if not model:
        blockers.append('SEMANTIC_JUDGE_MODEL_missing')
    git_head = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True).stdout.strip()
    report = dict(status='blocked' if blockers else 'running', execution_source='not_executed',
        dataset_size=len(cases), planned_calls=len(cases) * policy['repetitions'],
        provider='OpenAI', model=model, dataset_sha256=digest(args.dataset),
        policy_sha256=digest(args.policy), review_sha256=digest(args.review) if args.review.exists() else None,
        runner_sha256=digest(Path(__file__)),
        verdict_schema_sha256=hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest(),
        prompt_sha256=hashlib.sha256(OpenAISemanticAdmissibilityProvider.system_message().encode()).hexdigest(),
        commit=git_head, python=sys.version.split()[0], started_at=datetime.now(timezone.utc).isoformat(),
        criteria=policy, blockers=blockers, trials=[], metrics=None, empirical_acceptance=False,
        semantic_grounding_verified=False, proposition_to_inference='closed')
    _write(args.output, report)
    if blockers:
        print(json.dumps(dict(status='blocked', blockers=blockers, executed_calls=0)))
        return 2
    # A new client, separate from every generation client. No generator is
    # constructed or called. Dedicated credentials; no .env or ambient-key fallback.
    from openai import OpenAI, __version__ as sdk_version
    provider = OpenAISemanticAdmissibilityProvider(
        client=OpenAI(api_key=key, timeout=30.0, max_retries=0), model=model)
    report.update(openai_sdk_version=sdk_version, execution_source='actual_api')
    def checkpoint(rows):
        report['trials'] = list(rows)
        _write(args.output, report)
    try:
        report.update(run_trials(cases, labels, policy, provider,
                                execution_source='actual_api', checkpoint=checkpoint))
        report['status'] = 'passed' if report['empirical_acceptance'] else 'failed'
    except KeyboardInterrupt:
        report['status'] = 'interrupted'
        report['metrics'] = summarize(cases, labels, report['trials'], policy)
        report['empirical_acceptance'] = False
    finally:
        provider.client.close()
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        _write(args.output, report)
    print(json.dumps(dict(status=report['status'], output=str(args.output), metrics=report['metrics'])))
    return 0 if report['empirical_acceptance'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
