"""Current read-only release diagnostics, separate from the frozen answer API."""
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter
from app.services.cognition.reasoning.release_gate import inspect_release_gate
from evaluation.semantic_judge.astra_report import inspect_astra_report
from app.services.current_release_evidence import inspect_current_receipts

router = APIRouter(prefix='/governance', tags=['Release inspection'])
ROOT = Path(__file__).resolve().parents[3]
ASTRA_REPORT = Path('backend/evaluation/semantic_judge/results/astra-20261111-run1.json')


def _disabled(value):
    return (type(value) is dict and value.get('enabled') is False
            and value.get('production_enabled') is False
            and value.get('release_authorized') is False
            and value.get('semantic_grounding_verified') is False
            and value.get('proposition_to_inference') == 'closed')


@router.get('/release-inspection')
def release_inspection():
    # Paths are fixed by the application: no request-supplied file access, role
    # configuration, provider construction, catalog access or approval operation.
    result = {'schema_version': 'sprint21-current-release-inspection-v1',
              'observed_at': datetime.now(timezone.utc).isoformat(),
              'status': 'disabled', 'enabled': False, 'production_enabled': False,
              'release_authorized': False, 'semantic_grounding_verified': False,
              'proposition_to_inference': 'closed',
              'empirical_review_approved': False, 'presentation_review_approved': False,
              'blockers': ['production_answer_runtime_acceptance_incomplete',
                           'runtime_presentation_review_required',
                           'bound_production_authorization_required'],
              'denial_diagnostic': {'status': 'unavailable'},
              'astra_benchmark': {'status': 'unavailable', 'eligible_for_human_review': False},
              'limitation': 'Read-only evidence inspection; no API calls, acceptance signature, migration or production activation.'}
    try:
        diagnostic = inspect_release_gate(ROOT)
        if not _disabled(diagnostic):
            raise ValueError('invalid_diagnostic_authority')
        result['denial_diagnostic'] = {'status': 'disabled', 'blockers': diagnostic['blockers'],
            'scope': 'Underlying denial-only gate inventory; current limited owner acceptance is reported separately and cannot unlock this gate.'}
    except Exception:
        result['blockers'].append('current_denial_diagnostic_unavailable')
    try:
        audit = inspect_astra_report(ROOT, ASTRA_REPORT)
        if not _disabled(audit):
            raise ValueError('invalid_benchmark_authority')
        result['astra_benchmark'] = {
            'status': 'meets_recorded_thresholds_pending_review' if audit['empirical_report_eligible_for_human_review'] else 'evidence_invalid_or_missing',
            'eligible_for_human_review': audit['empirical_report_eligible_for_human_review'],
            'recomputed_metrics': audit['recomputed_empirical_metrics'],
            'errors': audit['errors'],
            'scope': '36 reviewed synthetic cases repeated three times; Chat Completions judge path only. Generation, relevance and production retrieval were not measured.'}
    except Exception:
        result['blockers'].append('astra_benchmark_diagnostic_unavailable')
    receipts = inspect_current_receipts(ROOT, benchmark_valid=result['astra_benchmark']['eligible_for_human_review'])
    result.update(receipts)
    if receipts['empirical_review_approved']:
        result['astra_benchmark']['status'] = 'owner_accepted_limited_evidence'
    else:
        result['blockers'].append('accepted_empirical_evidence_invalid_or_missing')
    return result
