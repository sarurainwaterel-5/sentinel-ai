from fastapi import FastAPI
from fastapi.testclient import TestClient
from app.routes import release_inspection as routes


def test_actual_saved_astra_evidence_is_currently_reviewable_but_never_enables_release():
    app=FastAPI(); app.include_router(routes.router)
    response=TestClient(app).get('/governance/release-inspection')
    assert response.status_code == 200
    data=response.json()
    assert data['astra_benchmark']['eligible_for_human_review'] is True
    assert data['denial_diagnostic']['status'] == 'disabled'
    assert data['empirical_review_approved'] is True
    assert data['independent_deployment_review_approved'] is True
    assert data['astra_benchmark']['status'] == 'owner_accepted_limited_evidence'
    assert data['source_workspace']['status'] == 'recorded_installed_and_verified'
    assert data['source_workspace']['live_state_attested'] is False
    assert data['presentation_review_approved'] is False
    assert data['enabled'] is data['production_enabled'] is data['release_authorized'] is False
    assert data['semantic_grounding_verified'] is False
    assert data['proposition_to_inference'] == 'closed'


def test_diagnostic_errors_are_sanitized_and_leave_release_closed(monkeypatch):
    def fail(*args): raise RuntimeError('secret-local-path-or-credential')
    monkeypatch.setattr(routes,'inspect_release_gate',fail)
    monkeypatch.setattr(routes,'inspect_astra_report',fail)
    result=routes.release_inspection()
    assert result['astra_benchmark']['eligible_for_human_review'] is False
    assert result['denial_diagnostic']['status'] == 'unavailable'
    assert 'secret-local' not in str(result)
    assert result['enabled'] is result['release_authorized'] is False


def test_unexpected_approval_flags_in_inspector_are_refused(monkeypatch):
    unexpected=dict(enabled=True,production_enabled=True,release_authorized=True,
                    semantic_grounding_verified=True,proposition_to_inference='open')
    monkeypatch.setattr(routes,'inspect_release_gate',lambda *args: unexpected)
    monkeypatch.setattr(routes,'inspect_astra_report',lambda *args: unexpected)
    result=routes.release_inspection()
    assert result['denial_diagnostic']['status'] == 'unavailable'
    assert result['astra_benchmark']['eligible_for_human_review'] is False
    assert result['production_enabled'] is False


def test_request_cannot_choose_a_report_file_or_approve_release():
    app=FastAPI(); app.include_router(routes.router)
    client=TestClient(app)
    result=client.get('/governance/release-inspection?report=/etc/passwd&enabled=true').json()
    assert result['astra_benchmark']['eligible_for_human_review'] is True
    assert result['enabled'] is False
    assert client.post('/governance/release-inspection',json={'enabled':True}).status_code == 405


def test_missing_or_modified_receipts_fail_closed(tmp_path):
    from app.services.current_release_evidence import inspect_current_receipts, PINS
    import shutil
    from pathlib import Path
    root=routes.ROOT
    for relative, _ in PINS.values():
        target=tmp_path/relative; target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(root/relative,target)
    report=Path('backend/evaluation/semantic_judge/results/astra-20261111-run1.json')
    shutil.copyfile(root/report,tmp_path/report)
    assert inspect_current_receipts(tmp_path,benchmark_valid=True)['empirical_review_approved'] is True
    owner=tmp_path/PINS['owner'][0]
    owner.write_text(owner.read_text()+' ')
    result=inspect_current_receipts(tmp_path,benchmark_valid=True)
    assert result['empirical_review_approved'] is False
    assert result['source_workspace']['status']=='recorded_installed_and_verified'
    (tmp_path/PINS['installed'][0]).unlink()
    assert inspect_current_receipts(tmp_path,benchmark_valid=True)['source_workspace']['status']=='evidence_invalid_or_missing'


def test_invalid_benchmark_never_uses_an_accepted_companion():
    from app.services.current_release_evidence import inspect_current_receipts
    result=inspect_current_receipts(routes.ROOT,benchmark_valid=False)
    assert result['empirical_review_approved'] is False
    assert result['independent_deployment_review_approved'] is False
