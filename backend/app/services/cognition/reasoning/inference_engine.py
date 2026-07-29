"""
Deterministic inference generation for SentinelAI.

The inference engine converts an EvidenceBundle into inspectable
candidate inferences without using an LLM.

Sprint 14 begins conservatively:

- inference statements remain close to source evidence,
- similar evidence statements may be grouped,
- provenance is preserved through evidence IDs,
- confidence reflects evidence quality and independence,
- limitations are explicit,
- conflicting evidence reduces confidence.

This service does not produce the final reasoning conclusion.
"""

from __future__ import annotations

import re
from collections import defaultdict

from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    EvidenceDisposition,
    EvidenceItem,
    Inference,
)


class InferenceEngine:
    """
    Produce conservative candidate inferences from organized evidence.

    The engine is intentionally domain-neutral and deterministic.
    Domain-specific inference rules can be added later without changing
    the public contract.
    """

    def __init__(
        self,
        *,
        similarity_threshold: float = 0.72,
        maximum_inferences: int = 8,
        statement_limit: int = 420,
    ):
        self.similarity_threshold = similarity_threshold
        self.maximum_inferences = maximum_inferences
        self.statement_limit = statement_limit

    @staticmethod
    def _evidence_id(
        item: EvidenceItem,
        fallback_index: int,
    ) -> str:
        stored_identity = item.source.metadata.get(
            "evidence_id"
        )

        if stored_identity:
            return str(stored_identity)

        document_identity = (
            item.source.document_id
            or item.source.file_hash
            or item.source.filename
            or "unknown-document"
        )

        chunk_identity = (
            item.source.chunk_index
            if item.source.chunk_index is not None
            else fallback_index
        )

        return f"{document_identity}:{chunk_identity}"

    @staticmethod
    def _normalize_whitespace(value: str) -> str:
        return re.sub(r"\s+", " ", value).strip()

    @classmethod
    def _first_complete_statement(
        cls,
        value: str,
    ) -> str:
        """
        Extract one bounded statement without inventing new language.

        The result stays close to the retrieved evidence rather than
        summarizing it through an external model.
        """

        cleaned = cls._normalize_whitespace(value)

        if not cleaned:
            return ""

        sentence_match = re.match(
            r"^(.+?[.!?])(?:\s|$)",
            cleaned,
        )

        if sentence_match:
            return sentence_match.group(1).strip()

        return cleaned

    def _bounded_statement(
        self,
        value: str,
    ) -> str:
        statement = self._first_complete_statement(value)

        if len(statement) <= self.statement_limit:
            return statement

        shortened = statement[
            : self.statement_limit
        ].rsplit(" ", 1)[0]

        return f"{shortened}…"

    @staticmethod
    def _tokens(value: str) -> set[str]:
        """
        Return meaningful lowercase tokens for deterministic overlap.

        Very short tokens are excluded because they add noise to
        similarity comparisons.
        """

        return {
            token
            for token in re.findall(
                r"[a-z0-9]+",
                value.casefold(),
            )
            if len(token) >= 3
        }

    @classmethod
    def _statement_similarity(
        cls,
        left: str,
        right: str,
    ) -> float:
        left_tokens = cls._tokens(left)
        right_tokens = cls._tokens(right)

        if not left_tokens or not right_tokens:
            return 0.0

        intersection = left_tokens & right_tokens
        union = left_tokens | right_tokens

        return len(intersection) / len(union)

    @staticmethod
    def _usable_items(
        bundle: EvidenceBundle,
    ) -> list[EvidenceItem]:
        """
        Prefer explicitly supporting evidence.

        When no claim-classification pass has occurred yet, contextual
        evidence remains eligible for conservative candidate inference.
        """

        if bundle.supporting:
            return bundle.supporting

        return bundle.contextual

    def _group_items(
        self,
        items: list[EvidenceItem],
    ) -> list[list[EvidenceItem]]:
        """
        Group evidence whose bounded statements substantially overlap.

        This is lexical grouping, not semantic equivalence. It therefore
        remains conservative and independently testable.
        """

        groups: list[list[EvidenceItem]] = []

        for item in items:
            statement = self._bounded_statement(
                item.statement
            )

            if not statement:
                continue

            matched_group = None

            for group in groups:
                representative = self._bounded_statement(
                    group[0].statement
                )

                similarity = self._statement_similarity(
                    statement,
                    representative,
                )

                if similarity >= self.similarity_threshold:
                    matched_group = group
                    break

            if matched_group is None:
                groups.append([item])
            else:
                matched_group.append(item)

        return groups

    @staticmethod
    def _unique_document_count(
        items: list[EvidenceItem],
    ) -> int:
        identities = {
            (
                item.source.document_id
                or item.source.file_hash
                or item.source.filename
            )
            for item in items
            if (
                item.source.document_id
                or item.source.file_hash
                or item.source.filename
            )
        }

        return len(identities)

    @staticmethod
    def _average_relevance(
        items: list[EvidenceItem],
    ) -> float:
        if not items:
            return 0.0

        return sum(
            item.relevance_score
            for item in items
        ) / len(items)

    @staticmethod
    def _conflicting_items(
        bundle: EvidenceBundle,
        candidate_statement: str,
    ) -> list[EvidenceItem]:
        """
        Return explicitly classified conflicting evidence.

        Sprint 14 does not infer contradictions from lexical differences.
        Conflict must already be represented in the EvidenceBundle.
        """

        del candidate_statement

        return list(bundle.conflicting)

    def _confidence_score(
        self,
        *,
        supporting_items: list[EvidenceItem],
        conflicting_items: list[EvidenceItem],
    ) -> float:
        """
        Calculate deterministic candidate-inference confidence.

        Factors:

        - retrieval relevance,
        - number of supporting items,
        - independent document support,
        - explicit conflict penalty.

        This score represents support strength, not universal truth.
        """

        if not supporting_items:
            return 0.0

        average_relevance = self._average_relevance(
            supporting_items
        )

        evidence_volume = min(
            len(supporting_items) / 4,
            1.0,
        )

        document_independence = min(
            self._unique_document_count(
                supporting_items
            )
            / 3,
            1.0,
        )

        conflict_penalty = min(
            len(conflicting_items) * 0.12,
            0.36,
        )

        score = (
            average_relevance * 0.65
            + evidence_volume * 0.20
            + document_independence * 0.15
            - conflict_penalty
        )

        return round(
            max(0.0, min(score, 1.0)),
            3,
        )

    @staticmethod
    def _limitations(
        *,
        supporting_items: list[EvidenceItem],
        conflicting_items: list[EvidenceItem],
        bundle: EvidenceBundle,
    ) -> list[str]:
        limitations: list[str] = []

        document_count = (
            InferenceEngine._unique_document_count(
                supporting_items
            )
        )

        if len(supporting_items) == 1:
            limitations.append(
                "The candidate inference is supported by only one "
                "retrieved evidence item."
            )

        if document_count <= 1:
            limitations.append(
                "The available support comes from one document and "
                "has not been independently corroborated."
            )

        if conflicting_items:
            limitations.append(
                "Explicitly conflicting evidence is present and must "
                "be evaluated before accepting the inference."
            )

        if bundle.gaps:
            limitations.append(
                "The evidence analysis identified unresolved "
                "information gaps."
            )

        if bundle.unknown:
            limitations.append(
                "Some retrieved sources did not contain usable "
                "evidence text."
            )

        return limitations

    def _build_inference(
        self,
        *,
        group: list[EvidenceItem],
        bundle: EvidenceBundle,
        group_index: int,
    ) -> Inference:
        del group_index
        statement = self._bounded_statement(
            group[0].statement
        )

        conflicting_items = self._conflicting_items(
            bundle,
            statement,
        )

        supporting_evidence_ids = [
            self._evidence_id(item, index)
            for index, item in enumerate(
                group,
                start=1,
            )
        ]

        conflicting_evidence_ids = [
            self._evidence_id(item, index)
            for index, item in enumerate(
                conflicting_items,
                start=1,
            )
        ]

        limitations = self._limitations(
            supporting_items=group,
            conflicting_items=conflicting_items,
            bundle=bundle,
        )

        if (
            group[0].disposition
            == EvidenceDisposition.CONTEXTUAL
        ):
            limitations.insert(
                0,
                (
                    "This candidate was derived from contextual "
                    "retrieval evidence that has not yet been "
                    "classified against a specific hypothesis."
                ),
            )

        return Inference(
            statement=statement,
            supporting_evidence_ids=(
                supporting_evidence_ids
            ),
            conflicting_evidence_ids=(
                conflicting_evidence_ids
            ),
            assumptions=[],
            confidence_score=self._confidence_score(
                supporting_items=group,
                conflicting_items=conflicting_items,
            ),
            limitations=limitations,
        )

    def infer(
        self,
        evidence: EvidenceBundle,
    ) -> list[Inference]:
        """
        Generate candidate inferences from an EvidenceBundle.

        Empty or unusable evidence produces no inference rather than an
        unsupported conclusion.
        """

        usable_items = [
            item
            for item in self._usable_items(evidence)
            if self._bounded_statement(item.statement)
        ]

        if not usable_items:
            return []

        groups = self._group_items(usable_items)

        inferences = [
            self._build_inference(
                group=group,
                bundle=evidence,
                group_index=index,
            )
            for index, group in enumerate(
                groups,
                start=1,
            )
        ]

        inferences.sort(
            key=lambda inference: (
                inference.confidence_score,
                len(
                    inference.supporting_evidence_ids
                ),
            ),
            reverse=True,
        )

        return inferences[
            : self.maximum_inferences
        ]
