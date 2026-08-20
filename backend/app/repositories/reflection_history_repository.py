"""
Persistent Reflection History Repository for SentinelAI.

This repository stores ReflectionRecord domain objects through
SQLAlchemy while preserving append-only historical integrity.

It does not:

- rewrite historical Reflection,
- interpret cognition,
- repair Reflection,
- execute Recommendations.
"""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.models.reflection_history import (
    ReflectionHistoryRecordModel,
)

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)

from app.services.cognition.reflection.reflection_history_repository import (
    DuplicatePersistedReflectionError,
)


class PersistentReflectionHistoryRepository:
    """
    SQLAlchemy-backed Reflection history repository.
    """

    def __init__(
        self,
        db,
    ) -> None:
        self.db = db

    @staticmethod
    def _to_model(
        record: ReflectionRecord,
    ) -> ReflectionHistoryRecordModel:
        return ReflectionHistoryRecordModel(
            reflection_id=record.reflection_id,
            mission_id=record.mission_id,
            session_id=record.session_id,
            organization_id=record.organization_id,
            reflected_at=(
                record.reflected_at.isoformat()
            ),
            learning_event_ids=list(
                record.learning_event_ids
            ),
            pattern_ids=list(
                record.pattern_ids
            ),
            insight_ids=list(
                record.insight_ids
            ),
            recommendation_ids=list(
                record.recommendation_ids
            ),
            status=record.status,
            reflection_confidence_score=(
                record.reflection_confidence_score
            ),
            reflection_confidence_level=(
                record.reflection_confidence_level
            ),
            coherent=record.coherent,
            constitutional_score=(
                record.constitutional_score
            ),
            admissible=record.admissible,
            longitudinal_understanding_ids=list(
                record.longitudinal_understanding_ids
            ),
            reflective_trends=list(
                record.reflective_trends
            ),
        )

    @staticmethod
    def _to_record(
        model: ReflectionHistoryRecordModel,
    ) -> ReflectionRecord:
        return ReflectionRecord(
            reflection_id=model.reflection_id,
            mission_id=model.mission_id,
            session_id=model.session_id,
            organization_id=model.organization_id,
            reflected_at=datetime.fromisoformat(
                model.reflected_at
            ),
            learning_event_ids=list(
                model.learning_event_ids
                or []
            ),
            pattern_ids=list(
                model.pattern_ids
                or []
            ),
            insight_ids=list(
                model.insight_ids
                or []
            ),
            recommendation_ids=list(
                model.recommendation_ids
                or []
            ),
            status=model.status,
            reflection_confidence_score=(
                model.reflection_confidence_score
            ),
            reflection_confidence_level=(
                model.reflection_confidence_level
            ),
            coherent=model.coherent,
            constitutional_score=(
                model.constitutional_score
            ),
            admissible=model.admissible,
            longitudinal_understanding_ids=list(
                model.longitudinal_understanding_ids
                or []
            ),
            reflective_trends=list(
                model.reflective_trends
                or []
            ),
        )

    def save(
        self,
        record: ReflectionRecord,
    ) -> None:
        """
        Persist one historical Reflection.

        Existing Reflection identities may not be overwritten.
        """

        existing = (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .filter(
                ReflectionHistoryRecordModel.reflection_id
                == record.reflection_id
            )
            .first()
        )

        if existing is not None:
            raise DuplicatePersistedReflectionError(
                "Reflection "
                f"'{record.reflection_id}' "
                "already exists."
            )

        model = self._to_model(
            record
        )

        try:
            self.db.add(
                model
            )

            self.db.commit()

        except IntegrityError as exc:
            self.db.rollback()

            raise DuplicatePersistedReflectionError(
                "Reflection "
                f"'{record.reflection_id}' "
                "already exists."
            ) from exc

    def get(
        self,
        reflection_id: str,
    ) -> ReflectionRecord | None:
        model = (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .filter(
                ReflectionHistoryRecordModel.reflection_id
                == reflection_id
            )
            .first()
        )

        if model is None:
            return None

        return self._to_record(
            model
        )

    def for_mission(
        self,
        mission_id: str,
    ) -> list[ReflectionRecord]:
        models = (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .filter(
                ReflectionHistoryRecordModel.mission_id
                == mission_id
            )
            .order_by(
                ReflectionHistoryRecordModel.reflected_at.asc(),
                ReflectionHistoryRecordModel.reflection_id.asc(),
            )
            .all()
        )

        return [
            self._to_record(
                model
            )
            for model in models
        ]

    def for_organization(
        self,
        organization_id: str,
    ) -> list[ReflectionRecord]:
        models = (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .filter(
                ReflectionHistoryRecordModel.organization_id
                == organization_id
            )
            .order_by(
                ReflectionHistoryRecordModel.reflected_at.asc(),
                ReflectionHistoryRecordModel.reflection_id.asc(),
            )
            .all()
        )

        return [
            self._to_record(
                model
            )
            for model in models
        ]

    def chronological(
        self,
    ) -> list[ReflectionRecord]:
        models = (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .order_by(
                ReflectionHistoryRecordModel.reflected_at.asc(),
                ReflectionHistoryRecordModel.reflection_id.asc(),
            )
            .all()
        )

        return [
            self._to_record(
                model
            )
            for model in models
        ]

    @property
    def count(self) -> int:
        return (
            self.db.query(
                ReflectionHistoryRecordModel
            )
            .count()
        )
