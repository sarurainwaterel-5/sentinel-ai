from types import SimpleNamespace
from app.core.bridge import health, summary


def test_bridge_health_retains_observed_time_configuration_and_warnings(monkeypatch):
    snapshot = SimpleNamespace(observed_at="now", status="degraded", warnings=["Memory unavailable"], services=[SimpleNamespace(name="Memory", status="unavailable")], model_features_configured=False)
    monkeypatch.setattr(health.SystemsObserver, "observe", lambda self: snapshot)
    result = health.build_operational_health()
    assert result["overall"] == "Degraded"
    assert result["observed_at"] == "now"
    assert result["observations"] == ["Memory unavailable"]
    assert result["model_features_configured"] is False


def test_bridge_structure_does_not_claim_semantic_coherence(monkeypatch):
    monkeypatch.setattr(summary, "build_canon_manifest", lambda: dict(name="Canon", version="1", document_count=1, layer_count=1, types={}))
    monkeypatch.setattr(summary, "build_canon_report", lambda: dict(status="healthy", warnings=[]))
    monkeypatch.setattr(summary, "build_canon_graph", lambda: dict(name="Graph", version="1", node_count=1, edge_count=0, relationships={}))
    monkeypatch.setattr(summary, "build_operational_health", lambda: {"overall": "Degraded"})
    result = summary.build_bridge_summary()
    assert result["reflection"]["evaluation"] == "not_verified"
    assert "understands itself" not in result["reflection"]["message"]
    assert result["execution_authority"] == "human"
    assert result["health"]["overall"] == "Degraded"
