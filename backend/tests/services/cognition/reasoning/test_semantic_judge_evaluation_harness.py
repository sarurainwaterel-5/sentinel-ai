"""Synthetic harness unit tests, NOT measured semantic judge accuracy."""
import json
import pytest
from evaluation.semantic_judge.runner import ROOT, digest, load_inputs, main, run_trials, summarize
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticAdmissibilityResponse, SemanticJudgeVerdict


def inputs(tmp_path):
    data = json.loads((ROOT / 'dataset.json').read_text())
    review = dict(dataset_sha256=digest(ROOT / 'dataset.json'), approved=True,
        reviewer='UNIT_TEST_NOT_HUMAN_REVIEW', reviewed_at='UNIT_TEST_TIMESTAMP',
        independent_of_candidate_generation_and_judge=True,
        labels={c['case_id']: c['proposed_admissible'] for c in data['cases']})
    path = tmp_path / 'review.json'
    path.write_text(json.dumps(review))
    return load_inputs(ROOT / 'dataset.json', ROOT / 'acceptance.json', path), path


def test_dataset_coverage_and_structural_validity(tmp_path):
    (cases, policy, labels, blockers), _ = inputs(tmp_path)
    assert len(cases) == 36 and sum(labels.values()) == 18
    assert blockers == []
    for category in policy['negative_categories'] + policy['positive_categories']:
        assert sum(c['category'] == category for c in cases) == 3
    assert all(c['annotation_status'] == 'requires_independent_human_review' for c in cases)


@pytest.mark.parametrize('change,blocker', [
    ({'approved': False}, 'independent_human_review_unapproved'),
    ({'reviewer': None}, 'independent_human_review_unapproved'),
    ({'independent_of_candidate_generation_and_judge': False}, 'independent_human_review_unapproved'),
    ({'dataset_sha256': 'stale'}, 'human_review_dataset_hash_mismatch'),
    ({'labels': {}}, 'human_review_labels_incomplete'),
])
def test_review_gates(tmp_path, change, blocker):
    _, path = inputs(tmp_path)
    review = json.loads(path.read_text()); review.update(change)
    path.write_text(json.dumps(review))
    assert load_inputs(ROOT / 'dataset.json', ROOT / 'acceptance.json', path)[3] == [blocker]


def test_disputed_labels_require_revision(tmp_path):
    _, path = inputs(tmp_path)
    review = json.loads(path.read_text()); key = next(iter(review['labels']))
    review['labels'][key] = not review['labels'][key]
    path.write_text(json.dumps(review))
    assert load_inputs(ROOT / 'dataset.json', ROOT / 'acceptance.json', path)[3] == ['disputed_labels_require_dataset_revision_before_evaluation']


def test_blocked_cli_has_no_calls_or_metrics(tmp_path, monkeypatch):
    for key in ['SEMANTIC_JUDGE_API_KEY', 'SEMANTIC_JUDGE_MODEL']:
        monkeypatch.delenv(key, raising=False)
    out = tmp_path / 'blocked.json'
    assert main(['--review', str(tmp_path / 'missing.json'), '--output', str(out)]) == 2
    report = json.loads(out.read_text())
    assert report['metrics'] is None and report['trials'] == []
    assert report['status'] == 'blocked' and report['execution_source'] == 'not_executed'
    assert not report['empirical_acceptance'] and len(report['blockers']) == 3


def rows_for(cases, labels, repeats):
    return [dict(case_id=c['case_id'], repetition=i, admissible=labels[c['case_id']], operational_error=False)
            for i in range(repeats) for c in cases]


def test_confusion_matrix_and_stability(tmp_path):
    (cases, policy, labels, _), _ = inputs(tmp_path)
    rows = rows_for(cases, labels, 3)
    next(r for r in rows if not labels[r['case_id']])['admissible'] = True
    next(r for r in rows if labels[r['case_id']])['admissible'] = False
    result = summarize(cases, labels, rows, policy)
    assert result['confusion_matrix'] == dict(true_accepts=53, false_accepts=1, false_rejects=1, true_rejects=53)
    assert result['accuracy'] == 106 / 108 and result['stable_cases'] == 34
    assert not result['criteria_passed']
    assert len(result['false_accept_cases']) == len(result['false_reject_cases']) == 1


def test_errors_not_counted_as_semantic_correctness(tmp_path):
    (cases, policy, labels, _), _ = inputs(tmp_path)
    rows = rows_for(cases, labels, 3)
    for row in rows:
        row.update(operational_error=True, admissible=False)
    result = summarize(cases, labels, rows, policy)
    assert result['accuracy'] is None and sum(result['confusion_matrix'].values()) == 0
    assert result['operational_errors'] == 108 and not result['criteria_passed']
    assert result['fail_closed_decision_matrix']['true_rejects'] == 54


def test_incomplete_and_unstable_results_cannot_pass(tmp_path):
    (cases, policy, labels, _), _ = inputs(tmp_path)
    rows = rows_for(cases, labels, 3)
    assert not summarize(cases, labels, rows[:-1], policy)['criteria_passed']
    rows[0]['admissible'] = not rows[0]['admissible']
    assert summarize(cases, labels, rows, policy)['decision_stability'] < 1


def test_unit_provider_never_creates_empirical_acceptance_or_sees_labels(tmp_path):
    (cases, policy, labels, _), _ = inputs(tmp_path)
    mapping = {c['candidate']['statement']: labels[c['case_id']] for c in cases}
    captured = []
    class TestOnlyProvider:
        def assess(self, *, request):
            captured.append(request.model_dump())
            accepted = mapping[request.statement]
            data = {k: False for k in SemanticJudgeVerdict.model_fields if k not in {'admissible', 'rejection_reasons'}}
            data.update(admissible=accepted, unsupported_fact=not accepted,
                        rejection_reasons=[] if accepted else ['unsupported_fact'])
            return SemanticAdmissibilityResponse(content=json.dumps(data))
    report = run_trials(cases, labels, policy, TestOnlyProvider())
    assert len(report['trials']) == 108 and report['metrics']['criteria_passed']
    assert report['execution_source'] == 'unit_test' and not report['empirical_acceptance']
    assert all(set(r) == {'statement', 'qualifications', 'premises', 'relationships'} for r in captured)


def test_pre_registered_thresholds():
    policy = json.loads((ROOT / 'acceptance.json').read_text())
    assert policy['max_false_accepts'] == 0 and policy['max_false_reject_rate'] == 0.1
    assert policy['min_accuracy'] == 0.95 and policy['min_decision_stability'] == 1
    assert policy['max_operational_errors'] == 0


def test_reason_stability_is_reported_separately(tmp_path):
    (cases, policy, labels, _), _ = inputs(tmp_path)
    rows = rows_for(cases, labels, 3)
    rows[0]['rejection_reasons'] = ['unsupported_fact']
    report = summarize(cases, labels, rows, policy)
    assert report['decision_stability'] == 1
    assert report['reason_stability'] == 35 / 36
