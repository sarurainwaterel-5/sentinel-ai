"""Bounded, explicit, offline incident evidence investigation; never remediation."""
from time import monotonic
from .contracts import SREError, digest
from .investigation_verifier import verify_snapshot, verify_hypotheses, ROOT_CAUSE_POLICY
from . import GOVERNANCE


_DESCRIPTIONS = {
    'SERVICE_CHECK_FAILURE': 'Selected checks report impairment; the underlying cause remains unknown.',
    'DEPENDENCY_DISRUPTION': 'A dependency failure is reported alongside configured relationships; propagation is unverified.',
    'COLLECTOR_OR_EVIDENCE_GAP': 'Incomplete validation or collection may limit interpretation of the selected evidence.',
    'RECENT_CHANGE_ASSOCIATION': 'A deployment event appears in the selected timeline; causation and relevance require verification.',
}


def _generate(snapshot):
    observations = snapshot['observations']
    support = {kind: [] for kind in _DESCRIPTIONS}
    passes = []
    for o in observations:
        oid = o['observation_id']; typ = o['observation_type']; payload = o['payload']
        if typ == 'SERVICE_HEALTH':
            if payload['outcome'] in ('FAIL', 'PARTIAL'):
                support['SERVICE_CHECK_FAILURE'].append(oid)
            if payload['outcome'] == 'PASS':
                passes.append(oid)
        if typ == 'DEPENDENCY_FAILURE' and snapshot['dependencies']:
            support['DEPENDENCY_DISRUPTION'].append(oid)
        if o['data_quality'] != 'VALIDATED' or typ == 'SERVICE_HEALTH' and payload['outcome'] == 'COLLECTOR_ERROR':
            support['COLLECTOR_OR_EVIDENCE_GAP'].append(oid)
        if typ == 'DEPLOYMENT_EVENT':
            support['RECENT_CHANGE_ASSOCIATION'].append(oid)
    result = []
    for kind, ids in support.items():
        if not ids:
            continue
        result.append({'hypothesis_id': kind, 'description': _DESCRIPTIONS[kind],
                       'supporting_observation_ids': sorted(ids),
                       'contradictory_observation_ids': sorted(passes) if kind in ('SERVICE_CHECK_FAILURE', 'DEPENDENCY_DISRUPTION') else [],
                       'dependency_ids': sorted(d['dependency_id'] for d in snapshot['dependencies']) if kind == 'DEPENDENCY_DISRUPTION' else [],
                       'missing_evidence': ['Independent diagnostic evidence establishing or excluding the proposed mechanism.'],
                       'suggested_verification_steps': ['Request authorized diagnostics; compare timestamps, check semantics and contradictory observations.'],
                       'assessment_status': 'PLAUSIBLE_NOT_CAUSALLY_VERIFIED'})
    return result


def run_investigation(store, access, tenant, application, service_id, *, evaluated_at,
                      observation_ids=None, incident_id=None, cancelled=None,
                      max_observations=100, max_dependencies=128, timeout_seconds=5,
                      clock=monotonic):
    """Explicit read-only compatibility pipeline, current authorization at publication.

    Finite local computations check cancellation/time at stage boundaries. No model
    tasks or partial report are released. The trusted store supplies one atomic,
    audited-integrity snapshot; canonical hashes bind bytes, not semantic truth.
    """
    if type(timeout_seconds) not in (int, float) or not 0 < timeout_seconds <= 30:
        raise SREError('INVESTIGATION_BUDGET')
    if type(max_observations) is not int or not 1 <= max_observations <= 100 or type(max_dependencies) is not int or not 0 <= max_dependencies <= 128:
        raise SREError('INVESTIGATION_BUDGET')
    if cancelled is not None and not callable(cancelled):
        raise SREError('INVALID_CANCELLATION')
    start = clock()

    def checkpoint():
        if cancelled is not None and cancelled():
            raise SREError('INVESTIGATION_CANCELLED')
        if clock() - start >= timeout_seconds:
            raise SREError('INVESTIGATION_TIMEOUT')
        store.authorizer.check(access, tenant, application, 'read')

    checkpoint()
    snapshot = store.investigation_snapshot(access, tenant, application, service_id,
                  evaluated_at=evaluated_at, observation_ids=observation_ids, incident_id=incident_id,
                  max_observations=max_observations, max_dependencies=max_dependencies)
    checkpoint(); verify_snapshot(snapshot)
    hypotheses = _generate(snapshot)
    checkpoint()
    verification = verify_hypotheses(snapshot, hypotheses)
    if verification['status'] != 'VERIFIED_STRUCTURAL_POLICY':
        raise SREError('INVESTIGATION_VERIFICATION_FAILED')
    observations = snapshot['observations']
    inventory = [{'observation_id': o['observation_id'], 'record_sha256': o['record_sha256'],
                  'evidence_ref': o['evidence_ref'], 'source_id': o['source_id'],
                  'data_quality': o['data_quality'], 'validation': o.get('validation'),
                  'semantic_truth': 'NOT_ESTABLISHED'} for o in observations]
    timeline = sorted([{'observation_id': o['observation_id'], 'source_timestamp': o['source_timestamp'],
                        'ingested_at': o['ingested_at'], 'observation_type': o['observation_type'],
                        'correlation_id': o['correlation_id']} for o in observations],
                       key=lambda o: (o['source_timestamp'], o['observation_id']))
    correlations = []
    for cid in sorted({o['correlation_id'] for o in observations}):
        ids = sorted(o['observation_id'] for o in observations if o['correlation_id'] == cid)
        if len(ids) > 1:
            correlations.append({'relationship': 'SHARED_SOURCE_CORRELATION_ID', 'correlation_id': cid,
                                 'observation_ids': ids, 'causal_status': 'NOT_ESTABLISHED'})
    report = {'schema_version': 1, 'scope': snapshot['scope'], 'selection': snapshot['selection'],
              'evaluated_at': snapshot['evaluated_at'], 'affected_service': service_id,
              'incident_summary': 'Explicit selected evidence reviewed; no incident declaration or causal conclusion.',
              'snapshot_sha256': snapshot['snapshot_sha256'], 'audit_head': snapshot['audit_head'],
              'health': snapshot['health'], 'timeline': timeline, 'evidence_inventory': inventory,
              'dependencies': snapshot['dependencies'], 'correlations': correlations,
              'hypotheses': hypotheses, 'verification': verification,
              'verified_findings': [{'kind': 'RECORD_BINDING', 'observation_ids': sorted(o['observation_id'] for o in observations),
                                     'statement': 'Selected records and review references passed structural consistency checks; semantic truth is not established.'}],
              'unresolved_questions': ['What underlying mechanism explains the observations?', 'Are selected source claims accurate and sufficient?'],
              'recommended_next_diagnostic_steps': ['Request independently reviewed, authorized diagnostics for the selected service.',
                                                     'Review missing evidence and contradictory observations before choosing any response.'],
              'root_cause': {'status': 'WITHHELD', 'verification_policy': ROOT_CAUSE_POLICY},
              'roles': ['Observer', 'Investigator', 'Verifier', 'Supervisor'],
              'execution_authority': 'NONE', 'governance': {**GOVERNANCE, 'MODE': 'RECOMMENDATION_ONLY', 'ADR_037': 'PROPOSED', 'EMPIRICAL_SEMANTIC_ACCEPTANCE': 'NOT_ESTABLISHED'}}
    checkpoint()
    return {**report, 'report_sha256': digest(report)}
