"""Explicit bounded real-provider rehearsal; never an answer route or release gate.

Uses only the existing reviewed synthetic sources. Actual transport outputs stay
separate from frozen unit_test coordinators. Human acceptance remains unset.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import html
import json
import os
from pathlib import Path
import subprocess
import secrets
import stat
import time

from app.services.providers.openai_governed_transport import (
    GenerationPayload, GovernedTransportFailure, _bounded_json,
)
from app.services.providers.selected_model_configuration import create_selected_model_clients
from app.services.cognition.reasoning.semantic_admissibility_provider import (
    SemanticAdmissibilityRequest, SemanticPremiseText, SemanticRelationshipText,
    SemanticJudgeVerdict,
)
from .presentation_guard import RelevanceVerdict

ROOT = Path(__file__).resolve().parents[3]
DATASET = ROOT / 'backend/evaluation/governed_answers/answer_cases.proposed.json'
REVIEW = ROOT / 'backend/evaluation/governed_answers/answer_review.human.approved.json'
MAX_CALLS = 44
MAX_SECONDS = 1500
MAX_REPORT_BYTES = 4 * 1024 * 1024
FROZEN_DATASET_SHA256 = 'd5a4391d5108e14894fec3158261d9a91600e5b7b28695138388e29218891ba9'
FROZEN_REVIEW_SHA256 = '3394b69158b48e0b28db4b25017c64add583f1df8a0ffc6af99edd0ee7337e23'


class CheckpointPersistenceFailure(Exception):
    """A checkpoint failure stops dispatch; never retry a possibly paid call."""


class PrivateReportWriter:
    """Exclusive reservation and atomic, bounded, durable JSON checkpoints.

    The parent must be private mode0700 and owned by this UID. Observed inode,
    mode, owner or symlink changes refuse replacement. The directory owner is
    trusted: POSIX stat+replace cannot prevent an arbitrary same-UID actor from
    racing between the final inode check and rename. Directory fsync failure
    after rename raises but leaves the newly published complete JSON intact.
    """
    def __init__(self, target):
        target = Path(target)
        if not target.is_absolute() or target.name in ('', '.', '..'):
            raise ValueError('Absolute private report path required.')
        if ROOT == target.resolve() or ROOT in target.resolve().parents:
            raise ValueError('Report must stay outside repository.')
        self.target, self._closed = target, False
        self._directory = os.open(target.parent, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            parent = os.fstat(self._directory)
            if stat.S_IMODE(parent.st_mode) != 0o700 or parent.st_uid != os.geteuid():
                raise ValueError('Private owned report directory required.')
            self._parent_identity = (parent.st_dev, parent.st_ino)
            fd = os.open(target.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self._directory)
            try:
                info = os.fstat(fd)
                self._owned_identity = (info.st_dev, info.st_ino)
                if stat.S_IMODE(info.st_mode) != 0o600:
                    raise ValueError('Private report permissions required.')
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(self._directory)
        except BaseException:
            os.close(self._directory)
            self._closed = True
            raise

    def _guard(self):
        if self._closed:
            raise ValueError('Report writer is closed.')
        parent = os.stat(self.target.parent, follow_symlinks=False)
        info = os.stat(self.target.name, dir_fd=self._directory, follow_symlinks=False)
        if ((parent.st_dev, parent.st_ino) != self._parent_identity
                or not stat.S_ISDIR(parent.st_mode) or stat.S_IMODE(parent.st_mode) != 0o700
                or parent.st_uid != os.geteuid() or not stat.S_ISREG(info.st_mode)
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.geteuid()
                or (info.st_dev, info.st_ino) != self._owned_identity):
            raise ValueError('Report ownership changed.')

    def checkpoint(self, report):
        data = (canonical(report) + '\n').encode('utf-8')
        if len(data) > MAX_REPORT_BYTES:
            raise ValueError('Report exceeds checkpoint limit.')
        self._guard()
        temporary = '.provider-checkpoint-' + secrets.token_hex(16) + '.tmp'
        temporary_identity = None
        try:
            fd = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=self._directory)
            with os.fdopen(fd, 'wb') as output:
                info = os.fstat(output.fileno())
                temporary_identity = (info.st_dev, info.st_ino)
                if stat.S_IMODE(info.st_mode) != 0o600 or info.st_uid != os.geteuid():
                    raise ValueError('Private checkpoint permissions required.')
                output.write(data)
                output.flush()
                os.fsync(output.fileno())
            self._guard()
            temp_info = os.stat(temporary, dir_fd=self._directory, follow_symlinks=False)
            if not stat.S_ISREG(temp_info.st_mode) or (temp_info.st_dev, temp_info.st_ino) != temporary_identity:
                raise ValueError('Checkpoint ownership changed.')
            os.replace(temporary, self.target.name, src_dir_fd=self._directory, dst_dir_fd=self._directory)
            self._owned_identity = temporary_identity
            temporary_identity = None
            os.fsync(self._directory)
        finally:
            if temporary_identity is not None:
                try:
                    info = os.stat(temporary, dir_fd=self._directory, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    if stat.S_ISREG(info.st_mode) and (info.st_dev, info.st_ino) == temporary_identity:
                        os.unlink(temporary, dir_fd=self._directory)

    def close(self):
        if not self._closed:
            os.close(self._directory)
            self._closed = True


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def load_inputs():
    with DATASET.open('rb') as source:
        dataset_bytes = source.read(1024 * 1024 + 1)
    with REVIEW.open('rb') as source:
        review_bytes = source.read(1024 * 1024 + 1)
    if (len(dataset_bytes) > 1024 * 1024 or len(review_bytes) > 1024 * 1024
            or hashlib.sha256(dataset_bytes).hexdigest() != FROZEN_DATASET_SHA256
            or hashlib.sha256(review_bytes).hexdigest() != FROZEN_REVIEW_SHA256):
        raise ValueError('Exact frozen reviewed synthetic packet required.')
    dataset = _bounded_json(dataset_bytes.decode())
    review = _bounded_json(review_bytes.decode())
    expected = hashlib.sha256(dataset_bytes).hexdigest()
    cases = dataset['cases']
    labels = {row['case_id']: row for row in review['case_reviews']}
    ids = [case['case_id'] for case in cases]
    if (review.get('approved') is not True or not review.get('reviewer')
            or review.get('dataset_sha256') != expected or len(cases) != 13
            or len(set(ids)) != len(ids) or len(review['case_reviews']) != 13
            or len(labels) != 13 or set(labels) != set(ids)
            or any(type(labels[c][key]) is not bool for c in ids
                   for key in ('statement_admissible', 'answers_question'))):
        raise ValueError('Complete hash-bound approved input review required.')
    return cases, labels, {'dataset_sha256': expected,
                          'review_sha256': hashlib.sha256(review_bytes).hexdigest()}


def candidate_from(value):
    return GenerationPayload.model_validate_json(canonical({
        field: value[field] for field in GenerationPayload.model_fields}), strict=True)


def structurally_complete(candidate, case):
    premise_ids = [row['premise_id'] for row in case['premises']]
    evidence_ids = {row['evidence_id'] for row in case['sources']}
    covered = {item for row in case['premises'] for item in row['evidence_ids']}
    refs = [(r.source_premise_id, r.target_premise_id, r.kind.value)
            for r in candidate.relationship_references]
    expected = [(r['source_premise_id'], r['target_premise_id'], r['kind'])
                for r in case['relationships']]
    return (bool(candidate.statement.strip())
            and len(set(premise_ids)) == len(premise_ids)
            and len(set(candidate.premise_ids)) == len(candidate.premise_ids)
            and set(candidate.premise_ids) == set(premise_ids)
            and covered == evidence_ids and len(evidence_ids) == len(case['sources'])
            and len(refs) == len(set(refs)) and sorted(refs) == sorted(expected))


def consistent(verdict):
    defects = {key for key in SemanticJudgeVerdict.model_fields
               if key not in ('admissible', 'rejection_reasons') and getattr(verdict, key)}
    return (verdict.admissible == (not defects)
            and set(verdict.rejection_reasons) == defects
            and len(verdict.rejection_reasons) == len(defects))


async def run_rehearsal(*, transport, configuration, cases, labels, bindings, checkpoint=None):
    # Retain exact entry inputs across awaits, and do not let a caller attach
    # frozen-file digests to a modified case set or modified human labels.
    cases, labels, bindings, configuration = (_bounded_json(canonical(value))
        for value in (cases, labels, bindings, configuration))
    reviewed_cases, reviewed_labels, reviewed_bindings = load_inputs()
    if (canonical(cases) != canonical(reviewed_cases) or canonical(labels) != canonical(reviewed_labels)
            or any(bindings.get(key) != value for key, value in reviewed_bindings.items())):
        raise ValueError('Run inputs must match the frozen reviewed packet.')
    started = time.monotonic()
    report = {'version': 'sprint21-real-provider-rehearsal-v1',
              'started_at': datetime.now(timezone.utc).isoformat(),
              'execution_source': transport.execution_source,
              'configuration': configuration, 'bindings': bindings,
              'limits': {'transport_calls': MAX_CALLS, 'wall_seconds': MAX_SECONDS,
                         'per_call_seconds': 30, 'max_output_tokens_per_call': 4096,
                         'sdk_retries': 0},
              'attempted_transport_calls': 0, 'cases': [], 'status': 'running',
              'empirical_acceptance': False, 'production_enabled': False,
              'release_authorized': False, 'semantic_grounding_verified': False,
              'proposition_to_inference': 'closed', 'execution_authenticated': False,
              'limitation': 'Reviewed synthetic sources only; no production retrieval, source-truth proof, full-context certification or human release acceptance.'}
    generated = [case for case in cases if labels[case['case_id']]['statement_admissible']
                 and labels[case['case_id']]['answers_question']]
    if len(cases) != 13 or len(generated) != 6:
        raise ValueError('Expected reviewed thirteen controls and six positive generation cases.')
    plan = [(case, 'reviewed_control') for case in cases] + [(case, 'generated_candidate') for case in generated]
    report['plan'] = [{'case_id': c['case_id'], 'mode': mode} for c, mode in plan]
    report['plan_sha256'] = digest(report['plan'])

    def persist():
        if checkpoint is not None:
            try:
                checkpoint(_bounded_json(canonical(report)))
            except Exception:
                raise CheckpointPersistenceFailure('Provider evidence checkpoint failed; dispatch stopped.') from None

    persist()

    async def dispatch(role, payload, row):
        if report['attempted_transport_calls'] >= MAX_CALLS or time.monotonic() - started >= MAX_SECONDS:
            raise GovernedTransportFailure('budget_exceeded')
        request_json = canonical(payload)
        if len(request_json.encode('utf-8')) > 65536:
            raise GovernedTransportFailure('budget_exceeded')
        report['attempted_transport_calls'] += 1
        step = {'role': role, 'request_sha256': hashlib.sha256(request_json.encode()).hexdigest(), 'status': 'attempted'}
        row['steps'].append(step)
        persist()
        try:
            response = await asyncio.wait_for(transport.call(role=role, request_json=request_json), timeout=30)
            if time.monotonic() - started >= MAX_SECONDS:
                raise GovernedTransportFailure('budget_exceeded')
            if type(response) is not str:
                raise GovernedTransportFailure('malformed_response')
            if len(response.encode('utf-8')) > 32768:
                raise GovernedTransportFailure('budget_exceeded')
            value = _bounded_json(response)
            step.update(status='completed', request=_bounded_json(request_json),
                        response=value, response_json=response,
                        response_sha256=hashlib.sha256(response.encode()).hexdigest())
            persist()
            return response
        except CheckpointPersistenceFailure:
            raise
        except asyncio.TimeoutError:
            step.update(status='blocked', error='timeout')
            persist()
            raise GovernedTransportFailure('timeout') from None
        except GovernedTransportFailure as exc:
            step.update(status='blocked', error=exc.reason)
            persist()
            raise
        except Exception:
            step.update(status='blocked', error='malformed_response')
            persist()
            raise GovernedTransportFailure('malformed_response') from None

    for case, mode in plan:
        row = {'case_id': case['case_id'], 'category': case['category'], 'mode': mode,
               'question': case['question'], 'sources': case['sources'],
               'premises': case['premises'], 'relationships': case['relationships'], 'steps': [],
               'status': 'running', 'preview_allowed': False, 'production_enabled': False}
        report['cases'].append(row)
        try:
            if mode == 'reviewed_control':
                candidate = candidate_from(case['candidate'])
            else:
                raw = await dispatch('generation', {'question': case['question'], 'sources': case['sources'],
                    'premises': case['premises'], 'relationships': case['relationships']}, row)
                candidate = GenerationPayload.model_validate_json(raw, strict=True)
            row['candidate'] = candidate.model_dump(mode='json')
            row['structural_status'] = 'passed' if structurally_complete(candidate, case) else 'rejected'
            if row['structural_status'] != 'passed':
                row['status'] = 'structural_rejection'
                persist()
                continue
            request = SemanticAdmissibilityRequest(statement=candidate.statement,
                qualifications=tuple(candidate.qualifications),
                premises=tuple(SemanticPremiseText(premise_id=p['premise_id'], statement=p['statement']) for p in case['premises']),
                relationships=tuple(SemanticRelationshipText(**{key:r[key] for key in SemanticRelationshipText.model_fields}) for r in case['relationships']))
            raw = await dispatch('statement', request.model_dump(mode='json'), row)
            statement = SemanticJudgeVerdict.model_validate_json(raw, strict=True)
            if not consistent(statement):
                raise GovernedTransportFailure('malformed_response')
            context = {'question': case['question'], 'sources': case['sources'],
                       'premises': case['premises'], 'relationships': case['relationships'],
                       'candidate': candidate.model_dump(mode='json')}
            raw = await dispatch('relevance', context, row)
            relevance = RelevanceVerdict.model_validate_json(raw, strict=True)
            if relevance.request_sha256 != digest(context):
                raise GovernedTransportFailure('malformed_response')
            row['preview_allowed'] = statement.admissible and relevance.answers_question and not relevance.uncertain
            row['status'] = 'review_preview' if row['preview_allowed'] else 'withheld'
            if mode == 'reviewed_control':
                row['comparison'] = {'expected_statement_admissible': labels[case['case_id']]['statement_admissible'],
                    'expected_answers_question': labels[case['case_id']]['answers_question'],
                    'statement_matches': statement.admissible == labels[case['case_id']]['statement_admissible'],
                    'relevance_matches': relevance.answers_question == labels[case['case_id']]['answers_question'] and not relevance.uncertain}
            persist()
        except CheckpointPersistenceFailure:
            raise
        except GovernedTransportFailure as exc:
            row.update(status='operational_failure', error=exc.reason)
            report['status'] = 'blocked'
            persist()
            break
        except Exception:
            row.update(status='operational_failure', error='malformed_response')
            report['status'] = 'blocked'
            persist()
            break
    if report['status'] == 'running':
        report['status'] = 'completed_pending_human_review'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['summary'] = {'planned_cases': len(plan), 'recorded_cases': len(report['cases']),
        'operational_failures': sum(r['status'] == 'operational_failure' for r in report['cases']),
        'structural_rejections': sum(r['status'] == 'structural_rejection' for r in report['cases']),
        'review_previews': sum(r['preview_allowed'] for r in report['cases']),
        'control_statement_mismatches': sum(not r['comparison']['statement_matches'] for r in report['cases'] if 'comparison' in r),
        'control_relevance_mismatches': sum(not r['comparison']['relevance_matches'] for r in report['cases'] if 'comparison' in r)}
    persist()
    return report


def render_review(report):
    """Exact escaped model wording with original quotes, never executable model HTML."""
    escape = lambda value: html.escape(str(value), quote=True)
    sections = []
    for row in report['cases']:
        candidate = row.get('candidate', {})
        sources = ''.join('<li><b>'+escape(s['evidence_id'])+'</b>: '+escape(s['text'])+'</li>' for s in row['sources'])
        qualifications = ''.join('<li>'+escape(q)+'</li>' for q in candidate.get('qualifications', []))
        context = {'premises': row['premises'], 'relationships': row['relationships']}
        sections.append('<section><h2>'+escape(row['case_id'])+' · '+escape(row['mode'])+'</h2><p><b>Question:</b> '+escape(row['question'])+'</p><p><b>Status:</b> '+escape(row['status'])+'</p><h3>Exact candidate for review</h3><p>'+escape(candidate.get('statement', 'No candidate returned.'))+'</p><ul>'+qualifications+'</ul><h3>Complete supplied sources</h3><ul>'+sources+'</ul><h3>Supplied premises and relationships</h3><pre>'+escape(json.dumps(context, indent=2, ensure_ascii=False))+'</pre><details><summary>Assessment evidence</summary><pre>'+escape(json.dumps(row['steps'], indent=2, ensure_ascii=False))+'</pre></details></section>')
    return '<!doctype html><html lang="en"><meta charset="utf-8"><title>Sprint 21 provider review</title><style>body{font:17px/1.5 system-ui;max-width:1000px;margin:40px auto;padding:20px}section{border-top:2px solid #aaa;margin-top:30px}pre{white-space:pre-wrap;overflow-wrap:anywhere}</style><h1>Sprint 21 — provider review</h1><p>Execution source: '+escape(report['execution_source'])+'</p><p>Private review artifact. Production answering is disabled. Candidate wording may be wrong, unsupported or withheld; showing it here does not approve it.</p><p>Report SHA-256: '+escape(digest(report))+'</p><pre>'+escape(json.dumps(report['summary'], indent=2))+'</pre>'+''.join(sections)+'</html>'


async def execute():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--execute', action='store_true', help='Explicitly perform up to 44 actual API transport calls.')
    args = parser.parse_args()
    if not args.execute:
        parser.error('--execute is required; this is not an offline fixture run')
    cases, labels, bindings = load_inputs()
    # Explicit role names only: never inherit the general application key.
    names = ('SEMANTIC_GENERATION_API_KEY', 'SEMANTIC_JUDGE_API_KEY', 'SEMANTIC_RELEVANCE_API_KEY')
    credentials = {name: os.getenv(name) for name in names}
    if not all(credentials.values()):
        parser.error('Explicit generation, judge and relevance credentials are required.')
    target = args.output
    if not target.is_absolute() or not target.parent.is_dir() or target.exists() or target.is_symlink():
        parser.error('Output must be a new absolute private file in an existing directory.')
    if ROOT == target.resolve() or ROOT in target.resolve().parents:
        parser.error('Provider outputs must stay outside the repository.')
    # Reserve and persist an initialization record before clients or paid work.
    writer = PrivateReportWriter(target)
    clients = None
    try:
        writer.checkpoint({'version': 'sprint21-real-provider-rehearsal-v1',
            'status': 'initializing', 'attempted_transport_calls': 0,
            'empirical_acceptance': False, 'production_enabled': False,
            'release_authorized': False, 'proposition_to_inference': 'closed'})
        clients = await create_selected_model_clients(credentials=credentials)
        bindings['implementation_commit'] = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip()
        bindings['rehearsal_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        report = await run_rehearsal(transport=clients.transport, configuration=clients.configuration,
            cases=cases, labels=labels, bindings=bindings, checkpoint=writer.checkpoint)
        print(json.dumps({'status':report['status'], 'summary':report['summary'],
                          'attempted_transport_calls':report['attempted_transport_calls']}))
    finally:
        writer.close()
        if clients is not None:
            await clients.close()


if __name__ == '__main__':
    asyncio.run(execute())
