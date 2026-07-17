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


@dataclass
class DomainEvidence:
    """
    Evidence supporting the existence, purpose, or status of a domain.
    """

    source: str
    description: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OperationalDomain:
    """
    A validated operating context that specializes SentinelAI without
    changing SentinelAI's constitutional identity.
    """

    domain_id: str
    name: str
    description: str
    kind: DomainKind
    status: DomainStatus

    owner_id: str | None = None
    evidence: list[DomainEvidence] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
