import asyncio
import copy
import json
import hashlib
import os
import stat
import sys
from types import SimpleNamespace
import pytest
from evaluation.governed_answers import live_provider_rehearsal as module
from app.services.providers.openai_governed_transport import GovernedTransportFailure
from evaluation.governed_answers.live_provider_rehearsal import (
    load_inputs, candidate_from, structurally_complete, consistent, run_rehearsal, render_review, digest,
)
from app.services.cognition.reasoning.semantic_admissibility_provider import SemanticJudgeVerdict


class ScriptedTransport:
    execution_source = 'unit_test'
    def __init__(self, cases, labels):
        self.cases, self.labels, self.calls = cases, labels, []
    async def call(self, *, role, request_json):
        payload = json.loads(request_json)
        self.calls.append((role, payload))
        if role == 'generation':
            case = next(c for c in self.cases if c['question'] == payload['question'])
            return candidate_from(case['candidate']).model_dump_json()
        if role == 'statement':
            # Model decisions are scripted, never reported as empirical evidence.
            case = next(c for c in self.cases if c['candidate']['statement'] == payload['statement'])
            good = self.labels[case['case_id']]['statement_admissible']
            fields = {name: False for name in SemanticJudgeVerdict.model_fields if name not in ('admissible','rejection_reasons')}
            fields['insufficient_support'] = not good
            return json.dumps(dict(fields, admissible=good, rejection_reasons=[] if good else ['insufficient_support']))
        case = next(c for c in self.cases if c['question'] == payload['question'] and c['candidate']['statement'] == payload['candidate']['statement'])
        return json.dumps({'request_sha256': digest(payload), 'answers_question': self.labels[case['case_id']]['answers_question'], 'uncertain':False, 'reason':'Scripted fixture decision.'})


def execute(transport):
    cases, labels, bindings = load_inputs()
    return asyncio.run(run_rehearsal(transport=transport, configuration={'production_enabled':False}, cases=cases, labels=labels, bindings=bindings))


def test_complete_plan_keeps_real_vs_scripted_provenance_and_disabled_boundaries():
    cases, labels, _ = load_inputs()
    transport = ScriptedTransport(cases, labels)
    report = execute(transport)
    assert report['status'] == 'completed_pending_human_review'
    assert report['execution_source'] == 'unit_test'
    assert report['attempted_transport_calls'] == 44
    assert len(report['cases']) == 19
    assert report['summary']['control_statement_mismatches'] == 0
    assert report['summary']['control_relevance_mismatches'] == 0
    assert report['empirical_acceptance'] is False and report['release_authorized'] is False
    assert report['production_enabled'] is False and report['proposition_to_inference'] == 'closed'
    for role, payload in transport.calls:
        wire = json.dumps(payload)
        for forbidden in ('human_rationale', 'human_classification', 'proposed_expectation', 'rationale_origin'):
            assert forbidden not in wire
        if role == 'statement':
            assert 'question' not in payload and 'sources' not in payload


@pytest.mark.parametrize('reason', ['unavailable','refused','incomplete','malformed_response','timeout','budget_exceeded'])
def test_operational_errors_preserve_partial_evidence_and_stop_without_retry(reason):
    class Failing:
        execution_source = 'unit_test'
        calls = 0
        async def call(self, **kwargs):
            self.calls += 1
            raise GovernedTransportFailure(reason)
    transport = Failing()
    report = execute(transport)
    assert report['status'] == 'blocked'
    assert report['attempted_transport_calls'] == transport.calls == 1
    assert report['cases'][0]['error'] == reason
    assert report['cases'][0]['preview_allowed'] is False


def test_relevance_digest_mismatch_never_allows_a_preview():
    cases, labels, _ = load_inputs()
    class Mismatch(ScriptedTransport):
        async def call(self, **kwargs):
            value = await super().call(**kwargs)
            if kwargs['role'] == 'relevance':
                row = json.loads(value); row['request_sha256'] = '0'*64
                return json.dumps(row)
            return value
    report = execute(Mismatch(cases, labels))
    assert report['status'] == 'blocked' and report['cases'][0]['error'] == 'malformed_response'
    assert report['cases'][0]['preview_allowed'] is False


