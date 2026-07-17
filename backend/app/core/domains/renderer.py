from typing import Any

from app.core.domains.builder import build_domain_registry
from app.core.domains.validator import (
    DomainValidationReport,
    build_domain_validation_report,
)


class DomainModelValidationError(RuntimeError):
    """
    Raised when an invalid domain registry is submitted for rendering.
    """


def render_domain_model(
    validation_report: DomainValidationReport | None = None,
) -> dict[str, Any]:
    """
    Render SentinelAI's validated Domain Model.

    Renderer communicates validated operational-domain information.

    It does not discover, register, build, validate, activate,
    compose, or modify domains.
    """

    registry = build_domain_registry()
    report = validation_report or build_domain_validation_report()

    if report.errors:
        raise DomainModelValidationError(
            "Domain Model rendering refused because validation failed "
            f"with {report.errors} error(s)."
        )

    domains = registry.list_domains()

    system_domains = [
        domain.to_dict()
        for domain in domains
        if domain.kind == "system"
    ]

    user_domains = [
        domain.to_dict()
        for domain in domains
        if domain.kind == "user"
    ]

    status_counts = {
        status: sum(
            1 for domain in domains if domain.status == status
        )
        for status in (
            "active",
            "developing",
            "planned",
            "limited",
            "unavailable",
        )
    }

    summary = {
        "total_domains": len(domains),
        "system_domains": len(system_domains),
        "user_domains": len(user_domains),
        "active_domains": status_counts["active"],
        "developing_domains": status_counts["developing"],
        "planned_domains": status_counts["planned"],
        "limited_domains": status_counts["limited"],
        "unavailable_domains": status_counts["unavailable"],
    }

    return {
        "principle": (
            "Operational Domains specialize SentinelAI's operation "
            "while preserving a single validated constitutional identity."
        ),
        "summary": summary,
        "system_domains": system_domains,
        "user_domains": user_domains,
        "validation": report.to_dict(),
    }
