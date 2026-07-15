from pathlib import Path
from typing import Any

from app.core.self.builder import PROJECT_ROOT, build_self_model
from app.core.self.validator import ValidationReport, build_validation_report


SELF_DOCS_ROOT = PROJECT_ROOT / "docs" / "self"
IDENTITY_MODEL_PATH = SELF_DOCS_ROOT / "SENTINEL_IDENTITY_MODEL.md"


class IdentityModelValidationError(RuntimeError):
    """
    Raised when an invalid self-model is submitted for rendering.
    """


def markdown_list(items: list[str], empty_message: str) -> str:
    """
    Render a Markdown list or a clear empty-state message.
    """

    if not items:
        return f"- {empty_message}"

    return "\n".join(f"- {item}" for item in items)


def render_identity(model: dict[str, Any]) -> str:
    """
    Render SentinelAI's validated identity facts.
    """

    identity = model.get("identity", {})
    principles = identity.get("principles", [])

    principle_names = [
        principle.get("name", "Unnamed principle")
        for principle in principles
    ]

    return f"""## Identity

**Name:** {identity.get("name") or "Not established"}

**Category:** {identity.get("category") or "Not established"}

**Purpose:** {identity.get("purpose") or "Not established"}

**Mission:** {identity.get("mission") or "Not established"}

### Guiding Principles

{markdown_list(principle_names, "No guiding principles have been validated.")}
"""


def render_structure(model: dict[str, Any]) -> str:
    """
    Render SentinelAI's discovered structural facts.
    """

    structure = model.get("structure", {})

    workspaces = [
        f"{workspace.get('name', workspace.get('id', 'Unknown'))} "
        f"(`{workspace.get('component', 'Unknown component')}`)"
        for workspace in structure.get("workspaces", [])
    ]

    routes = [
        f"`{'/'.join(route.get('methods', [])) or 'UNKNOWN'} "
        f"{route.get('path', 'Unknown path')}`"
        for route in structure.get("routes", [])
    ]

    layers = [
        f"{layer.get('name', 'Unclassified')}: "
        f"{layer.get('document_count', 0)} documents"
        for layer in structure.get("knowledge_layers", [])
    ]

    return f"""## Structure

### Workspaces

{markdown_list(workspaces, "No workspaces were discovered.")}

### Public Routes

{markdown_list(routes, "No public routes were discovered.")}

### Knowledge Layers

{markdown_list(layers, "No knowledge layers were derived.")}
"""


def render_function(model: dict[str, Any]) -> str:
    """
    Render verified capabilities and operational domains.
    """

    function = model.get("function", {})

    capabilities = [
        f"{item.get('name', 'Unnamed capability')} "
        f"— {item.get('status', 'unknown')}"
        for item in function.get("capabilities", [])
    ]

    domains = [
        f"{item.get('name', 'Unnamed domain')} "
        f"— {item.get('status', 'unknown')}"
        for item in function.get("operational_domains", [])
    ]

    return f"""## Function

### Verified Capabilities

{markdown_list(capabilities, "No capabilities have been verified yet.")}

### Operational Domains

{markdown_list(domains, "No operational domains have been registered yet.")}
"""


def render_knowledge(model: dict[str, Any]) -> str:
    """
    Render summarized knowledge facts.
    """

    summary = model.get("summary", {})

    return f"""## Knowledge

- Principle documents: {summary.get("document_count", 0)}
- Knowledge layers: {summary.get("knowledge_layer_count", 0)}
- Active connections: {summary.get("relationship_count", 0)}
- Evidence records: {summary.get("evidence_count", 0)}
"""


def render_boundaries(model: dict[str, Any]) -> str:
    """
    Render explicitly declared limitations and unsupported capabilities.
    """

    boundaries = model.get("boundaries", {})

    limitations = [
        item.get("name", "Unnamed limitation")
        for item in boundaries.get("limitations", [])
    ]

    unsupported = [
        item.get("name", "Unnamed unsupported capability")
        for item in boundaries.get("unsupported_capabilities", [])
    ]

    policies = [
        item.get("name", "Unnamed policy")
        for item in boundaries.get("policies", [])
    ]

    return f"""## Boundaries

### Limitations

{markdown_list(limitations, "No explicit limitations have been registered yet.")}

### Unsupported Capabilities

{markdown_list(unsupported, "No unsupported capabilities have been registered yet.")}

### Policies

{markdown_list(policies, "No self-model policies have been registered yet.")}
"""


def render_evidence(model: dict[str, Any]) -> str:
    """
    Render the evidence sources supporting the Identity Model.
    """

    records = model.get("evidence", [])

    evidence_lines = [
        (
            f"`{record.get('source', 'Unknown source')}` — "
            f"{record.get('description', 'No description provided.')}"
        )
        for record in records
    ]

    return f"""## Evidence

{markdown_list(evidence_lines, "No evidence has been registered.")}
"""


def render_validation(report: ValidationReport) -> str:
    """
    Render validation status and non-passing checks.
    """

    concerns = [
        f"{check.level.upper()}: {check.message}"
        for check in report.checks
        if check.level != "pass"
    ]

    return f"""## Validation

**Status:** {report.status}

- Passed checks: {report.passed}
- Warnings: {report.warnings}
- Errors: {report.errors}

### Open Concerns

{markdown_list(concerns, "No validation concerns detected.")}
"""


def render_identity_model(
    model: dict[str, Any],
    report: ValidationReport,
) -> str:
    """
    Render a validated candidate model as Markdown.

    The renderer communicates approved facts only. It never modifies,
    repairs, or supplements the candidate model.
    """

    if report.errors:
        raise IdentityModelValidationError(
            "Identity Model rendering refused because validation failed "
            f"with {report.errors} error(s)."
        )

    sections = [
        "# SentinelAI Identity Model",
        """
> **Generated Artifact**
>
> This document is generated from SentinelAI's observed architecture.
> Do not edit it manually.
>
> To change SentinelAI's identity, change the underlying reality and
> regenerate this model through Discovery, Builder, Validator, and Renderer.
""".strip(),
        render_identity(model),
        render_structure(model),
        render_function(model),
        render_knowledge(model),
        render_boundaries(model),
        render_evidence(model),
        render_validation(report),
    ]

    return "\n\n---\n\n".join(section.strip() for section in sections) + "\n"


def generate_identity_model(
    output_path: Path = IDENTITY_MODEL_PATH,
) -> Path:
    """
    Build, validate, and publish SentinelAI's generated Identity Model.
    """

    model = build_self_model()
    report = build_validation_report(model)

    content = render_identity_model(model, report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(content, encoding="utf-8")

    return output_path
