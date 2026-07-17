from app.core.domains.discover import discover_system_domains
from app.core.domains.registry import DomainRegistry


def build_domain_registry() -> DomainRegistry:
    """
    Build SentinelAI's domain registry from discovered operational domains.

    Discovery observes.
    Registry records.
    Builder assembles.
    """

    registry = DomainRegistry()

    for domain in discover_system_domains():
        registry.register(domain)

    return registry
