"""
Semantic premise relationship evaluation for SentinelAI.

This module defines the bounded contract used by semantic
relationship evaluation.

Semantic assessment may classify how two propositions relate.

It does not:

- create evidence,
- create premises,
- synthesize propositions,
- form conclusions,
- determine proposition truth,
- or calculate conclusion confidence.

Its confidence value represents confidence in the semantic
relationship classification only.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

import os

from dotenv import load_dotenv
from openai import OpenAI

from app.services.cognition.reasoning.models import (
    Premise,
)


load_dotenv()


class SemanticRelationshipAssessment(BaseModel):
    """
    Structured candidate judgment about the semantic relationship
    between two evidence-grounded Premises.

    This assessment is not itself an authoritative reasoning
    conclusion.
    """

    relationship: Literal[
        "supports",
        "conflicts",
        "complements",
        "unresolved",
    ]

    basis: str = Field(
        min_length=1,
    )

    confidence: float = Field(
        ge=0.0,
        le=1.0,
    )
class SemanticPremiseRelationshipEvaluator:
    """
    Evaluate the semantic relationship between two Premises.

    The evaluator may classify a relationship as:

    - supports,
    - conflicts,
    - complements,
    - unresolved.

    It does not determine proposition truth or synthesize
    higher-order propositions.
    """

    def __init__(
        self,
        *,
        client=None,
        model: str = "gpt-4.1-mini",
    ):
        if client is None:
            api_key = os.getenv(
                "OPENAI_API_KEY"
            )

            if not api_key:
                raise RuntimeError(
                    "OPENAI_API_KEY is not configured."
                )

            client = OpenAI(
                api_key=api_key,
            )

        self.client = client
        self.model = model

    @staticmethod
    def _system_message() -> str:
        return (
            "You are SentinelAI's semantic premise "
            "relationship evaluator. "
            "You receive exactly two evidence-grounded "
            "propositions: SOURCE and TARGET. "
            "Classify only the semantic relationship from "
            "SOURCE to TARGET. "
            "\n\n"
            "Allowed relationships:\n"
            "- supports: SOURCE materially increases support "
            "for TARGET.\n"
            "- conflicts: SOURCE is materially incompatible "
            "with TARGET such that both claims cannot be "
            "accepted together without qualification.\n"
            "- complements: SOURCE and TARGET provide distinct "
            "but compatible information about a shared subject "
            "without SOURCE directly supporting TARGET.\n"
            "- unresolved: the supplied propositions do not "
            "provide enough information to establish one of "
            "the relationships above.\n"
            "\n"
            "Do not determine whether either proposition is "
            "true. Do not introduce outside facts. Do not "
            "invent evidence. Do not synthesize a new "
            "proposition. Do not infer causation unless it is "
            "explicitly contained in the propositions. "
            "When the relationship is ambiguous, choose "
            "unresolved. "
            "Confidence represents confidence in the "
            "relationship classification only, not confidence "
            "in proposition truth."
        )

    @staticmethod
    def _user_message(
        *,
        source: Premise,
        target: Premise,
    ) -> str:
        return (
            "Assess the semantic relationship from SOURCE "
            "to TARGET using only these propositions.\n\n"
            f"SOURCE:\n{source.statement}\n\n"
            f"TARGET:\n{target.statement}"
        )

    def evaluate(
        self,
        *,
        source: Premise,
        target: Premise,
    ) -> SemanticRelationshipAssessment:
        """
        Produce one bounded semantic relationship assessment.
        """

        completion = (
            self.client.chat.completions.parse(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            self._system_message()
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            self._user_message(
                                source=source,
                                target=target,
                            )
                        ),
                    },
                ],
                response_format=(
                    SemanticRelationshipAssessment
                ),
                temperature=0.0,
            )
        )

        message = (
            completion.choices[0].message
        )

        if message.refusal:
            raise RuntimeError(
                "Sentinel's semantic relationship "
                f"evaluation was refused: {message.refusal}"
            )

        assessment = message.parsed

        if assessment is None:
            raise RuntimeError(
                "Sentinel's semantic relationship evaluator "
                "returned no structured assessment."
            )

        return assessment
