from app.core.domains.models import OperationalDomain
from app.core.domains.system_domains import SYSTEM_DOMAINS


def discover_system_domains() -> list[OperationalDomain]:
    """
    Discover SentinelAI's foundational operational domains.

    Discovery observes available system domains.

    It does not validate, activate, compose, or interpret them.
    """

    return list(SYSTEM_DOMAINS)