def test_inconsistent_judge_verdict_is_not_an_acceptance():
    case = json.loads(SemanticJudgeVerdict(admissible=True, unsupported_fact=True, certainty_inflation=False, causal_overreach=False, negation_reversal=False, fabricated_precision=False, conflict_suppression=False, unsupported_qualification=False, insufficient_support=False, rejection_reasons=()).model_dump_json())
    assert consistent(SemanticJudgeVerdict.model_validate_json(json.dumps(case))) is False


def test_duplicate_or_missing_source_coverage_is_rejected_structurally():
    cases, _, _ = load_inputs(); case = copy.deepcopy(cases[0])
    candidate = candidate_from(case['candidate'])
    assert structurally_complete(candidate, case)
    assert not structurally_complete(candidate.model_copy(update={'premise_ids':['p1','p1']}), case)
    case['sources'].append(copy.deepcopy(case['sources'][0]))
    assert not structurally_complete(candidate, case)


def test_html_escapes_model_and_source_content_and_identifies_withheld_candidates():
    cases, labels, _ = load_inputs()
    report = execute(ScriptedTransport(cases, labels))
    report['cases'][0]['candidate']['statement'] = '<script>alert("model")</script>'
    report['cases'][0]['sources'][0]['text'] = '<img src=x onerror=alert(1)>'
    rendered = render_review(report)
    assert '<script>' not in rendered and '<img src=x' not in rendered
    assert '&lt;script&gt;' in rendered and '&lt;img' in rendered
    assert 'withheld' in rendered and 'Production answering is disabled' in rendered
    assert 'Execution source: unit_test' in rendered
    assert 'actual provider review' not in rendered
    assert 'Supplied premises and relationships' in rendered


@pytest.mark.parametrize('budget', [0, 1, 43])
def test_global_call_budget_stops_without_extra_dispatch(monkeypatch, budget):
    cases, labels, _ = load_inputs()
    transport = ScriptedTransport(cases, labels)
    monkeypatch.setattr(module, 'MAX_CALLS', budget)
    report = execute(transport)
    assert report['status'] == 'blocked'
    assert len(transport.calls) == report['attempted_transport_calls'] == budget
    assert report['cases'][-1]['error'] == 'budget_exceeded'
    assert report['cases'][-1]['preview_allowed'] is False


def test_wall_budget_expiry_after_dispatch_discards_response(monkeypatch):
    cases, labels, _ = load_inputs()
    class Late(ScriptedTransport):
        async def call(self, **kwargs):
            response = await super().call(**kwargs)
            monkeypatch.setattr(module, 'time', SimpleNamespace(monotonic=lambda: 2000))
            return response
    monkeypatch.setattr(module, 'time', SimpleNamespace(monotonic=lambda: 0))
    report = execute(Late(cases, labels))
    assert report['status'] == 'blocked'
    assert report['attempted_transport_calls'] == 1
    step = report['cases'][0]['steps'][0]
    assert step['error'] == 'budget_exceeded'
    assert 'response' not in step
    assert report['cases'][0]['preview_allowed'] is False


def test_uncertain_relevance_withholds_every_candidate():
    cases, labels, _ = load_inputs()
    class Uncertain(ScriptedTransport):
        async def call(self, **kwargs):
            response = await super().call(**kwargs)
            if kwargs['role'] == 'relevance':
                value = json.loads(response)
                value.update(answers_question=True, uncertain=True)
                return json.dumps(value)
            return response
    report = execute(Uncertain(cases, labels))
    assert report['status'] == 'completed_pending_human_review'
    assert report['summary']['review_previews'] == 0
    assert report['summary']['control_relevance_mismatches'] == 13
    assert all(not row['preview_allowed'] for row in report['cases'])


@pytest.mark.parametrize('response,error', [
    ('{"admissible":true,"admissible":false}', 'malformed_response'),
    ('not-json-private-data', 'malformed_response'),
    ('"' + 'x' * 32768 + '"', 'budget_exceeded'),
    (None, 'malformed_response'),
])
def test_malformed_or_oversized_response_stops_and_never_previews(response, error):
    class Malformed:
        execution_source = 'unit_test'
        async def call(self, **kwargs):
            return response
    report = execute(Malformed())
    assert report['status'] == 'blocked'
    assert report['attempted_transport_calls'] == 1
    assert report['cases'][0]['error'] == error
    assert not report['cases'][0]['preview_allowed']


