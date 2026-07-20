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
        evidence_id="engineering-architecture-map",
        title="SentinelAI Architecture Map",
        kind="document",
        source="docs/architecture/ARCHITECTURE_MAP.md",
        description=(
            "Documents SentinelAI's engineering architecture "
            "and system organization."
        ),
    )
],
    ),
OperationalDomain(
    domain_id="trading",
    name="Trading",
    description=(
        "Support evidence-driven market analysis, risk management, "
        "trade planning, performance review, and trading education."
    ),
    kind="system",
    status="developing",
    evidence=[
        DomainEvidence(
            evidence_id="trading-domain-foundation",
            title="Trading Domain Foundation",
            kind="document",
            source="docs/domains/trading/DOMAIN.md",
            description=(
                "Defines the Trading Domain's purpose, scope, boundaries, "
                "maturity, and evidence requirements."
            ),
        ),
        DomainEvidence(
            evidence_id="trading-principles",
            title="Trading Principles",
            kind="principle",
            source="docs/domains/trading/PRINCIPLES.md",
            description=(
                "Defines the enduring principles governing market reasoning, "
                "risk, explainability, probability, and reflection."
            ),
        ),
    ],
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

