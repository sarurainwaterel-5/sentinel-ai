"""
Public API contracts for SentinelAI Reflection.

These models define the external Reflection boundary.

The API contract:

- identifies the historical Learning Events to examine,
- carries Reflection mission context,
- preserves governed Reflection status,
- preserves confidence and constitutional coherence separately,
- preserves human-approval requirements,
- exposes deterministic communication.

The API contract does not:

- perform Reflection,
- reconstruct historical cognition,
- discover Patterns,
- generate Insights,
- generate Recommendations,
- determine constitutional coherence,
- authorize execution.
"""

from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class ReflectionAPIRequest(BaseModel):
    """
    Public request for one governed Reflection operation.

    Learning Event IDs identify authoritative historical cognition.

    The caller does not provide Patterns, Insights, or Recommendations.
    """

    title: str = Field(
        min_length=1,
    )

    learning_event_ids: list[str] = Field(
        min_length=1,
    )

    constitutional_context: str = Field(
        min_length=1,
    )

    mission_id: str | None = None

    session_id: str | None = None

    organization_id: str = "default"

    @field_validator(
        "title",
        "constitutional_context",
        "organization_id",
        mode="before",
    )
    @classmethod
    def reject_blank_required_text(
        cls,
        value,
    ):
        if isinstance(value, str):
            value = value.strip()

            if not value:
                raise ValueError(
                    "Required text cannot be blank."
                )

        return value

    @field_validator(
        "learning_event_ids",
    )
    @classmethod
    def preserve_unique_event_ids(
        cls,
        value: list[str],
    ) -> list[str]:
        """
        Preserve caller-supplied provenance order while rejecting
        blank identities and removing duplicates.
        """

        cleaned: list[str] = []

        for event_id in value:
            normalized = event_id.strip()

            if not normalized:
                raise ValueError(
                    "Learning Event IDs cannot be blank."
                )

            if normalized not in cleaned:
                cleaned.append(
                    normalized
                )

        if not cleaned:
            raise ValueError(
                "At least one Learning Event ID is required."
            )

        return cleaned


class ReflectionAPIResponse(BaseModel):
    """
    Public summary of one governed Reflection operation.

    Confidence and constitutional coherence remain independent
    dimensions.

    This response grants no execution authority.
    """

    title: str = Field(
        min_length=1,
    )

    status: str = Field(
        min_length=1,
    )

    admissible: bool

    coherent: bool

    reflection_confidence_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    reflection_confidence_level: str = Field(
        min_length=1,
    )

    constitutional_score: float = Field(
        ge=0.0,
        le=1.0,
    )

    learning_event_ids: list[str] = Field(
        default_factory=list,
    )

    pattern_count: int = Field(
        ge=0,
    )

    insight_count: int = Field(
        ge=0,
    )

    recommendation_count: int = Field(
        ge=0,
    )

    human_approval_required: bool

    formatted_reflection: str = Field(
        min_length=1,
    )

    mission_id: str | None = None

    session_id: str | None = None

    organization_id: str = "default"