def test_modified_cases_cannot_borrow_reviewed_input_digests():
    cases, labels, bindings = load_inputs()
    cases[0]['question'] = 'An unreviewed replacement question'
    transport = ScriptedTransport(cases, labels)
    with pytest.raises(ValueError, match='frozen reviewed packet'):
        asyncio.run(run_rehearsal(transport=transport, configuration={},
                    cases=cases, labels=labels, bindings=bindings))
    assert transport.calls == []


def test_report_snapshots_context_configuration_and_exact_response_binding():
    cases, labels, bindings = load_inputs()
    original = copy.deepcopy(cases)
    configuration = {'production_enabled': False}
    class Mutating(ScriptedTransport):
        async def call(self, **kwargs):
            response = await super().call(**kwargs)
            cases[0]['sources'][0]['text'] = 'Mutated outside the request snapshot'
            configuration['production_enabled'] = True
            bindings['dataset_sha256'] = '0' * 64
            return response
    report = asyncio.run(run_rehearsal(transport=Mutating(cases, labels), configuration=configuration,
        cases=cases, labels=labels, bindings=bindings))
    assert report['cases'][0]['sources'] == original[0]['sources']
    assert report['configuration']['production_enabled'] is False
    assert report['bindings']['dataset_sha256'] == module.FROZEN_DATASET_SHA256
    for row in report['cases']:
        expected = next(case for case in original if case['case_id'] == row['case_id'])
        assert row['question'] == expected['question']
        assert row['premises'] == expected['premises']
        assert row['relationships'] == expected['relationships']
        for step in row['steps']:
            assert step['request_sha256'] == digest(step['request'])
            assert step['response_sha256'] == hashlib.sha256(step['response_json'].encode()).hexdigest()
            assert step['response'] == json.loads(step['response_json'])


def test_edited_dataset_and_forged_approval_pair_are_rejected(tmp_path, monkeypatch):
    dataset = json.loads(module.DATASET.read_text())
    review = json.loads(module.REVIEW.read_text())
    dataset['cases'][0]['question'] = 'Unreviewed source substitution'
    dataset_path, review_path = tmp_path / 'cases.json', tmp_path / 'review.json'
    dataset_path.write_text(json.dumps(dataset))
    review['dataset_sha256'] = hashlib.sha256(dataset_path.read_bytes()).hexdigest()
    review_path.write_text(json.dumps(review))
    monkeypatch.setattr(module, 'DATASET', dataset_path)
    monkeypatch.setattr(module, 'REVIEW', review_path)
    with pytest.raises(ValueError, match='Exact frozen'):
        load_inputs()


def test_blank_generated_statement_is_rejected_before_assessment_calls():
    cases, labels, _ = load_inputs()
    class Blank(ScriptedTransport):
        async def call(self, **kwargs):
            response = await super().call(**kwargs)
            if kwargs['role'] == 'generation':
                value = json.loads(response)
                value['statement'] = '  \n '
                return json.dumps(value)
            return response
    transport = Blank(cases, labels)
    report = execute(transport)
    generated = [row for row in report['cases'] if row['mode'] == 'generated_candidate']
    assert len(generated) == report['summary']['structural_rejections'] == 6
    assert all(row['status'] == 'structural_rejection' and not row['preview_allowed'] for row in generated)
    assert all([step['role'] for step in row['steps']] == ['generation'] for row in generated)
    assert report['attempted_transport_calls'] == 32


def test_private_writer_exclusive_atomic_checkpoints_and_size_bound(tmp_path):
    target = tmp_path / 'report.json'
    writer = module.PrivateReportWriter(target)
    try:
        writer.checkpoint({'status': 'running', 'attempted_transport_calls': 0})
        old_inode = target.stat().st_ino
        writer.checkpoint({'status': 'running', 'attempted_transport_calls': 1})
        assert json.loads(target.read_text())['attempted_transport_calls'] == 1
        assert target.stat().st_ino != old_inode
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        before = target.read_bytes()
        with pytest.raises(ValueError, match='checkpoint limit'):
            writer.checkpoint({'text': 'x' * module.MAX_REPORT_BYTES})
        assert target.read_bytes() == before
        with pytest.raises(FileExistsError):
            module.PrivateReportWriter(target)
    finally:
        writer.close()
    assert list(tmp_path.iterdir()) == [target]


