"""
Durable Learning Event Repository for SentinelAI.

The repository preserves completed Learning Events as immutable
intellectual history.

It does not:

- discover Patterns,
- generate Insights,
- perform Reflection,
- modify Learning Events,
- rewrite cognitive history,
- interpret meaning,
- execute recommendations.

Learning records change.

The repository preserves that record.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.core.cognition.models import (
    LearningEvent,
)


class LearningEventNotFoundError(LookupError):
    """
    Raised when authoritative cognitive history cannot be found.
    """


class LearningEventRepository:
    """
    Durable persistence authority for Learning Events.

    Historical cognition is immutable by default.
    """

    def __init__(
        self,
        *,
        database_path: str | Path,
    ):
        self.database_path = Path(
            database_path
        )

        self.database_path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        self._initialize()

    def _connect(
        self,
    ) -> sqlite3.Connection:
        """
        Open one repository connection.
        """

        connection = sqlite3.connect(
            self.database_path
        )

        connection.row_factory = (
            sqlite3.Row
        )

        return connection

    def _initialize(
        self,
    ) -> None:
        """
        Ensure the durable Learning Event table exists.
        """

        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS learning_events (
                    learning_event_id TEXT PRIMARY KEY,
                    payload TEXT NOT NULL
                )
                """
            )

            connection.commit()

    @staticmethod
    def _serialize(
        event: LearningEvent,
    ) -> str:
        """
        Serialize one Learning Event without modifying it.
        """

        payload = event.to_dict()

        payload["learned_at"] = (
            event.learned_at.isoformat()
        )

        return json.dumps(
            payload,
            sort_keys=True,
        )

    @staticmethod
    def _deserialize(
        payload: str,
    ) -> LearningEvent:
        """
        Reconstruct one independent Learning Event object.
        """

        data = json.loads(
            payload
        )

        from datetime import datetime

        learned_at = datetime.fromisoformat(
            data["learned_at"]
        )

        return LearningEvent(
            learning_event_id=(
                data["learning_event_id"]
            ),
            source=data.get(
                "source",
                "",
            ),
            domain_ids=list(
                data.get(
                    "domain_ids",
                    [],
                )
            ),
            observations_added=list(
                data.get(
                    "observations_added",
                    [],
                )
            ),
            evidence_added=list(
                data.get(
                    "evidence_added",
                    [],
                )
            ),
            concepts_added=list(
                data.get(
                    "concepts_added",
                    [],
                )
            ),
            principles_added=list(
                data.get(
                    "principles_added",
                    [],
                )
            ),
            relationships_added=list(
                data.get(
                    "relationships_added",
                    [],
                )
            ),
            understandings_added=list(
                data.get(
                    "understandings_added",
                    [],
                )
            ),
            summary=data.get(
                "summary",
                "",
            ),
            learned_at=learned_at,
            metadata=dict(
                data.get(
                    "metadata",
                    {},
                )
            ),
        )

    def save(
        self,
        event: LearningEvent,
    ) -> None:
        """
        Persist one immutable Learning Event.

        Existing identities may not be silently overwritten.
        """

        payload = self._serialize(
            event
        )

        try:
            with self._connect() as connection:
                connection.execute(
                    """
                    INSERT INTO learning_events (
                        learning_event_id,
                        payload
                    )
                    VALUES (?, ?)
                    """,
                    (
                        event.learning_event_id,
                        payload,
                    ),
                )

                connection.commit()

        except sqlite3.IntegrityError as exc:
            raise ValueError(
                "Learning Event "
                f"'{event.learning_event_id}' "
                "already exists."
            ) from exc

    def get(
        self,
        learning_event_id: str,
    ) -> LearningEvent:
        """
        Retrieve one authoritative Learning Event.
        """

        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT payload
                FROM learning_events
                WHERE learning_event_id = ?
                """,
                (
                    learning_event_id,
                ),
            ).fetchone()

        if row is None:
            raise LearningEventNotFoundError(
                "Learning Event "
                f"'{learning_event_id}' "
                "was not found."
            )

        return self._deserialize(
            row["payload"]
        )

    def get_many(
        self,
        learning_event_ids: list[str],
    ) -> list[LearningEvent]:
        """
        Retrieve authoritative Learning Events in requested order.

        Duplicate identities resolve once.

        Missing identities fail visibly.
        """

        unique_ids = list(
            dict.fromkeys(
                learning_event_ids
            )
        )

        return [
            self.get(
                event_id
            )
            for event_id in unique_ids
        ]
