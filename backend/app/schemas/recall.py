from pydantic import BaseModel, Field


class RecallGeneration(BaseModel):
    """
    Structured language-model output for evidence-based Recall.

    Retrieval confidence remains deterministic and is calculated
    separately by ReasoningService.
    """

    answer: str = Field(
        description=(
            "A concise answer grounded only in the supplied evidence."
        )
    )

    confidence_basis: str = Field(
        description=(
            "A concise explanation of why the supplied evidence "
            "supports or limits the answer."
        )
    )

    recommended_next_step: str = Field(
        description=(
            "One practical next action based on the answer."
        )
    )

    suggested_follow_up: str = Field(
        description=(
            "One natural follow-up question that continues the inquiry."
        )
    )

    related_topics: list[str] = Field(
        default_factory=list,
        description=(
            "Two to five short knowledge-topic labels derived from "
            "the supplied evidence."
        ),
    )
