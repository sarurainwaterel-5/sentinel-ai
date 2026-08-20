"""
Contract 026 — Reproducible Reflection History Migration.

SentinelAI's persistent cognitive history must be reconstructable from
version-controlled schema migrations.

The migration must:

- create the reflection_history table,
- preserve the fields required by ReflectionRecord,
- remove the table on downgrade,
- recreate the table on a subsequent upgrade.

A working developer database is not sufficient.

The schema must be reproducible from source.
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import (
    create_engine,
    inspect,
)


@pytest.fixture
def migrated_database(tmp_path):
    database_path = (
        tmp_path
        / "sentinel-reflection-migration.sqlite3"
    )

    database_url = (
        f"sqlite:///{database_path}"
    )

    config = Config(
        "alembic.ini"
    )

    config.set_main_option(
        "sqlalchemy.url",
        database_url,
    )

    yield (
        config,
        database_url,
    )


def table_names(
    database_url: str,
) -> set[str]:
    engine = create_engine(
        database_url
    )

    try:
        return set(
            inspect(
                engine
            ).get_table_names()
        )
    finally:
        engine.dispose()


def column_names(
    database_url: str,
    table_name: str,
) -> set[str]:
    engine = create_engine(
        database_url
    )

    try:
        columns = inspect(
            engine
        ).get_columns(
            table_name
        )

        return {
            column["name"]
            for column in columns
        }
    finally:
        engine.dispose()


def test_upgrade_creates_reflection_history_table(
    migrated_database,
):
    config, database_url = (
        migrated_database
    )

    command.upgrade(
        config,
        "head",
    )

    assert (
        "reflection_history"
        in table_names(
            database_url
        )
    )


def test_migration_contains_required_reflection_columns(
    migrated_database,
):
    config, database_url = (
        migrated_database
    )

    command.upgrade(
        config,
        "head",
    )

    columns = column_names(
        database_url,
        "reflection_history",
    )

    required = {
        "reflection_id",
        "mission_id",
        "session_id",
        "organization_id",
        "reflected_at",
        "learning_event_ids",
        "pattern_ids",
        "insight_ids",
        "recommendation_ids",
        "status",
        "reflection_confidence_score",
        "reflection_confidence_level",
        "coherent",
        "constitutional_score",
        "admissible",
        "longitudinal_understanding_ids",
        "reflective_trends",
    }

    assert required.issubset(
        columns
    )


def test_reflection_id_is_primary_key(
    migrated_database,
):
    config, database_url = (
        migrated_database
    )

    command.upgrade(
        config,
        "head",
    )

    engine = create_engine(
        database_url
    )

    try:
        primary_key = inspect(
            engine
        ).get_pk_constraint(
            "reflection_history"
        )

        assert primary_key[
            "constrained_columns"
        ] == [
            "reflection_id"
        ]

    finally:
        engine.dispose()


def test_downgrade_removes_reflection_history_table(
    migrated_database,
):
    config, database_url = (
        migrated_database
    )

    command.upgrade(
        config,
        "head",
    )

    assert (
        "reflection_history"
        in table_names(
            database_url
        )
    )

    command.downgrade(
        config,
        "base",
    )

    assert (
        "reflection_history"
        not in table_names(
            database_url
        )
    )


def test_upgrade_after_downgrade_recreates_schema(
    migrated_database,
):
    config, database_url = (
        migrated_database
    )

    command.upgrade(
        config,
        "head",
    )

    command.downgrade(
        config,
        "base",
    )

    command.upgrade(
        config,
        "head",
    )

    assert (
        "reflection_history"
        in table_names(
            database_url
        )
    )

    columns = column_names(
        database_url,
        "reflection_history",
    )

    assert (
        "reflection_id"
        in columns
    )

    assert (
        "learning_event_ids"
        in columns
    )

    assert (
        "constitutional_score"
        in columns
    )


def test_migration_does_not_depend_on_application_runtime_table_creation(
    migrated_database,
):
    """
    The migration itself must create the table.

    Base.metadata.create_all() is intentionally never called in this
    contract.
    """

    config, database_url = (
        migrated_database
    )

    assert (
        "reflection_history"
        not in table_names(
            database_url
        )
    )

    command.upgrade(
        config,
        "head",
    )

    assert (
        "reflection_history"
        in table_names(
            database_url
        )
    )
