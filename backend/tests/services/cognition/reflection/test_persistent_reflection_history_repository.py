"""
Contract 025 — Persistent Reflection History Repository.

This contract establishes process-boundary persistence semantics for
historical ReflectionRecords through SentinelAI's SQLAlchemy
architecture.

It must preserve:

- identity,
- mission/session/organization context,
- exact Reflection timestamp,
- Learning Event provenance,
- Pattern/Insight/Recommendation provenance,
- Reflection status,
- Reflection confidence,
- constitutional judgment,
- longitudinal Understanding provenance,
- reflective trends.

Persistence remains append-only.

A new Session and Repository instance must recover the same historical
ReflectionRecord.
"""

from datetime import UTC, datetime

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base

from app.models.reflection_history import (
    ReflectionHistoryRecordModel,
)

from app.repositories.reflection_history_repository import (
    PersistentReflectionHistoryRepository,
)

from app.services.cognition.reflection.reflection_history import (
    ReflectionRecord,
)

from app.services.cognition.reflection.reflection_history_repository import (
    DuplicatePersistedReflectionError,
)


def make_record(
    *,
    reflection_id: str = "reflection-001",
    mission_id: str = "mission-001",
    organization_id: str = "default",
    status: str = "complete",
    confidence_score: float = 0.86,
    confidence_level: str = "high",
    coherent: bool = True,
    constitutional_score: float = 1.0,
    admissible: bool = True,
) -> ReflectionRecord:
    return ReflectionRecord(
        reflection_id=reflection_id,
        mission_id=mission_id,
        session_id="sprint-18",
        organization_id=organization_id,
        reflected_at=datetime(
            2026,
            8,
            18,
            14,
            30,
            15,
            123456,
            tzinfo=UTC,
        ),
        learning_event_ids=[
            "learning-1",
            "learning-2",
        ],
        pattern_ids=[
            "pattern-1",
            "pattern-2",
        ],
        insight_ids=[
            "insight-1",
        ],
        recommendation_ids=[
            "recommendation-1",
        ],
        status=status,
        reflection_confidence_score=(
            confidence_score
        ),
        reflection_confidence_level=(
            confidence_level
        ),
        coherent=coherent,
        constitutional_score=(
            constitutional_score
        ),
        admissible=admissible,
        longitudinal_understanding_ids=[
            "understanding-v1",
            "understanding-v2",
        ],
        reflective_trends=[
            "revision",
            "reinforcement",
        ],
    )


@pytest.fixture
def session_factory(tmp_path):
    database_path = (
        tmp_path
        / "reflection-history.sqlite3"
    )

    engine = create_engine(
        f"sqlite:///{database_path}"
    )

    Base.metadata.create_all(
        bind=engine,
        tables=[
            ReflectionHistoryRecordModel.__table__,
        ],
    )

    factory = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=engine,
    )

    yield factory

    engine.dispose()


def test_repository_persists_and_retrieves_record(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        record = make_record()

        repository.save(record)

        loaded = repository.get(
            "reflection-001"
        )

        assert loaded == record

    finally:
        db.close()


def test_history_survives_new_session_and_repository(
    session_factory,
):
    first_db = session_factory()

    first_repository = (
        PersistentReflectionHistoryRepository(
            first_db
        )
    )

    record = make_record()

    first_repository.save(record)

    first_db.close()

    second_db = session_factory()

    try:
        second_repository = (
            PersistentReflectionHistoryRepository(
                second_db
            )
        )

        loaded = second_repository.get(
            "reflection-001"
        )

        assert loaded == record

    finally:
        second_db.close()


def test_unknown_reflection_returns_none(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        assert repository.get(
            "reflection-missing"
        ) is None

    finally:
        db.close()


def test_duplicate_identity_cannot_overwrite_history(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-001",
            )
        )

        with pytest.raises(
            DuplicatePersistedReflectionError,
            match="reflection-001",
        ):
            repository.save(
                make_record(
                    reflection_id="reflection-001",
                    mission_id="different-mission",
                )
            )

        loaded = repository.get(
            "reflection-001"
        )

        assert loaded is not None
        assert loaded.mission_id == "mission-001"

    finally:
        db.close()


def test_insufficient_reflection_survives_persistence(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-001a",
                status="insufficient_evidence",
                confidence_score=0.263,
                confidence_level="low",
            )
        )

        loaded = repository.get(
            "reflection-001a"
        )

        assert loaded is not None

        assert (
            loaded.status
            == "insufficient_evidence"
        )

        assert (
            loaded.reflection_confidence_score
            == 0.263
        )

        assert (
            loaded.reflection_confidence_level
            == "low"
        )

    finally:
        db.close()


