"""
Premise extraction for SentinelAI reasoning.

This component converts inspectable EvidenceItems into
traceable Premises.

Premise extraction does not:

- form conclusions,
- synthesize multiple premises,
- classify contradictions,
- infer assumptions,
- calculate confidence.

Its responsibility is to establish the proposition layer
between retrieved evidence and downstream reasoning.
"""

from __future__ import annotations

import re

from app.services.cognition.reasoning.models import (
    EvidenceBundle,
    EvidenceItem,
    Premise,
)


class PremiseExtractor:
    """
    Extract normalized, evidence-grounded propositions.

    Every produced Premise preserves explicit evidence lineage.
    """

    @staticmethod
    def _normalize_statement(
        value: str,
    ) -> str:
        return re.sub(
            r"\s+",
            " ",
            str(value),
        ).strip()

    @staticmethod
    def _evidence_id(
        item: EvidenceItem,
        index: int,
    ) -> str:
        stored_identity = (
            item.source.metadata.get(
                "evidence_id"
            )
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
            else index
        )

        return (
            f"{document_identity}:"
            f"{chunk_identity}"
        )

    @staticmethod
    def _premise_id(
        evidence_id: str,
        index: int,
    ) -> str:
        return (
            f"premise:{index}:{evidence_id}"
        )

    @staticmethod
    def _domain_ids(
        item: EvidenceItem,
    ) -> list[str]:
        if not item.source.module:
            return []

        return [
            item.source.module,
        ]

    @staticmethod
    def _usable_items(
        evidence: EvidenceBundle,
    ) -> list[EvidenceItem]:
        return [
            *evidence.supporting,
            *evidence.contextual,
        ]

    def extract(
        self,
        evidence: EvidenceBundle,
    ) -> list[Premise]:
        """
        Extract traceable premises from usable evidence.

        Equivalent normalized statements are consolidated into
        one premise while preserving all supporting evidence IDs.
        """

        items = self._usable_items(
            evidence
        )

        grouped: dict[
            str,
            dict[str, object],
        ] = {}

        for index, item in enumerate(
            items,
            start=1,
        ):
            statement = self._normalize_statement(
                item.statement
            )

            if not statement:
                continue

            normalized_key = (
                statement.casefold()
            )

            evidence_id = self._evidence_id(
                item,
                index,
            )

            if normalized_key not in grouped:
                grouped[normalized_key] = {
                    "statement": statement,
                    "evidence_ids": [],
                    "domain_ids": [],
                    "source_document_ids": [],
                    "source_chunk_indexes": [],
                    "dispositions": [],
                }

            group = grouped[
                normalized_key
            ]

            group["evidence_ids"].append(
                evidence_id
            )

            group["domain_ids"].extend(
                self._domain_ids(
                    item
                )
            )

            if (
                item.source.document_id
                is not None
            ):
                group[
                    "source_document_ids"
                ].append(
                    item.source.document_id
                )

            if (
                item.source.chunk_index
                is not None
            ):
                group[
                    "source_chunk_indexes"
                ].append(
                    item.source.chunk_index
                )

            group[
                "dispositions"
            ].append(
                item.disposition.value
            )

        premises: list[Premise] = []

        for index, group in enumerate(
            grouped.values(),
            start=1,
        ):
            evidence_ids = list(
                dict.fromkeys(
                    group["evidence_ids"]
                )
            )

            premises.append(
                Premise(
                    premise_id=(
                        self._premise_id(
                            evidence_ids[0],
                            index,
                        )
                    ),
                    statement=(
                        group["statement"]
                    ),
                    evidence_ids=(
                        evidence_ids
                    ),
                    domain_ids=list(
                        dict.fromkeys(
                            group[
                                "domain_ids"
                            ]
                        )
                    ),
                    metadata={
                        "source_document_ids": list(
                            dict.fromkeys(
                                group[
                                    "source_document_ids"
                                ]
                            )
                        ),
                        "source_chunk_indexes": list(
                            dict.fromkeys(
                                group[
                                    "source_chunk_indexes"
                                ]
                            )
                        ),
                        "evidence_dispositions": list(
                            dict.fromkeys(
                                group[
                                    "dispositions"
                                ]
                            )
                        ),
                    },
                )
            )

        return premises
