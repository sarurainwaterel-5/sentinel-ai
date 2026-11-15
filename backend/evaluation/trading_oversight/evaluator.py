"""Pure consistency assessment. Never an authorization or an independent risk engine."""
from .contracts import Snapshot, Scope, Policy, digest, utc_time

AUTHORITY = {'advisory_only': True, 'execution_authorized': False, 'live_authorized': False}
CHECKER_VERSION = 'sentinel.offline.paper-oversight.v0.1'


def assess_snapshot(snapshot: Snapshot, *, expected_scope: dict, expected_policy_hashes: dict, now: str) -> dict:
    scope = Scope.model_validate(expected_scope).model_dump()
    policies = Policy.model_validate(expected_policy_hashes).model_dump()
    current = utc_time(now)
    # Re-parse instead of trusting a construct()/mutated Pydantic instance.
    from .contracts import parse_snapshot, canonical
    s = parse_snapshot(canonical(snapshot.model_dump(mode='json')).encode()).model_dump(mode='json')
    findings = []
    def add(code, severity, observation, evidence=None, missing=None):
        findings.append({'code': code, 'severity': severity, 'observation': observation,
                         'evidence': evidence or [], 'missing_evidence': missing or [],
                         'human_next_step': 'Inspect the existing paper platform and resolve the indicated evidence limitation.',
                         'limitation': 'Offline advisory; no provider authentication, strategy approval or account authorization.'})
    input_hash = digest(s)
    payload = {k: v for k, v in s.items() if k != 'payload_sha256'}
    integrity = 'SELF_CONSISTENT_UNANCHORED'
    if digest(payload) != s['payload_sha256']:
        add('PAYLOAD_HASH_MISMATCH', 'CRITICAL', 'Payload digest differs from declared content.')
        integrity = 'INVALID'
    if s['scope'] != scope:
        add('ACCOUNT_SCOPE_MISMATCH', 'CRITICAL', 'Snapshot scope differs from separately supplied expected scope.')
    if s['policy_binding'] != policies:
        add('POLICY_HASH_MISMATCH', 'CRITICAL', 'Policy identities differ from independently supplied expectations.')
    binding = s['state_binding']
    previous, sequence = binding['prior_head'], binding['prior_sequence']
    audit_bad = False
    last_time = None
    for e in s['audit']['events']:
        base = {k: v for k, v in e.items() if k != 'hash'}
        event_time = utc_time(e['timestamp'])
        if e['sequence'] != sequence + 1 or e['previousHash'] != previous or digest(base) != e['hash']:
            audit_bad = True
        if last_time is not None and event_time < last_time:
            audit_bad = True
        if event_time > utc_time(s['clock']['source_as_of']):
            audit_bad = True
        # Account/epoch identifiers in audit payload must agree, when provided.
        for key, expected in [('account_id', scope['account_id']), ('organization_id', scope['organization_id']), ('observation_epoch', binding['observation_epoch']), ('account_revision', binding['account_revision'])]:
            if key in e['payload'] and e['payload'][key] != expected:
                audit_bad = True
        previous, sequence, last_time = e['hash'], e['sequence'], event_time
    if sequence != binding['latest_sequence'] or previous != binding['latest_head']:
        audit_bad = True
    if s['audit']['continuity'] == 'GENESIS' and (binding['prior_sequence'] != 0 or binding['prior_head'] != '0' * 64):
        audit_bad = True
    if s['completeness']['full_source_chain'] and s['audit']['continuity'] != 'GENESIS':
        audit_bad = True
    if audit_bad:
        integrity = 'INVALID'
        add('AUDIT_CHAIN_INVALID', 'CRITICAL', 'Audit ordering, hashes, scope or terminal checkpoint is inconsistent.')
    if s['audit']['continuity'] != 'GENESIS':
        add('AUDIT_CHECKPOINT_UNANCHORED', 'WARNING', 'No separately trusted prior checkpoint is available.')
    c = s['clock']
    chronological = (utc_time(c['coverage_start']) <= utc_time(c['coverage_end']) <= utc_time(c['source_as_of']) <= utc_time(c['created_at']) <= utc_time(c['received_at']) <= current)
    if not chronological or utc_time(s['account_state']['as_of']) > utc_time(c['source_as_of']):
        add('CHRONOLOGY_INVALID', 'CRITICAL', 'Coverage, source, receipt, account or evaluation clocks contradict.')
    domain_matches = {'synthetic': 'SYNTHETIC', 'historical-replay': 'REPLAY', 'paper-ledger': 'WALL'}
    if c['domain'] != domain_matches[s['provenance']['kind']]:
        add('CLOCK_PROVENANCE_MISMATCH', 'CRITICAL', 'Replay/synthetic/wall clock and provenance disagree.')
    if (current - utc_time(c['source_as_of'])).total_seconds() > 60:
        add('SNAPSHOT_STALE', 'WARNING', 'Source snapshot is older than the offline 60-second observation convention; this is not the risk quote rule.')
    quote = c['quote_as_of']
    if quote is None or not 0 <= (utc_time(c['source_as_of']) - utc_time(quote)).total_seconds() <= 2:
        add('QUOTE_FRESHNESS_UNVERIFIED', 'WARNING', 'No quote at or within two seconds before source-as-of is supplied; live freshness is never established.')
    a = s['account_state']
    if (utc_time(c['source_as_of']) - utc_time(a['as_of'])).total_seconds() > 60:
        add('ACCOUNT_STATE_STALE', 'WARNING', 'Account-state observation predates source-as-of by more than the offline freshness convention.')
    if s['source']['dirty']:
        add('SOURCE_BUILD_UNVERIFIED', 'WARNING', 'Source declares a dirty baseline; its commit does not establish an exact deployed build.')
    if a['position_status'] == 'UNKNOWN' or any(a[x] is None for x in ('pending_orders', 'reservations', 'session_entries', 'realized_pnl_cents', 'kill_active', 'frozen')):
        add('EXPOSURE_UNKNOWN', 'CRITICAL', 'Position or account-control completeness is unknown; unknown is not flat.')
    if a['protection'] != 'CLAIMED_PRESENT':
        add('PROTECTION_UNVERIFIED', 'WARNING', 'Protective-order evidence is missing or unverified.')
    if a['kill_active'] or a['frozen']:
        add('PLATFORM_ENTRY_LOCK', 'WARNING', 'Snapshot reports an existing kill/frozen control.')
    if s['readiness']['reconciliation'] != 'RECONCILED':
        add('RECONCILIATION_REQUIRED', 'CRITICAL', 'The supplied account is not explicitly reconciled.')
    if s['completeness']['omitted_sections'] or s['completeness']['truncated'] or not s['completeness']['full_source_chain']:
        add('INCOMPLETE_EVIDENCE', 'WARNING', 'Snapshot explicitly lacks complete evidence coverage.')
    ids = [p['candidate_id'] for p in s['proposals']]
    if len(ids) != len(set(ids)):
        add('DUPLICATE_PROPOSAL', 'CRITICAL', 'Proposal IDs conflict within the snapshot.')
    invalid_geometry = []
    for p in s['proposals']:
        geometry = p['stop_ticks'] < p['entry_ticks'] < p['target_ticks'] if p['direction'] == 'long' else p['target_ticks'] < p['entry_ticks'] < p['stop_ticks']
        if not geometry:
            invalid_geometry.append(p['candidate_sha256'])
    if invalid_geometry:
        add('PROPOSAL_GEOMETRY_INVALID', 'CRITICAL', 'Supplied integer tick geometry contradicts direction.', invalid_geometry)
    add('SOURCE_AUTHENTICITY_UNVERIFIED', 'WARNING', 'Operator-supplied hashes establish consistency only; platform/provider origin is unverified.')
    add('CONTEXT_AND_CANDIDATE_HASHES_UNVERIFIED', 'WARNING', 'Context and candidate digests are opaque source claims; complete original objects are absent and cannot be recomputed.')
    add('STRATEGY_UNVERIFIED', 'WARNING', 'Strategy was not independently reconstructed from complete pinned causal inputs.')
    add('ACCOUNT_RISK_UNVERIFIED', 'WARNING', 'No independently attested account risk configuration, instrument economics or risk authorization is supplied. Research defaults are not account facts.')
    add('IMAF_DEFINITIONS_UNAPPROVED', 'BLOCKER', 'Entries remain locked pending operational definitions; no assessment can approve a trade.', missing=s['readiness']['open_definition_ids'])
    base = {'schema_version': 'sentinel.trading.oversight.assessment.v0.1',
            'snapshot_sha256': input_hash, 'scope': s['scope'], 'state_binding': binding,
            'checker_versions': {'offline': CHECKER_VERSION}, 'policy_binding': policies,
            'observed_at': now, 'source_as_of': c['source_as_of'],
            'overall_status': 'BLOCKED', 'integrity': integrity, 'strategy': 'UNVERIFIED',
            'risk': 'UNVERIFIED', 'source': 'OPERATOR_SUPPLIED_UNVERIFIED',
            'reconciliation': s['readiness']['reconciliation'], 'findings': findings,
            'human_review': 'PENDING', 'authority': dict(AUTHORITY)}
    return {'assessment_id': digest(base), **base}
