"""Version 1 Astra benchmark; frozen inputs, dedicated judge key, no retries."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from evaluation.semantic_judge.runner import ROOT, digest, load_inputs, run_trials, summarize, _write
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict
from app.services.providers.openai_semantic_admissibility import OpenAISemanticAdmissibilityProvider
from app.services.providers.openai_reasoning_admissibility import OpenAIReasoningAdmissibilityProvider

REPO = ROOT.parents[2]
ROLES = {"generation": "gpt-6.1-sol", "semantic_judge": "gpt-6-astra", "relevance": "gpt-6.1-terra"}
FROZEN_INPUTS = {
    'dataset.json': 'd57de823b86797a6b25ff36a808c678cc8843ef5a1b4d7188576f27fe0cc7adb',
    'acceptance.json': '4847ef02ffe88b3747944eb736fbd79c7e46518297f9c819877fd910ce497288',
    'SentinelAI_Sprint_20_3_G_Human_Approval_Record.json': 'e4fe2bcf4f202e18fc12fd41801b36872629b43462e7dc266841900f48cf1917',
}
CONFIG = {"model": "gpt-6-astra", "reasoning_effort": "low", "max_completion_tokens": 4096, "timeout": 30.0, "max_retries": 0}


def _selection_json(path):
    """Bounded manifest parsing rejects duplicate keys and non-JSON numbers."""
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate manifest key')
            result[key] = value
        return result
    def invalid_constant(value):
        raise ValueError('Non-finite manifest number')
    with path.open('rb') as stream:
        raw = stream.read(65537)
    if len(raw) > 65536:
        raise ValueError('Manifest too large')
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid_constant)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--review', type=Path, default=ROOT / 'SentinelAI_Sprint_20_3_G_Human_Approval_Record.json')
    parser.add_argument('--selection', type=Path, default=REPO / 'docs/governance/sprint21-model-selection.json')
    args = parser.parse_args(argv)
    dataset, policy_path = ROOT / 'dataset.json', ROOT / 'acceptance.json'
    cases, policy, labels, blockers = load_inputs(dataset, policy_path, args.review)
    protected = [dataset, policy_path, args.review, args.selection, Path(__file__), ROOT / 'runner.py',
                 Path(sys.modules[OpenAIReasoningAdmissibilityProvider.__module__].__file__),
                 Path(sys.modules[OpenAISemanticAdmissibilityProvider.__module__].__file__)]
    tracked = subprocess.run(['git', 'ls-files', '--error-unmatch', str(args.output.resolve())],
                             capture_output=True).returncode == 0
    if args.output.exists() or args.output.is_symlink():
        parser.error('Output must be a new file; existing outputs cannot be overwritten.')
    if args.output.resolve() in {p.resolve() for p in protected} or tracked:
        parser.error('Output must not overwrite benchmark inputs, implementations, or tracked files.')
    try:
        selection = _selection_json(args.selection) if args.selection.exists() else None
    except (ValueError, OSError, RecursionError):
        selection = None
    if selection is not None and not isinstance(selection, dict):
        selection = None
    if selection is None:
        blockers.append('model_selection_missing')
    elif selection.get('roles') != ROLES:
        blockers.append('model_selection_roles_mismatch')
    if selection is not None:
        expected = dict(model=CONFIG['model'], reasoning_effort='low', max_completion_tokens=4096,
                        timeout_seconds=30.0, max_retries=0, sampling_parameters='omitted',
                        expected_cases=36, repetitions=3, planned_calls=108, order_seed=203)
        benchmark = selection.get('benchmark', {})
        if not isinstance(benchmark, dict):
            benchmark = {}
        if benchmark.get('version') != 'astra-semantic-benchmark-v1':
            blockers.append('preregistered_benchmark_version_mismatch')
        if any(type(benchmark.get(k)) is not type(v) or benchmark.get(k) != v for k, v in expected.items()):
            blockers.append('preregistered_benchmark_config_mismatch')
        frozen = benchmark.get('frozen_input_sha256', {})
        if frozen != FROZEN_INPUTS:
            blockers.append('preregistered_frozen_hashes_mismatch')
        if not isinstance(frozen, dict):
            frozen = {}
        for path in (dataset, policy_path, args.review):
            if not path.exists() or FROZEN_INPUTS.get(path.name) != digest(path):
                blockers.append('preregistered_input_hash_mismatch:' + path.name)
    key = os.environ.get('SEMANTIC_JUDGE_API_KEY')
    if not key or 'placeholder' in key.lower():
        blockers.append('SEMANTIC_JUDGE_API_KEY_missing_or_placeholder')
    adapter_path = Path(sys.modules[OpenAIReasoningAdmissibilityProvider.__module__].__file__)
    legacy_adapter = Path(sys.modules[OpenAISemanticAdmissibilityProvider.__module__].__file__)
    report = dict(version='astra-benchmark-v1', status='blocked' if blockers else 'running',
        execution_source='not_executed', dataset_size=len(cases), planned_calls=len(cases)*policy['repetitions'],
        executed_calls=0, provider='OpenAI', model=CONFIG['model'], provider_config=CONFIG, selected_roles=ROLES,
        model_selection_sha256=digest(args.selection) if selection is not None else None,
        dataset_sha256=digest(dataset), policy_sha256=digest(policy_path),
        review_sha256=digest(args.review) if args.review.exists() else None,
        runner_sha256=digest(Path(__file__)), adapter_sha256=digest(adapter_path),
        legacy_runner_sha256=digest(ROOT / 'runner.py'), legacy_adapter_sha256=digest(legacy_adapter),
        verdict_schema_sha256=hashlib.sha256(json.dumps(SemanticJudgeVerdict.model_json_schema(), sort_keys=True).encode()).hexdigest(),
        prompt_sha256=hashlib.sha256(OpenAIReasoningAdmissibilityProvider.system_message().encode()).hexdigest(),
        commit=subprocess.run(['git','rev-parse','HEAD'], capture_output=True,text=True).stdout.strip(),
        python=sys.version.split()[0], started_at=datetime.now(timezone.utc).isoformat(),
        criteria=policy, blockers=blockers, trials=[], metrics=None, empirical_acceptance=False,
        semantic_grounding_verified=False, proposition_to_inference='closed')
    # Persist bound inputs and configuration before any possible API request.
    args.output.parent.mkdir(parents=True, exist_ok=True)
    try:
        # Exclusive reservation also closes the check/write race for an existing path.
        with args.output.open('x') as stream:
            stream.write(json.dumps(report, indent=2) + '\n')
    except FileExistsError:
        parser.error('Output appeared during preflight; refusing to overwrite it.')
    if blockers:
        print(json.dumps(dict(status='blocked', blockers=blockers, executed_calls=0)))
        return 2
    from openai import OpenAI, __version__ as sdk_version
    provider = OpenAIReasoningAdmissibilityProvider(
        client=OpenAI(api_key=key, timeout=30.0, max_retries=0), **CONFIG)
    report.update(openai_sdk_version=sdk_version, execution_source='actual_api')
    def checkpoint(rows):
        report['trials'] = list(rows)
        report['executed_calls'] = len(rows)
        _write(args.output, report)
    try:
        report.update(run_trials(cases, labels, policy, provider, execution_source='actual_api', checkpoint=checkpoint))
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
