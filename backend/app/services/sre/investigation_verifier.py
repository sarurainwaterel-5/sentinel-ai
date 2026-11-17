"""Independent structural policy for deterministic recommendation-only hypotheses.

This verifier establishes record/citation consistency, never causal or empirical truth.
It has no providers, tools, clock, storage access, or execution authority.
"""
from .contracts import SREError, digest, timestamp, identifier, evidence

ROOT_CAUSE_POLICY = 'CAUSAL_VERIFICATION_UNAVAILABLE_V1'

# Independent presentation allowlist prevents altered free prose passing citation checks.
_ALLOWED_DESCRIPTIONS = {
    'SERVICE_CHECK_FAILURE': 'Selected checks report impairment; the underlying cause remains unknown.',
    'DEPENDENCY_DISRUPTION': 'A dependency failure is reported alongside configured relationships; propagation is unverified.',
    'COLLECTOR_OR_EVIDENCE_GAP': 'Incomplete validation or collection may limit interpretation of the selected evidence.',
    'RECENT_CHANGE_ASSOCIATION': 'A deployment event appears in the selected timeline; causation and relevance require verification.',
}


def verify_snapshot(snapshot):
    try:
        if type(snapshot) is not dict or snapshot['schema_version'] != 1:
            raise ValueError()
        body = {k: v for k, v in snapshot.items() if k != 'snapshot_sha256'}
        if digest(body) != snapshot['snapshot_sha256']:
            raise ValueError()
        scope = snapshot['scope']
        for k in ('tenant_id', 'application_id', 'service_id'):
            identifier(scope[k])
            if snapshot['service'][k] != scope[k]:
                raise ValueError()
        at = timestamp(snapshot['evaluated_at'])
        observations = snapshot['observations']
        if type(observations) is not list or not 1 <= len(observations) <= 100:
            raise ValueError()
        ids = []
        for observation in observations:
            if any(observation[k] != scope[k] for k in scope):
                raise ValueError()
            oid = identifier(observation['observation_id']); ids.append(oid)
            evidence(observation['evidence_ref'])
            original = {k: v for k, v in observation.items()
                        if k not in ('source_data_quality', 'record_sha256', 'validation')}
            original['data_quality'] = observation['source_data_quality']
            if digest(original) != observation['record_sha256']:
                raise ValueError()
            if timestamp(observation['source_timestamp']) > at or timestamp(observation['ingested_at']) > at:
                raise ValueError()
            review = observation.get('validation')
            if observation['data_quality'] == 'VALIDATED':
                if not review or review['observation_hash'] != observation['record_sha256'] or review['observation_id'] != oid:
                    raise ValueError()
                if any(review[k] != scope[k] for k in ('tenant_id', 'application_id')):
                    raise ValueError()
                if timestamp(review['reviewed_at']) > at or timestamp(review['reviewed_at']) < timestamp(observation['ingested_at']):
                    raise ValueError()
                evidence(review['evidence_ref']); identifier(review['reviewer_id'])
            elif observation['data_quality'] not in ('SOURCE_CLAIM', 'INVALID'):
                raise ValueError()
        if len(ids) != len(set(ids)) or sorted(ids) != sorted(snapshot['selection']['observation_ids']):
            raise ValueError()
        for dependency in snapshot['dependencies']:
            if any(dependency[k] != scope[k] for k in ('tenant_id', 'application_id')):
                raise ValueError()
            evidence(dependency['evidence_ref'])
            if scope['service_id'] not in (dependency['source_service_id'], dependency['dependent_service_id']):
                raise ValueError()
        incident = snapshot.get('incident')
        if snapshot['selection']['kind'] == 'INCIDENT':
            if not incident or incident['incident_id'] != snapshot['selection']['incident_id'] or sorted(incident['initial_observation_ids']) != sorted(ids):
                raise ValueError()
            if any(incident[k] != scope[k] for k in scope):
                raise ValueError()
        elif snapshot['selection']['kind'] != 'OBSERVATIONS' or incident is not None:
            raise ValueError()
        if snapshot['health']['execution_authority'] != 'NONE':
            raise ValueError()
        return True
    except (KeyError, TypeError, ValueError, AttributeError, OverflowError):
        raise SREError('INVESTIGATION_EVIDENCE_INVALID') from None


