from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.core.self.builder import build_self_model


ValidationLevel = Literal["pass", "warning", "error"]


@dataclass
class ValidationCheck:
    """
    One verification performed against SentinelAI's candidate self-model.
    """

    name: str
    category: str
    level: ValidationLevel
    message: str
    evidence: list[str] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return self.level == "pass"


@dataclass
class ValidationReport:
    """
    Immutable report describing whether a candidate self-model is safe
    to render as SentinelAI's evidence-backed identity.
    """

    status: str
    passed: int
    warnings: int
    errors: int
    checks: list[ValidationCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def add_check(
    checks: list[ValidationCheck],
    *,
    name: str,
    category: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    failure_level: ValidationLevel = "error",
    evidence: list[str] | None = None,
) -> None:
    """
    Append a pass, warning, or error without modifying the self-model.
    """

    checks.append(
        ValidationCheck(
            name=name,
            category=category,
            level="pass" if condition else failure_level,
            message=success_message if condition else failure_message,
            evidence=evidence or [],
        )
    )


def evidence_sources(model: dict[str, Any]) -> set[str]:
    """
    Return all evidence source paths registered in the self-model.
    """

    return {
        record.get("source", "")
        for record in model.get("evidence", [])
        if record.get("source")
    }


def validate_identity(
    model: dict[str, Any],
    checks: list[ValidationCheck],
) -> None:
    """
    Verify SentinelAI's foundational identity claims.
    """

    identity = model.get("identity", {})
    sources = evidence_sources(model)

    add_check(
        checks,
        name="identity_name",
        category="identity",
        condition=identity.get("name") == "SentinelAI",
        success_message="SentinelAI's name is defined.",
        failure_message="SentinelAI's name is missing or invalid.",
    )

    add_check(
        checks,
        name="identity_category",
        category="identity",
        condition=bool(identity.get("category")),
        success_message="SentinelAI's category is defined.",
        failure_message="SentinelAI's category has not been established.",
        evidence=["docs/philosophy/VISION.md"],
    )

    add_check(
        checks,
        name="identity_purpose",
        category="identity",
        condition=bool(identity.get("purpose")),
        success_message="SentinelAI's purpose is defined.",
        failure_message="SentinelAI's purpose has not been established.",
        evidence=["docs/philosophy/VISION.md"],
    )

    add_check(
        checks,
        name="identity_mission",
        category="identity",
        condition=bool(identity.get("mission")),
        success_message="SentinelAI's communication mission is defined.",
        failure_message="SentinelAI's communication mission is unavailable.",
        failure_level="warning",
        evidence=["docs/design/SENTINEL_LANGUAGE.md"],
    )

    add_check(
        checks,
        name="identity_principles",
        category="identity",
        condition=bool(identity.get("principles")),
        success_message="SentinelAI's guiding principles are established.",
        failure_message="SentinelAI's guiding principles are unavailable.",
        failure_level="warning",
        evidence=["docs/philosophy/SENTINEL_TRIANGLE.md"],
    )

    required_identity_sources = {
        "docs/philosophy/VISION.md",
        "docs/design/SENTINEL_LANGUAGE.md",
        "docs/philosophy/SENTINEL_TRIANGLE.md",
    }

    missing_sources = sorted(required_identity_sources - sources)

    add_check(
        checks,
        name="identity_evidence",
        category="evidence",
        condition=not missing_sources,
        success_message="All foundational identity claims have registered evidence.",
        failure_message=(
            "Foundational identity evidence is incomplete: "
            + ", ".join(missing_sources)
        ),
        failure_level="warning",
        evidence=sorted(required_identity_sources),
    )


def validate_structure(
    model: dict[str, Any],
    checks: list[ValidationCheck],
) -> None:
    """
    Verify discovered architectural structure.
    """

    structure = model.get("structure", {})

    add_check(
        checks,
        name="workspaces_discovered",
        category="structure",
        condition=bool(structure.get("workspaces")),
        success_message="Operator workspaces were discovered.",
        failure_message="No operator workspaces were discovered.",
    )

    add_check(
        checks,
        name="routes_discovered",
        category="structure",
        condition=bool(structure.get("routes")),
        success_message="Public API routes were discovered.",
        failure_message="No public API routes were discovered.",
    )

    add_check(
        checks,
        name="knowledge_layers_built",
        category="structure",
        condition=bool(structure.get("knowledge_layers")),
        success_message="Knowledge layers were derived from discovered documents.",
        failure_message="No knowledge layers could be derived.",
    )


def validate_knowledge(
    model: dict[str, Any],
    checks: list[ValidationCheck],
) -> None:
    """
    Verify the discovered knowledge structure.
    """

    knowledge = model.get("knowledge", {})

    add_check(
        checks,
        name="documents_discovered",
        category="knowledge",
        condition=bool(knowledge.get("documents")),
        success_message="Canon documents were discovered.",
        failure_message="No Canon documents were discovered.",
    )

    add_check(
        checks,
        name="relationships_discovered",
        category="knowledge",
        condition=bool(knowledge.get("relationships")),
        success_message="Knowledge relationships were discovered.",
        failure_message="No knowledge relationships were discovered.",
        failure_level="warning",
    )


def validate_evidence(
    model: dict[str, Any],
    checks: list[ValidationCheck],
) -> None:
    """
    Verify that discovery and identity claims include traceable evidence.
    """

    evidence = model.get("evidence", [])

    add_check(
        checks,
        name="evidence_registry_present",
        category="evidence",
        condition=bool(evidence),
        success_message="The evidence registry contains traceable sources.",
        failure_message="The self-model contains no registered evidence.",
    )

    invalid_records = [
        index
        for index, record in enumerate(evidence)
        if not record.get("evidence_type")
        or not record.get("source")
        or not record.get("description")
    ]

    add_check(
        checks,
        name="evidence_records_complete",
        category="evidence",
        condition=not invalid_records,
        success_message="All evidence records contain type, source, and description.",
        failure_message=(
            "Incomplete evidence records found at indexes: "
            + ", ".join(map(str, invalid_records))
        ),
    )


def validate_boundaries(
    model: dict[str, Any],
    checks: list[ValidationCheck],
) -> None:
    """
    Report whether SentinelAI currently has explicit documented boundaries.

    Boundaries are not fully populated yet, so absence is a warning rather
    than an error during this initial validator phase.
    """

    boundaries = model.get("boundaries", {})
    has_boundaries = any(
        boundaries.get(key)
        for key in (
            "limitations",
            "policies",
            "unsupported_capabilities",
        )
    )

    add_check(
        checks,
        name="boundaries_declared",
        category="boundaries",
        condition=has_boundaries,
        success_message="SentinelAI has explicit documented boundaries.",
        failure_message=(
            "No explicit limitations, policies, or unsupported capabilities "
            "have been registered yet."
        ),
        failure_level="warning",
    )


def build_validation_report(
    model: dict[str, Any] | None = None,
) -> ValidationReport:
    """
    Validate a candidate self-model without modifying it.

    Only validated truth may become SentinelAI's rendered identity.
    """

    candidate = model or build_self_model()
    checks: list[ValidationCheck] = []

    validate_identity(candidate, checks)
    validate_structure(candidate, checks)
    validate_knowledge(candidate, checks)
    validate_evidence(candidate, checks)
    validate_boundaries(candidate, checks)

    passed = sum(check.level == "pass" for check in checks)
    warnings = sum(check.level == "warning" for check in checks)
    errors = sum(check.level == "error" for check in checks)

    if errors:
        status = "invalid"
    elif warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return ValidationReport(
        status=status,
        passed=passed,
        warnings=warnings,
        errors=errors,
        checks=checks,
    )
