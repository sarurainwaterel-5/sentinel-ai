from app.core.domains.models import DomainEvidence, OperationalDomain


SYSTEM_DOMAINS = [
    OperationalDomain(
        domain_id="engineering",
        name="Engineering",
        description=(
            "Support system design, implementation, debugging, "
            "documentation, and software architecture."
        ),
        kind="system",
        status="active",
        evidence=[
            DomainEvidence(
                source="docs/architecture/ARCHITECTURE_MAP.md",
                description="Documents SentinelAI's engineering architecture.",
            )
        ],
    ),
    OperationalDomain(
        domain_id="trading",
        name="Trading",
        description=(
            "Support market analysis, risk management, execution planning, "
            "and trading education."
        ),
        kind="system",
        status="developing",
    ),
    OperationalDomain(
        domain_id="security",
        name="Security",
        description=(
            "Support cybersecurity analysis and defensive operations."
        ),
        kind="system",
        status="developing",
    ),
    OperationalDomain(
        domain_id="law",
        name="Law",
        description=(
            "Support legal research and evidence-backed analysis."
        ),
        kind="system",
        status="developing",
    ),
    OperationalDomain(
        domain_id="marketing",
        name="Marketing",
        description=(
            "Support communication, branding, positioning, and growth strategy."
        ),
        kind="system",
        status="planned",
    ),
    OperationalDomain(
        domain_id="history",
        name="History",
        description=(
            "Support historical research, source comparison, and evidence analysis."
        ),
        kind="system",
        status="planned",
    ),
    OperationalDomain(
        domain_id="philosophy",
        name="Philosophy",
        description=(
            "Support philosophical reasoning and first-principles analysis."
        ),
        kind="system",
        status="planned",
    ),
]
