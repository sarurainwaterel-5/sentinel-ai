from fastapi.testclient import TestClient
import pytest
from app.main import app


def test_liveness_without_model_credentials(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    assert TestClient(app).get('/health').json()['service'] == 'SentinelAI'


@pytest.mark.parametrize('path', ['/ask', '/cognition/reason', '/cognition/plan', '/verification'])
def test_model_features_explain_missing_configuration(monkeypatch, path):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    response = TestClient(app).post(path, json={})
    assert response.status_code == 503
    assert 'OPENAI_API_KEY' in response.json()['detail']
