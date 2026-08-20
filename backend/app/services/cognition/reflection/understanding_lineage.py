"""
Understanding Lineage for SentinelAI Reflection.

Understanding Lineage represents explicit historical relationships
between authoritative Understanding states.

Lineage must be declared.

Similarity is not lineage.

This component owns structural lineage only. It does not determine
whether an Understanding actually became stronger, weaker, revised,
or contradicted. Those judgments belong to Understanding Evolution
Analysis.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from app.core.cognition.models import Understanding


class UnderstandingLineageKind(StrEnum):
    """
    Declared relationship kinds between Understanding states.
    """

    REVISED = "revised"
    STRENGTHENED = "strengthened"
    WEAKENED = "weakened"
    CONTRADICTED = "contradicted"


class UnderstandingLineageEdge(BaseModel):
    """
    One explicit directed relationship between Understanding states.
    """

    earlier_understanding_id: str
    later_understanding_id: str
    kind: UnderstandingLineageKind


class UnderstandingLineageValidationError(ValueError):
    """
    Raised when declared Understanding lineage is structurally invalid.
    """


class UnderstandingLineage:
    """
    Validated directed acyclic lineage of authoritative Understandings.
    """

    def __init__(
        self,
        *,
        understandings: dict[str, Understanding],
        edges: list[UnderstandingLineageEdge],
    ) -> None:
        self.understandings = dict(
            understandings
        )

        self.edges = list(
            edges
        )

        self._validate()

    def _validate(self) -> None:
        """
        Require structurally coherent declared lineage.
        """

        seen_edges: set[
            tuple[
                str,
                str,
                UnderstandingLineageKind,
            ]
        ] = set()

        for edge in self.edges:
            earlier_id = (
                edge.earlier_understanding_id
            )

            later_id = (
                edge.later_understanding_id
            )

            if (
                earlier_id
                not in self.understandings
            ):
                raise UnderstandingLineageValidationError(
                    "Unknown earlier Understanding "
                    f"'{earlier_id}'."
                )

            if (
                later_id
                not in self.understandings
            ):
                raise UnderstandingLineageValidationError(
                    "Unknown later Understanding "
                    f"'{later_id}'."
                )

            if earlier_id == later_id:
                raise UnderstandingLineageValidationError(
                    "An Understanding cannot have lineage "
                    "to itself."
                )

            signature = (
                earlier_id,
                later_id,
                edge.kind,
            )

            if signature in seen_edges:
                raise UnderstandingLineageValidationError(
                    "Duplicate Understanding lineage edge: "
                    f"{earlier_id} -> {later_id}."
                )

            seen_edges.add(
                signature
            )

        if self._contains_cycle():
            raise UnderstandingLineageValidationError(
                "Understanding lineage contains a cycle."
            )

    def _contains_cycle(self) -> bool:
        """
        Detect directed cycles without modifying lineage.
        """

        adjacency: dict[
            str,
            list[str],
        ] = {
            understanding_id: []
            for understanding_id
            in self.understandings
        }

        for edge in self.edges:
            adjacency[
                edge.earlier_understanding_id
            ].append(
                edge.later_understanding_id
            )

        visiting: set[str] = set()
        visited: set[str] = set()

        def visit(
            understanding_id: str,
        ) -> bool:
            if understanding_id in visiting:
                return True

            if understanding_id in visited:
                return False

            visiting.add(
                understanding_id
            )

            for successor_id in adjacency.get(
                understanding_id,
                [],
            ):
                if visit(
                    successor_id
                ):
                    return True

            visiting.remove(
                understanding_id
            )

            visited.add(
                understanding_id
            )

            return False

        return any(
            visit(
                understanding_id
            )
            for understanding_id
            in adjacency
            if understanding_id
            not in visited
        )

    def successors(
        self,
        understanding_id: str,
    ) -> list[str]:
        """
        Return directly declared successors in declaration order.
        """

        return [
            edge.later_understanding_id
            for edge in self.edges
            if (
                edge.earlier_understanding_id
                == understanding_id
            )
        ]

    def predecessors(
        self,
        understanding_id: str,
    ) -> list[str]:
        """
        Return directly declared predecessors in declaration order.
        """

        return [
            edge.earlier_understanding_id
            for edge in self.edges
            if (
                edge.later_understanding_id
                == understanding_id
            )
        ]

    def chain_from(
        self,
        understanding_id: str,
    ) -> list[str]:
        """
        Follow one unambiguous declared lineage chain.

        Branching is intentionally not interpreted here. If multiple
        direct successors exist, this method refuses to manufacture a
        preferred historical path.
        """

        if (
            understanding_id
            not in self.understandings
        ):
            raise UnderstandingLineageValidationError(
                "Unknown Understanding "
                f"'{understanding_id}'."
            )

        chain = [
            understanding_id
        ]

        current_id = understanding_id

        while True:
            successors = self.successors(
                current_id
            )

            if not successors:
                break

            if len(successors) > 1:
                raise UnderstandingLineageValidationError(
                    "Understanding lineage branches from "
                    f"'{current_id}' and cannot be represented "
                    "as one unambiguous chain."
                )

            current_id = successors[0]

            chain.append(
                current_id
            )

        return chain
