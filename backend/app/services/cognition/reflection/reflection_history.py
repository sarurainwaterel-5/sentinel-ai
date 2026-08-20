"""
Durable Reflection History for SentinelAI.

A ReflectionRecord preserves the result of Reflection at a particular
moment in cognitive history.

Historical Reflection is append-only.

Future cognition may examine it.

Future cognition may not rewrite it.
"""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class DuplicateReflectionRecordError(ValueError):
    """
    Raised when a Reflection identity is appended more than once.
    """


class ReflectionRecord(BaseModel):
    """
    Immutable historical snapshot of one Reflection result.

    The model itself remains mutable for normal application use,
    but ReflectionHistory stores and returns defensive copies.
    """

    reflection_id: str = Field(
        min_length=1,
    )

    mission_id: str | None = None
    session_id: str | None = None
    organization_id: str = "default"

    reflected_at: datetime

    learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    pattern_ids: list[str] = Field(
        default_factory=list,
    )

    insight_ids: list[str] = Field(
        default_factory=list,
    )

    recommendation_ids: list[str] = Field(
        default_factory=list,
    )

    status: str = Field(
        min_length=1,
    )

    reflection_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reflection_confidence_level: str = Field(
        min_length=1,
    )

    coherent: bool

    constitutional_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    admissible: bool

    longitudinal_understanding_ids: list[str] = Field(
        default_factory=list,
    )

    reflective_trends: list[str] = Field(
        default_factory=list,
    )


class ReflectionHistory:
    """
    Append-only in-memory Reflection history with snapshot semantics.

    This class owns historical preservation only.

    Persistence to disk belongs to a later repository layer.
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
        Produce a deep defensive copy of one ReflectionRecord.
        """

        return record.model_copy(
            deep=True
        )

    @property
    def count(self) -> int:
        return len(
            self._records
        )

    def append(
        self,
        record: ReflectionRecord,
    ) -> None:
        """
        Append one immutable historical snapshot.

        Existing Reflection identities may not be overwritten.
        """

        if (
            record.reflection_id
            in self._by_id
        ):
            raise DuplicateReflectionRecordError(
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
        Return a defensive copy of one historical Reflection.
        """

        record = self._by_id.get(
            reflection_id
        )

        if record is None:
            return None

        return self._snapshot(
            record
        )

    def records(
        self,
    ) -> list[ReflectionRecord]:
        """
        Return a snapshot of all historical Reflection records.
        """

        return [
            self._snapshot(
                record
            )
            for record in self._records
        ]

    def for_mission(
        self,
        mission_id: str,
    ) -> list[ReflectionRecord]:
        """
        Return historical Reflection records for one mission in
        append order.
        """

        return [
            self._snapshot(
                record
            )
            for record in self._records
            if record.mission_id == mission_id
        ]

    def chronological(
        self,
    ) -> list[ReflectionRecord]:
        """
        Return history in stable chronological order.

        Python sorting is stable, so equal timestamps preserve
        append order.
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
