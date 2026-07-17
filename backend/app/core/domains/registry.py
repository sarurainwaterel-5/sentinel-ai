from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.domains.models import OperationalDomain


@dataclass
class DomainRegistry:
    """
    Registry of operational domains known to SentinelAI.

    The registry records domains.
    It does not activate, validate, or interpret them.
    """

    domains: list[OperationalDomain] = field(default_factory=list)

    def register(self, domain: OperationalDomain) -> None:
        """
        Register a domain if its identifier is not already present.
        """

        if self.get(domain.domain_id) is not None:
            raise ValueError(
                f"Domain '{domain.domain_id}' is already registered."
            )

        self.domains.append(domain)

    def get(self, domain_id: str) -> OperationalDomain | None:
        """
        Return a domain by identifier.
        """

        return next(
            (
                domain
                for domain in self.domains
                if domain.domain_id == domain_id
            ),
            None,
        )

    def list_domains(self) -> list[OperationalDomain]:
        """
        Return domains in deterministic identifier order.
        """

        return sorted(
            self.domains,
            key=lambda domain: domain.domain_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """
        Return a serializable registry representation.
        """

        return asdict(self)
