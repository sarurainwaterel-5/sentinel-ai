"""Fixed historical receipt inspection; never a runtime release capability."""
import hashlib
import json
from pathlib import Path

PINS = {
    'owner': ('docs/governance/sprint21-owner-packet.accepted-20261113.json', '81838ee3378231e054420ea195797f39e657ed98697c516b016b86f8f6d8064a'),
    'review': ('backend/evaluation/semantic_judge/results/astra-20261111-run1.review.accepted.json', '89cff85980d0311c97de933d615aa2dde603e6413f00318c3cf1bae656643730'),
    'installed': ('docs/governance/governed-workspace.installed-20261113.json', 'c35a86f9304db312d57a7e2b01623b4a302861e8f76f6207cba1ee8eeaceb848'),
}


def _read(root, kind):
    relative, digest = PINS[kind]
    path = (root / relative).resolve(strict=True)
    path.relative_to(root.resolve(strict=True))
    data = path.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest:
        raise ValueError('receipt_binding_changed')
    value = json.loads(data)
    if (type(value) is not dict or value.get('production_enabled') is not False
            or value.get('release_authorized') is not False
            or value.get('proposition_to_inference') != 'closed'):
        raise ValueError('invalid_receipt_boundary')
    return value


def inspect_current_receipts(root: Path, *, benchmark_valid: bool):
    """Summarize exact accepted records, without reading secrets or live services."""
    result = {'empirical_review_approved': False,
              'independent_deployment_review_approved': False,
              'owner_packet': {'status': 'evidence_invalid_or_missing'},
              'source_workspace': {'status': 'evidence_invalid_or_missing',
                                   'live_state_attested': False}}
    try:
        owner = _read(root, 'owner')
        review = _read(root, 'review')
        report = (root / review['report_path']).resolve(strict=True)
        report.relative_to(root.resolve(strict=True))
        if (benchmark_valid is not True or owner['owner_packet_review_accepted'] is not True
                or review['empirical_review_approved'] is not True
                or review['independent_deployment_review_approved'] is not True
                or review['acceptance_record'] != PINS['owner'][0]
                or review['owner_packet_sha256'] != owner['artifact_sha256']['owner-review.html']
                or hashlib.sha256(report.read_bytes()).hexdigest() != review['report_sha256']):
            raise ValueError('invalid_acceptance_binding')
        result.update(empirical_review_approved=True,
                      independent_deployment_review_approved=True)
        result['owner_packet'] = {'status': 'accepted_with_packet_limitations',
            'record': PINS['owner'][0], 'record_sha256': PINS['owner'][1],
            'scope': 'Exact recorded benchmark, deployment separation and owner packet only; no production authorization or general semantic accuracy.'}
    except Exception:
        pass
    try:
        installed = _read(root, 'installed')
        if (installed['version'] != 'sentinel-governed-workspace-installed-v1'
                or installed['all_active_full_manifest_inspections_verified'] is not True
                or installed['all_archived_inspections_denied'] is not True
                or installed['legacy_public_tables_unchanged'] is not True):
            raise ValueError('invalid_installation_receipt')
        result['source_workspace'] = {
            'status': 'recorded_installed_and_verified', 'live_state_attested': False,
            'record': PINS['installed'][0], 'record_sha256': PINS['installed'][1],
            'recorded_local_date': installed['recorded_local_date'],
            'migrated_documents': installed['migrated_documents'],
            'active_documents': installed['active_documents'],
            'archived_documents': installed['archived_documents'],
            'quarantined_documents': installed['quarantined_documents'],
            'scope': 'Hash-bound historical operational source-inspection receipt; this endpoint does not contact the installed services or recheck private backup and corpus artifacts.'}
    except Exception:
        pass
    return result
