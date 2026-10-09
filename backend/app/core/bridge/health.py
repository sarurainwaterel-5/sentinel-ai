"""Translate observed platform condition into Bridge operator language."""
from app.services.workspaces.systems import SystemsObserver


def build_operational_health():
    snapshot = SystemsObserver().observe()
    return {
        "observed_at": snapshot.observed_at,
        "model_features_configured": snapshot.model_features_configured,
        "observations": snapshot.warnings,
        "overall": "Ready" if snapshot.status == "ready" else "Degraded",
        "warnings": len(snapshot.warnings),
        "services": {service.name: service.status for service in snapshot.services},
    }
