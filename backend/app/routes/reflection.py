"""
Public HTTP boundary for SentinelAI Reflection.

HTTP owns transport.

ReflectionApplicationService owns workflow.

The route does not:

- resolve Learning Events,
- perform Reflection,
- calculate confidence,
- determine constitutional coherence,
- format Reflection,
- execute Recommendations.
"""

from pathlib import Path

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db

from app.repositories.reflection_history_repository import (
    PersistentReflectionHistoryRepository,
)

from app.services.cognition.reflection.reflection_record_factory import (
    ReflectionRecordFactory,
)

from app.repositories.learning_event_repository import (
    LearningEventRepository,
)

from app.services.cognition.reflection.learning_event_resolver import (
    LearningEventResolver,
)

from app.services.cognition.reflection.reflection_api import (
    ReflectionAPIRequest,
    ReflectionAPIResponse,
)

from app.services.cognition.reflection.reflection_application_service import (
    ReflectionApplicationService,
)

from app.services.cognition.reflection.reflection_formatter import (
    ReflectionFormatter,
)

from app.services.cognition.reflection.reflection_orchestrator import (
    ReflectionOrchestrator,
)


router = APIRouter(
    prefix="/reflection",
    tags=["Reflection"],
)


DATABASE_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "learning-events.sqlite3"
)


repository = LearningEventRepository(
    database_path=DATABASE_PATH
)

resolver = LearningEventResolver(
    repository=repository
)

orchestrator = ReflectionOrchestrator()

formatter = ReflectionFormatter()

record_factory = ReflectionRecordFactory()


@router.post(
    "",
    response_model=ReflectionAPIResponse,
)
def reflect(
    request: ReflectionAPIRequest,
    db: Session = Depends(get_db),
) -> ReflectionAPIResponse:
    """
    Execute one governed Reflection operation and preserve its
    historical result.
    """

    history_repository = (
        PersistentReflectionHistoryRepository(
            db
        )
    )

    application_service = (
        ReflectionApplicationService(
            resolver=resolver,
            orchestrator=orchestrator,
            formatter=formatter,
            record_factory=record_factory,
            history_repository=(
                history_repository
            ),
        )
    )

    return application_service.reflect(
        request
    )
