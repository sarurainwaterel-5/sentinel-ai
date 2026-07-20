from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from app.core.cognition.models import CognitiveRegistry


ValidationLevel = Literal["pass", "warning", "error"]


@dataclass(slots=True)
class CognitiveValidationCheck:
    """
    One structural validation performed against the Cognitive Registry.
    """

    object_type: str
    object_id: str
    name: str
    level: ValidationLevel
    message: str

    @property
    def passed(self) -> bool:
        return self.level == "pass"


@dataclass(slots=True)
class CognitiveValidationReport:
    """
    Structural validation result for SentinelAI's cognitive state.
    """

    status: str
    passed: int
    warnings: int
    errors: int
    checks: list[CognitiveValidationCheck] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def add_check(
    checks: list[CognitiveValidationCheck],
    *,
    object_type: str,
    object_id: str,
    name: str,
    condition: bool,
    success_message: str,
    failure_message: str,
    failure_level: ValidationLevel = "error",
) -> None:
    """
    Record a validation result without modifying cognitive state.
    """

    checks.append(
        CognitiveValidationCheck(
            object_type=object_type,
            object_id=object_id,
            name=name,
            level="pass" if condition else failure_level,
            message=success_message if condition else failure_message,
        )
    )


def validate_unique_ids(
    *,
    object_type: str,
    object_ids: list[str],
    checks: list[CognitiveValidationCheck],
) -> None:
    """
    Verify that cognitive objects have defined and unique identifiers.
    """

    seen_ids: set[str] = set()

    for object_id in object_ids:
        display_id = object_id or "<missing>"

        add_check(
            checks,
            object_type=object_type,
            object_id=display_id,
            name="id_defined",
            condition=bool(object_id.strip()),
            success_message=f"{object_type.title()} identifier is defined.",
            failure_message=f"{object_type.title()} identifier is missing.",
        )

        add_check(
            checks,
            object_type=object_type,
            object_id=display_id,
            name="id_unique",
            condition=object_id not in seen_ids,
            success_message=(
                f"{object_type.title()} identifier is unique."
            ),
            failure_message=(
                f"Duplicate {object_type} identifier "
                f"'{display_id}' was found."
            ),
        )

        seen_ids.add(object_id)


def validate_cognitive_registry(
    registry: CognitiveRegistry,
) -> CognitiveValidationReport:
    """
    Validate SentinelAI's assembled cognitive state.

    Validator responsibilities:

    - Verify structural coherence.
    - Report duplicate or missing identifiers.
    - Preserve all supplied cognitive objects.

    Validator non-responsibilities:

    - Repairing cognitive state
    - Deduplicating cognitive objects
    - Determining factual truth
    - Extracting knowledge
    - Performing reasoning
    """

    checks: list[CognitiveValidationCheck] = []

    validate_unique_ids(
        object_type="observation",
        object_ids=[
            observation.observation_id
            for observation in registry.observations
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="evidence",
        object_ids=[
            evidence.evidence_id
            for evidence in registry.evidence
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="concept",
        object_ids=[
            concept.concept_id
            for concept in registry.concepts
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="principle",
        object_ids=[
            principle.principle_id
            for principle in registry.principles
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="relationship",
        object_ids=[
            relationship.relationship_id
            for relationship in registry.relationships
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="understanding",
        object_ids=[
            understanding.understanding_id
            for understanding in registry.understandings
        ],
        checks=checks,
    )

    validate_unique_ids(
        object_type="learning_event",
        object_ids=[
            event.learning_event_id
            for event in registry.learning_events
        ],
        checks=checks,
    )

    passed = sum(check.level == "pass" for check in checks)
    warnings = sum(check.level == "warning" for check in checks)
    errors = sum(check.level == "error" for check in checks)

    if errors:
        status = "invalid"
    elif warnings:
        status = "valid_with_warnings"
    else:
        status = "valid"

    return CognitiveValidationReport(
        status=status,
        passed=passed,
        warnings=warnings,
        errors=errors,
        checks=checks,
    )
