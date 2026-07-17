from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.core.domains.builder import build_domain_registry
from app.core.domains.models import OperationalDomain


ValidationLevel = Literal["pass", "warning", "error"]

VALID_KINDS = {"system", "user"}
VALID_STATUSES = {
    "planned",
    "developing",
    "active",
    "limited",
    "unavailable",
}


@dataclass
class DomainValidationCheck:
    domain_id: str
    name: str
    level: ValidationLevel
    message: str

    @property
    def passed(self) -> bool:
        return self.level == "pass"


@dataclass
class DomainValidationReport:
    status: str
    passed: int
    warnings: int
    errors: int
    checks: list[DomainValidationCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def add_check(
    checks: list[DomainValidationCheck],
    *,
    domain_id: str,
    name: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    failure_level: ValidationLevel = "error",
) -> None:
    checks.append(
        DomainValidationCheck(
            domain_id=domain_id,
            name=name,
            level="pass" if condition else failure_level,
            message=success_message if condition else failure_message,
        )
    )


def validate_domain(
    domain: OperationalDomain,
    checks: list[DomainValidationCheck],
) -> None:
    """
    Validate one operational domain without modifying it.
    """

    domain_id = domain.domain_id or "<missing>"

    add_check(
        checks,
        domain_id=domain_id,
        name="domain_id",
        condition=bool(domain.domain_id.strip()),
        success_message="Domain identifier is defined.",
        failure_message="Domain identifier is missing.",
    )

    add_check(
        checks,
        domain_id=domain_id,
        name="name",
        condition=bool(domain.name.strip()),
        success_message="Domain name is defined.",
        failure_message="Domain name is missing.",
    )

    add_check(
        checks,
        domain_id=domain_id,
        name="description",
        condition=bool(domain.description.strip()),
        success_message="Domain description is defined.",
        failure_message="Domain description is missing.",
    )

    add_check(
        checks,
        domain_id=domain_id,
        name="kind",
        condition=domain.kind in VALID_KINDS,
        success_message=f"Domain kind '{domain.kind}' is valid.",
        failure_message=f"Domain kind '{domain.kind}' is invalid.",
    )

    add_check(
        checks,
        domain_id=domain_id,
        name="status",
        condition=domain.status in VALID_STATUSES,
        success_message=f"Domain status '{domain.status}' is valid.",
        failure_message=f"Domain status '{domain.status}' is invalid.",
    )

    add_check(
        checks,
        domain_id=domain_id,
        name="owner",
        condition=domain.kind == "system" or bool(domain.owner_id),
        success_message="Domain ownership is valid.",
        failure_message="User domains must define an owner.",
    )

    evidence_required = domain.status in {"active", "developing"}

    add_check(
        checks,
        domain_id=domain_id,
        name="evidence",
        condition=not evidence_required or bool(domain.evidence),
        success_message="Domain evidence requirements are satisfied.",
        failure_message=(
            f"Domain status '{domain.status}' requires supporting evidence."
        ),
        failure_level="warning",
    )


def build_domain_validation_report() -> DomainValidationReport:
    """
    Validate all registered operational domains.

    Validator reports.
    Validator never repairs or activates domains.
    """

    registry = build_domain_registry()
    checks: list[DomainValidationCheck] = []

    for domain in registry.list_domains():
        validate_domain(domain, checks)

    passed = sum(check.level == "pass" for check in checks)
    warnings = sum(check.level == "warning" for check in checks)
    errors = sum(check.level == "error" for check in checks)

    if errors:
        status = "invalid"
    elif warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return DomainValidationReport(
        status=status,
        passed=passed,
        warnings=warnings,
        errors=errors,
        checks=checks,
    )
