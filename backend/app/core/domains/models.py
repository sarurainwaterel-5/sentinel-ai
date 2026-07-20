from dataclasses import asdict, dataclass, field
from typing import Any, Literal


DomainKind = Literal["system", "user"]

DomainStatus = Literal[
    "planned",
    "developing",
    "active",
    "limited",
    "unavailable",
]

EvidenceKind = Literal[
    "document",
    "adr",
    "sprint",
    "principle",
    "source_code",
    "route",
    "model",
    "service",
    "configuration",
]


@dataclass
class DomainEvidence:
    """
    A structured reference to reality supporting an Operational Domain.

    Domain evidence does not duplicate or own the underlying source.
    It identifies where supporting reality exists and explains why
    that source is relevant to the domain.
    """

    evidence_id: str
    title: str
    kind: EvidenceKind
    source: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serializable evidence representation.
        """

        return asdict(self)


@dataclass
class OperationalDomain:
    """
    A validated operating context that specializes SentinelAI without
    changing SentinelAI's constitutional identity.

    Responsibilities:

    - Represent one Operational Domain.
    - Reference the evidence supporting its existence and maturity.

    Non-responsibilities:

    - Domain activation
    - Domain reasoning
    - Domain validation
    - Domain composition
    - Domain discovery
    """

    domain_id: str
    name: str
    description: str
    kind: DomainKind
    status: DomainStatus

    owner_id: str | None = None
    evidence: list[DomainEvidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serializable domain representation.
        """

        return asdict(self)