def test_private_writer_refuses_public_parent_and_symlink(tmp_path):
    parent = tmp_path / 'public'
    parent.mkdir(mode=0o755)
    with pytest.raises(ValueError, match='Private owned'):
        module.PrivateReportWriter(parent / 'report.json')
    assert list(parent.iterdir()) == []
    original = tmp_path / 'original.json'
    original.write_bytes(b'preserve original')
    link = tmp_path / 'link.json'
    link.symlink_to(original)
    with pytest.raises(FileExistsError):
        module.PrivateReportWriter(link)
    assert original.read_bytes() == b'preserve original'


@pytest.mark.parametrize('kind', ['file', 'symlink'])
def test_observed_concurrent_target_replacement_preserves_foreign_evidence(tmp_path, monkeypatch, kind):
    target = tmp_path / 'report.json'
    writer = module.PrivateReportWriter(target)
    writer.checkpoint({'status': 'old'})
    original_guard, calls = writer._guard, []
    foreign = tmp_path / 'foreign.json'
    foreign.write_bytes(b'foreign evidence')
    def guard():
        calls.append(True)
        if len(calls) == 2:
            target.unlink()
            if kind == 'symlink':
                target.symlink_to(foreign)
            else:
                os.link(foreign, target)
        original_guard()
    monkeypatch.setattr(writer, '_guard', guard)
    try:
        with pytest.raises(ValueError, match='ownership changed'):
            writer.checkpoint({'status': 'new'})
        assert target.read_bytes() == foreign.read_bytes() == b'foreign evidence'
        assert target.is_symlink() == (kind == 'symlink')
        assert not list(tmp_path.glob('.provider-checkpoint-*'))
    finally:
        writer.close()


@pytest.mark.parametrize('failure', ['file_sync', 'replace'])
def test_prepublication_failure_preserves_prior_complete_checkpoint(tmp_path, monkeypatch, failure):
    target = tmp_path / 'report.json'
    writer = module.PrivateReportWriter(target)
    writer.checkpoint({'status': 'old'})
    prior = target.read_bytes()
    if failure == 'file_sync':
        original_fsync = module.os.fsync
        def fsync(fd):
            if stat.S_ISREG(os.fstat(fd).st_mode):
                raise OSError('private injected failure')
            return original_fsync(fd)
        monkeypatch.setattr(module.os, 'fsync', fsync)
    else:
        def replace(*args, **kwargs):
            raise OSError('private injected failure')
        monkeypatch.setattr(module.os, 'replace', replace)
    try:
        with pytest.raises(OSError):
            writer.checkpoint({'status': 'new'})
        assert target.read_bytes() == prior
        assert list(tmp_path.iterdir()) == [target]
    finally:
        writer.close()


def test_postpublication_directory_sync_failure_leaves_new_complete_json(tmp_path, monkeypatch):
    target = tmp_path / 'report.json'
    writer = module.PrivateReportWriter(target)
    writer.checkpoint({'status': 'old'})
    original_fsync = module.os.fsync
    def fsync(fd):
        if stat.S_ISDIR(os.fstat(fd).st_mode):
            raise OSError('private directory failure')
        return original_fsync(fd)
    monkeypatch.setattr(module.os, 'fsync', fsync)
    try:
        with pytest.raises(OSError):
            writer.checkpoint({'status': 'new'})
        assert json.loads(target.read_text()) == {'status': 'new'}
        assert list(tmp_path.iterdir()) == [target]
    finally:
        writer.close()


def test_cancelled_dispatch_keeps_durable_attempt_and_never_retries(tmp_path):
    target = tmp_path / 'report.json'
    writer = module.PrivateReportWriter(target)
    cases, labels, bindings = load_inputs()
    class Interrupted:
        execution_source = 'unit_test'
        calls = 0
        async def call(self, **kwargs):
            self.calls += 1
            raise asyncio.CancelledError()
    transport = Interrupted()
    try:
        with pytest.raises(asyncio.CancelledError):
            asyncio.run(run_rehearsal(transport=transport, configuration={}, cases=cases,
                labels=labels, bindings=bindings, checkpoint=writer.checkpoint))
    finally:
        writer.close()
    partial = json.loads(target.read_text())
    assert partial['status'] == 'running'
    assert partial['attempted_transport_calls'] == transport.calls == 1
    assert partial['cases'][0]['steps'][0]['status'] == 'attempted'
    assert partial['cases'][0]['preview_allowed'] is False
    assert partial['production_enabled'] is partial['empirical_acceptance'] is False