def test_provenance_survives_database_round_trip(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record()
        )

        loaded = repository.get(
            "reflection-001"
        )

        assert loaded is not None

        assert loaded.learning_event_ids == [
            "learning-1",
            "learning-2",
        ]

        assert loaded.pattern_ids == [
            "pattern-1",
            "pattern-2",
        ]

        assert loaded.insight_ids == [
            "insight-1",
        ]

        assert loaded.recommendation_ids == [
            "recommendation-1",
        ]

    finally:
        db.close()


def test_longitudinal_history_survives_database_round_trip(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record()
        )

        loaded = repository.get(
            "reflection-001"
        )

        assert loaded is not None

        assert (
            loaded.longitudinal_understanding_ids
            == [
                "understanding-v1",
                "understanding-v2",
            ]
        )

        assert loaded.reflective_trends == [
            "revision",
            "reinforcement",
        ]

    finally:
        db.close()


def test_constitutional_judgment_survives_database_round_trip(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record(
                coherent=False,
                constitutional_score=0.40,
                admissible=False,
            )
        )

        loaded = repository.get(
            "reflection-001"
        )

        assert loaded is not None
        assert loaded.coherent is False

        assert (
            loaded.constitutional_score
            == 0.40
        )

        assert loaded.admissible is False

    finally:
        db.close()


def test_timestamp_survives_database_round_trip_exactly(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        record = make_record()

        repository.save(record)

        loaded = repository.get(
            record.reflection_id
        )

        assert loaded is not None
        assert loaded.reflected_at == (
            record.reflected_at
        )

    finally:
        db.close()


def test_repository_filters_by_mission(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-001a",
                mission_id="mission-001",
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-001b",
                mission_id="mission-001",
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-002",
                mission_id="mission-002",
            )
        )

        results = repository.for_mission(
            "mission-001"
        )

        assert [
            record.reflection_id
            for record in results
        ] == [
            "reflection-001a",
            "reflection-001b",
        ]

    finally:
        db.close()


def test_repository_filters_by_organization(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-default",
                organization_id="default",
            )
        )

        repository.save(
            make_record(
                reflection_id="reflection-other",
                organization_id="other",
            )
        )

        results = (
            repository.for_organization(
                "default"
            )
        )

        assert [
            record.reflection_id
            for record in results
        ] == [
            "reflection-default",
        ]

    finally:
        db.close()


def test_repository_returns_stable_chronology(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        later = make_record(
            reflection_id="reflection-later",
        )

        earlier = later.model_copy(
            deep=True,
            update={
                "reflection_id": (
                    "reflection-earlier"
                ),
                "reflected_at": datetime(
                    2026,
                    8,
                    17,
                    12,
                    0,
                    tzinfo=UTC,
                ),
            },
        )

        repository.save(later)
        repository.save(earlier)

        results = repository.chronological()

        assert [
            record.reflection_id
            for record in results
        ] == [
            "reflection-earlier",
            "reflection-later",
        ]

    finally:
        db.close()


def test_repository_count_survives_new_session(
    session_factory,
):
    first_db = session_factory()

    first_repository = (
        PersistentReflectionHistoryRepository(
            first_db
        )
    )

    first_repository.save(
        make_record(
            reflection_id="reflection-001",
        )
    )

    first_repository.save(
        make_record(
            reflection_id="reflection-002",
        )
    )

    first_db.close()

    second_db = session_factory()

    try:
        second_repository = (
            PersistentReflectionHistoryRepository(
                second_db
            )
        )

        assert second_repository.count == 2

    finally:
        second_db.close()


def test_repository_has_no_update_delete_or_execution_authority(
    session_factory,
):
    db = session_factory()

    try:
        repository = (
            PersistentReflectionHistoryRepository(
                db
            )
        )

        forbidden = [
            "update",
            "replace",
            "overwrite",
            "delete",
            "remove",
            "rewrite",
            "repair",
            "execute",
        ]

        for name in forbidden:
            assert not hasattr(
                repository,
                name,
            )

    finally:
        db.close()