def verify_hypotheses(snapshot, hypotheses):
    """Check independently specified predicates and all cited/contrary record IDs."""
    verify_snapshot(snapshot)
    observations = {o['observation_id']: o for o in snapshot['observations']}
    dependencies = {d['dependency_id']: d for d in snapshot['dependencies']}
    allowed = {'SERVICE_CHECK_FAILURE', 'DEPENDENCY_DISRUPTION', 'COLLECTOR_OR_EVIDENCE_GAP', 'RECENT_CHANGE_ASSOCIATION'}
    errors = []
    seen = set()
    if type(hypotheses) is not list or len(hypotheses) > 4:
        raise SREError('INVESTIGATION_VERIFICATION_FAILED')
    for hypothesis in hypotheses:
        kind = hypothesis.get('hypothesis_id')
        if kind not in allowed or kind in seen:
            errors.append('UNSUPPORTED_HYPOTHESIS'); continue
        seen.add(kind)
        if hypothesis.get('description') != _ALLOWED_DESCRIPTIONS[kind]:
            errors.append('UNSUPPORTED_CAUSAL_CLAIM')
        support = set(hypothesis.get('supporting_observation_ids', []))
        contrary = set(hypothesis.get('contradictory_observation_ids', []))
        if not support or not (support | contrary) <= observations.keys():
            errors.append('INVALID_CITATION'); continue
        if hypothesis.get('assessment_status') != 'PLAUSIBLE_NOT_CAUSALLY_VERIFIED' or 'confidence' in hypothesis or 'root_cause' in hypothesis:
            errors.append('UNSUPPORTED_CAUSAL_CLAIM')
        for oid in support:
            o = observations[oid]; payload = o['payload']; typ = o['observation_type']
            valid = (
                kind == 'SERVICE_CHECK_FAILURE' and typ == 'SERVICE_HEALTH' and payload['outcome'] in ('FAIL', 'PARTIAL') or
                kind == 'DEPENDENCY_DISRUPTION' and typ == 'DEPENDENCY_FAILURE' and bool(hypothesis.get('dependency_ids')) or
                kind == 'COLLECTOR_OR_EVIDENCE_GAP' and (o['data_quality'] != 'VALIDATED' or typ == 'SERVICE_HEALTH' and payload['outcome'] == 'COLLECTOR_ERROR') or
                kind == 'RECENT_CHANGE_ASSOCIATION' and typ == 'DEPLOYMENT_EVENT'
            )
            if not valid:
                errors.append('IRRELEVANT_SUPPORT')
        expected_contrary = {oid for oid, o in observations.items()
                            if o['observation_type'] == 'SERVICE_HEALTH' and o['payload']['outcome'] == 'PASS'} if kind in ('SERVICE_CHECK_FAILURE', 'DEPENDENCY_DISRUPTION') else set()
        if contrary != expected_contrary:
            errors.append('CONTRADICTIONS_OMITTED')
        if any(d not in dependencies for d in hypothesis.get('dependency_ids', [])):
            errors.append('DEPENDENCY_CITATION_INVALID')
        if not hypothesis.get('missing_evidence') or not hypothesis.get('suggested_verification_steps'):
            errors.append('UNCERTAINTY_OMITTED')
    return {'status': 'VERIFIED_STRUCTURAL_POLICY' if not errors else 'WITHHELD',
            'errors': sorted(set(errors)), 'root_cause_policy': ROOT_CAUSE_POLICY,
            'semantic_accuracy': 'NOT_ESTABLISHED', 'independent_process': 'SEPARATE_DETERMINISTIC_POLICY_NOT_INDEPENDENT_MODEL'}
