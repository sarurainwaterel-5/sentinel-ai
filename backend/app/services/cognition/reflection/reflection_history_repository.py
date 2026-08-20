"""
Reflection History Repository for SentinelAI.

This module establishes the repository boundary for historical
ReflectionRecords.

The repository preserves:

- append-only Reflection identity,
- historical record fidelity,
- stable chronology,
- mission and organization retrieval,
- defensive snapshot semantics.

This in-memory adapter establishes repository behavior only.

It does not provide process-restart durability.
It does not interpret, repair, rewrite, or execute cognition.
"""

from __future__ import annotations

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)


class DuplicatePersistedReflectionError(ValueError):
    """
    Raised when a persisted Reflection identity already exists.
    """


class InMemoryReflectionHistoryRepository:
    """
    Append-only in-memory repository for historical ReflectionRecords.

    All write and read boundaries use deep defensive copies so callers
    cannot mutate repository-owned historical state.
    """

    def __init__(self) -> None:
        self._records: list[
            ReflectionRecord
        ] = []

        self._by_id: dict[
            str,
            ReflectionRecord
        ] = {}

    @staticmethod
    def _snapshot(
        record: ReflectionRecord,
    ) -> ReflectionRecord:
        """
        Return a deep defensive copy of one historical record.
        """

        return record.model_copy(
            deep=True
        )

    @property
    def count(self) -> int:
        """
        Return the number of persisted Reflection records.
        """

        return len(
            self._records
        )

    def save(
        self,
        record: ReflectionRecord,
    ) -> None:
        """
        Persist one historical Reflection snapshot.

        Existing Reflection identities cannot be overwritten.
        """

        if (
            record.reflection_id
            in self._by_id
        ):
            raise DuplicatePersistedReflectionError(
                "Reflection "
                f"'{record.reflection_id}' "
                "already exists."
            )

        snapshot = self._snapshot(
            record
        )

        self._records.append(
            snapshot
        )

        self._by_id[
            snapshot.reflection_id
        ] = snapshot

    def get(
        self,
        reflection_id: str,
    ) -> ReflectionRecord | None:
        """
        Retrieve one historical Reflection by identity.
        """

        record = self._by_id.get(
            reflection_id
        )

        if record is None:
            return None

        return self._snapshot(
            record
        )

    def for_mission(
        self,
        mission_id: str,
    ) -> list[ReflectionRecord]:
        """
        Retrieve Reflection history for one mission in save order.
        """

        return [
            self._snapshot(
                record
            )
            for record in self._records
            if record.mission_id == mission_id
        ]

    def for_organization(
        self,
        organization_id: str,
    ) -> list[ReflectionRecord]:
        """
        Retrieve Reflection history for one organization in save order.
        """

        return [
            self._snapshot(
                record
            )
            for record in self._records
            if (
                record.organization_id
                == organization_id
            )
        ]

    def chronological(
        self,
    ) -> list[ReflectionRecord]:
        """
        Retrieve Reflection history in stable chronological order.

        Python's sort is stable. Equal timestamps therefore retain
        repository save order rather than manufacturing a secondary
        temporal ordering.
        """

        ordered = sorted(
            self._records,
            key=lambda record: (
                record.reflected_at
            ),
        )

        return [
            self._snapshot(
                record
            )
            for record in ordered
        ]
