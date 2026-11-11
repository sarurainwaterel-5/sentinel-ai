"""Versioned benchmark preflight tests; never read credentials or call a provider."""
import json
import pytest
from evaluation.semantic_judge import astra_runner as runner


def test_missing_dedicated_key_blocks_without_ambient_fallback(tmp_path, monkeypatch):
    seen = []
    def getenv(name):
        seen.append(name)
        return None
    monkeypatch.setattr(runner.os.environ, 'get', getenv)
    output = tmp_path / 'preflight.json'
    assert runner.main(['--output', str(output)]) == 2
    assert [name for name in seen if 'API_KEY' in name] == ['SEMANTIC_JUDGE_API_KEY']
    report = json.loads(output.read_text())
    assert report['executed_calls'] == 0 and report['planned_calls'] == 108
    assert report['trials'] == [] and report['metrics'] is None
    assert report['execution_source'] == 'not_executed'
    assert report['blockers'] == ['SEMANTIC_JUDGE_API_KEY_missing_or_placeholder']
    assert not report['empirical_acceptance']
    for field in ('adapter_sha256','runner_sha256','legacy_runner_sha256','legacy_adapter_sha256',
                  'model_selection_sha256','dataset_sha256','policy_sha256','review_sha256',
                  'prompt_sha256','verdict_schema_sha256'):
        assert len(report[field]) == 64
    assert report['provider_config'] == runner.CONFIG
    assert report['proposition_to_inference'] == 'closed'


@pytest.mark.parametrize('mutation,expected', [
    ('roles', 'model_selection_roles_mismatch'),
    ('config', 'preregistered_benchmark_config_mismatch'),
    ('hash', 'preregistered_frozen_hashes_mismatch'),
])
def test_preregistration_drift_is_blocked(tmp_path, monkeypatch, mutation, expected):
    monkeypatch.setattr(runner.os.environ, 'get', lambda name: None)
    selection = json.loads((runner.REPO / 'docs/governance/sprint21-model-selection.json').read_text())
    if mutation == 'roles':
        selection['roles']['semantic_judge'] = 'different-model'
    elif mutation == 'config':
        selection['benchmark']['max_completion_tokens'] = 8192
    else:
        selection['benchmark']['frozen_input_sha256']['dataset.json'] = 'stale'
    path = tmp_path / 'selection.json'; path.write_text(json.dumps(selection))
    output = tmp_path / 'blocked.json'
    assert runner.main(['--selection', str(path), '--output', str(output)]) == 2
    report = json.loads(output.read_text())
    assert expected in report['blockers'] and report['executed_calls'] == 0


def test_no_cli_provider_or_model_override(tmp_path):
    with pytest.raises(SystemExit):
        runner.main(['--output', str(tmp_path / 'x'), '--model', 'other'])


def test_output_cannot_overwrite_frozen_input(monkeypatch):
    monkeypatch.setattr(runner.os.environ, 'get', lambda name: None)
    path = runner.ROOT / 'dataset.json'
    before = path.read_bytes()
    with pytest.raises(SystemExit):
        runner.main(['--output', str(path)])
    assert path.read_bytes() == before


@pytest.mark.parametrize('name', ['untracked-report.json', '.env'])
def test_existing_untracked_output_preserved(tmp_path, monkeypatch, name):
    monkeypatch.setattr(runner.os.environ, 'get', lambda name: None)
    output = tmp_path / name
    output.write_text('private fixture content')
    with pytest.raises(SystemExit):
        runner.main(['--output', str(output)])
    assert output.read_text() == 'private fixture content'


def test_broken_output_symlink_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(runner.os.environ, 'get', lambda name: None)
    output = tmp_path / 'report.json'
    target = tmp_path / 'missing'
    output.symlink_to(target)
    with pytest.raises(SystemExit):
        runner.main(['--output', str(output)])
    assert output.is_symlink() and not target.exists()


@pytest.mark.parametrize('malformation', ['boolean_retry', 'duplicate_key', 'oversize'])
def test_manifest_strict_json_and_scalar_types(tmp_path, monkeypatch, malformation):
    monkeypatch.setattr(runner.os.environ, 'get', lambda name: None)
    raw = (runner.REPO / 'docs/governance/sprint21-model-selection.json').read_text()
    if malformation == 'boolean_retry':
        selection = json.loads(raw)
        selection['benchmark']['max_retries'] = False
        raw = json.dumps(selection)
    elif malformation == 'duplicate_key':
        raw = raw.replace('"max_retries": 0', '"max_retries": 1, "max_retries": 0')
    else:
        raw = ' ' * 65537 + raw
    path = tmp_path / 'selection.json'; path.write_text(raw)
    output = tmp_path / 'report.json'
    assert runner.main(['--selection', str(path), '--output', str(output)]) == 2
    blockers = json.loads(output.read_text())['blockers']
    assert ('preregistered_benchmark_config_mismatch' if malformation == 'boolean_retry'
            else 'model_selection_missing') in blockers