def test_checkpoint_failure_before_dispatch_prevents_paid_work():
    cases, labels, bindings = load_inputs()
    transport = ScriptedTransport(cases, labels)
    persisted = []
    def fail_before_dispatch(report):
        if report['attempted_transport_calls']:
            raise OSError('private storage failure')
        persisted.append(report)
    with pytest.raises(module.CheckpointPersistenceFailure):
        asyncio.run(run_rehearsal(transport=transport, configuration={}, cases=cases,
            labels=labels, bindings=bindings, checkpoint=fail_before_dispatch))
    assert transport.calls == []
    assert len(persisted) == 1 and persisted[0]['status'] == 'running'
    assert persisted[0]['attempted_transport_calls'] == 0


def test_every_completed_response_and_final_report_are_checkpointed():
    cases, labels, bindings = load_inputs()
    saved = []
    report = asyncio.run(run_rehearsal(transport=ScriptedTransport(cases, labels),
        configuration={}, cases=cases, labels=labels, bindings=bindings, checkpoint=saved.append))
    assert saved[0]['attempted_transport_calls'] == 0 and saved[0]['plan_sha256']
    assert saved[-1] == report
    for attempt in range(1, 45):
        states = [snapshot['cases'][-1]['steps'][-1]['status'] for snapshot in saved
                  if snapshot['attempted_transport_calls'] == attempt]
        assert states[0] == 'attempted'
        assert 'completed' in states


def test_checkpoint_failure_after_response_never_dispatches_again():
    cases, labels, bindings = load_inputs()
    transport = ScriptedTransport(cases, labels)
    saved = []
    def interrupted_persistence(report):
        if report['cases'] and report['cases'][-1]['steps'][-1]['status'] == 'completed':
            raise OSError('private storage failure')
        saved.append(report)
    with pytest.raises(module.CheckpointPersistenceFailure):
        asyncio.run(run_rehearsal(transport=transport, configuration={}, cases=cases,
            labels=labels, bindings=bindings, checkpoint=interrupted_persistence))
    assert len(transport.calls) == 1
    assert saved[-1]['cases'][0]['steps'][0]['status'] == 'attempted'
    assert saved[-1]['cases'][0]['preview_allowed'] is False


def test_cli_persists_initialization_before_constructing_clients(tmp_path, monkeypatch, capsys):
    cases, labels, _ = load_inputs()
    target = tmp_path / 'report.json'
    observed = []
    async def create_clients(**kwargs):
        initial = json.loads(target.read_text())
        assert initial['status'] == 'initializing'
        assert initial['attempted_transport_calls'] == 0
        assert stat.S_IMODE(target.stat().st_mode) == 0o600
        observed.append('constructed')
        async def close():
            observed.append('closed')
        return SimpleNamespace(transport=ScriptedTransport(cases, labels), configuration={}, close=close)
    monkeypatch.setattr(module, 'create_selected_model_clients', create_clients)
    monkeypatch.setattr(module.subprocess, 'check_output', lambda *args, **kwargs: 'scripted-commit\n')
    monkeypatch.setattr(sys, 'argv', ['rehearsal', '--execute', '--output', str(target)])
    for name in ('SEMANTIC_GENERATION_API_KEY', 'SEMANTIC_JUDGE_API_KEY', 'SEMANTIC_RELEVANCE_API_KEY'):
        monkeypatch.setenv(name, 'scripted-not-a-real-credential')
    asyncio.run(module.execute())
    assert observed == ['constructed', 'closed']
    report = json.loads(target.read_text())
    assert report['status'] == 'completed_pending_human_review'
    assert report['execution_source'] == 'unit_test'
    assert report['attempted_transport_calls'] == 44
    assert report['empirical_acceptance'] is False
    capsys.readouterr()
