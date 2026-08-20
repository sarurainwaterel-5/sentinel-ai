"""
Learning Event Resolver for SentinelAI Reflection.

The Resolver translates requested Learning Event identities into
authoritative cognitive history.

It does not:

- create Learning Events,
- reconstruct history from caller payloads,
- modify stored Learning Events,
- discover Patterns,
- generate Insights,
- perform Reflection,
- interpret meaning.

The Repository owns history.

The Resolver locates history.
"""

from __future__ import annotations

from app.core.cognition.models import (
    LearningEvent,
)

from app.repositories.learning_event_repository import (
    LearningEventRepository,
)


class LearningEventResolver:
    """
    Resolve Learning Event identities through the authoritative repository.
    """

    def __init__(
        self,
        *,
        repository: LearningEventRepository,
    ):
        self.repository = repository

    def resolve(
        self,
        learning_event_ids: list[str],
    ) -> list[LearningEvent]:
        """
        Resolve authoritative Learning Events in requested order.

        Duplicate IDs are resolved once by the repository contract.

        Missing IDs fail visibly through repository authority.
        """

        if not learning_event_ids:
            return []

        return self.repository.get_many(
            learning_event_ids
        )
