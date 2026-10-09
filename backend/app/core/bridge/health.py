"""Translate observed platform condition into Bridge operator language."""
from app.services.workspaces.systems import SystemsObserver


def build_operational_health():
    snapshot = SystemsObserver().observe()
    return {
        "overall": "Ready" if snapshot.status == "ready" else "Degraded",
        "warnings": len(snapshot.warnings),
        "services": {service.name: service.status for service in snapshot.services},
    }
