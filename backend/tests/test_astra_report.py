"""Synthetic consistency records never establish live semantic acceptance."""
import copy
import hashlib
import json
from pathlib import Path
import random

import pytest

from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.providers.openai_reasoning_admissibility import OpenAIReasoningAdmissibilityProvider
from evaluation.semantic_judge.astra_report import FILES, inspect_astra_report
from evaluation.semantic_judge.astra_runner import CONFIG, ROLES
from evaluation.semantic_judge.runner import digest, load_inputs, summarize

ROOT = Path(__file__).resolve().parents[2]


@pytest.fixture
def evidence(tmp_path):
    for name in FILES.values():
        target = tmp_path / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((ROOT / name).read_bytes())
    paths = {key: tmp_path / name for key, name in FILES.items()}
    cases, policy, labels, blockers = load_inputs(paths['dataset_sha256'], paths['policy_sha256'], paths['review_sha256'])
    assert not blockers
    rows = []
    for repetition in range(3):
        ordered = list(cases)
        random.Random(policy['order_seed'] + repetition).shuffle(ordered)
        rows.extend(dict(case_id=c['case_id'], repetition=repetition, admissible=labels[c['case_id']],
                         operational_error=False, rejection_reasons=[] if labels[c['case_id']] else ['unsupported_fact'],
                         scope='independent_model_semantic_admissibility', elapsed_seconds=0) for c in ordered)
    report = dict(version='astra-benchmark-v1', execution_source='actual_api', provider='OpenAI',
                  model=CONFIG['model'], provider_config=CONFIG, selected_roles=ROLES,
                  criteria=policy, dataset_size=36, planned_calls=108, executed_calls=108, blockers=[],
                  openai_sdk_version='synthetic', python='synthetic', commit='synthetic',
                  started_at='2026-11-10T00:00:00Z', finished_at='2026-11-10T00:01:00Z',
                  status='passed', empirical_acceptance=True, trials=rows, metrics=summarize(cases, labels, rows, policy),
                  **{key: digest(path) for key, path in paths.items()},
                  prompt_sha256=hashlib.sha256(OpenAIReasoningAdmissibilityProvider.system_message().encode()).hexdigest(),
                  verdict_schema_sha256=hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest())
    return tmp_path, report


def inspect(evidence, change=None):
    root, original = evidence
    report = copy.deepcopy(original)
    if change:
        change(report)
    path = root / 'synthetic-report.json'
    path.write_text(json.dumps(report))
    result = inspect_astra_report(root, path)
    assert result['production_enabled'] is False
    assert result['release_authorized'] is False
    assert result['enabled'] is False
    assert result['semantic_grounding_verified'] is False
    assert result['proposition_to_inference'] == 'closed'
    assert result['blockers']
    return result


def test_absent_report_is_blocked():
    assert inspect_astra_report(ROOT)['errors'] == ['astra_report_missing']


def test_synthetic_consistency_only_qualifies_for_human_review(evidence):
    result = inspect(evidence)
    assert result['errors'] == []
    assert result['empirical_report_eligible_for_human_review'] is True


@pytest.mark.parametrize('change', [
    lambda r: r.update(version='wrong'), lambda r: r.update(execution_source='unit_test'),
    lambda r: r.update(model='wrong'), lambda r: r.update(adapter_sha256='wrong'),
    lambda r: r.update(runner_sha256='wrong'), lambda r: r.update(model_selection_sha256='wrong'),
    lambda r: r.update(provider_config={}), lambda r: r['provider_config'].update(max_retries=False),
    lambda r: r.update(selected_roles={}),
    lambda r: r.update(executed_calls=True), lambda r: r.update(empirical_acceptance=1),
    lambda r: r.update(metrics={'criteria_passed': True}),
    lambda r: r['metrics'].update(criteria_passed=1),
    lambda r: r.update(finished_at='2026-11-09T00:00:00Z'),
    lambda r: r['trials'].pop(), lambda r: r['trials'].reverse(),
    lambda r: r['trials'][0].update(admissible='true'),
    lambda r: r['trials'][0].update(repetition=True),
    lambda r: r['trials'][0].update(operational_error=True),
    lambda r: r['trials'][0].update(rejection_reasons=['invented_reason']),
    lambda r: r['trials'][0].update(elapsed_seconds=float('nan')),
    lambda r: r['trials'][0].update(elapsed_seconds=True),
])
def test_tampered_report_is_rejected(evidence, change):
    assert not inspect(evidence, change)['empirical_report_eligible_for_human_review']


def test_relaxed_policy_with_matching_hash_is_rejected(evidence):
    root, report = evidence
    path = root / FILES['policy_sha256']
    policy = json.loads(path.read_text())
    policy['min_accuracy'] = 0
    path.write_text(json.dumps(policy))
    report.update(criteria=policy, policy_sha256=digest(path))
    assert 'unregistered_benchmark_revision' in inspect(evidence)['errors']


def test_tampered_manifest_with_matching_hash_is_rejected(evidence):
    root, report = evidence
    path = root / FILES['model_selection_sha256']
    manifest = json.loads(path.read_text())
    manifest['benchmark']['reasoning_effort'] = 'high'
    path.write_text(json.dumps(manifest))
    report['model_selection_sha256'] = digest(path)
    assert 'model_selection_config_mismatch' in inspect(evidence)['errors']


@pytest.mark.parametrize('raw', ['{"status":"passed","status":"failed"}', ' ' * (2 * 1024 * 1024 + 1)])
def test_invalid_json_and_oversized_report_rejected(tmp_path, raw):
    path = tmp_path / 'report.json'
    path.write_text(raw)
    assert inspect_astra_report(tmp_path, path)['errors']


def test_symlink_escape_is_rejected(tmp_path):
    outside = tmp_path.parent / (tmp_path.name + '-outside.json')
    outside.write_text('{}')
    path = tmp_path / 'report.json'
    path.symlink_to(outside)
    assert inspect_astra_report(tmp_path, path)['errors']
