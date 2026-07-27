from statistics import mean

from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ReasoningService:
    """
    Evidence-grounded answer construction.

    Reasoning coordinates retrieval, context assembly, structured
    generation, deterministic confidence, and source traceability.
    """

    def __init__(self):
        self.retrieval = RetrievalService()
        self.context_builder = ContextBuilder()
        self.llm = LLMService()

    @staticmethod
    def _confidence_score(chunks: list) -> float:
        """
        Calculate transparent retrieval confidence.

        Sprint 13.2 uses a conservative combination of:

        - average similarity,
        - strongest source score,
        - evidence-volume support.

        This is retrieval confidence, not factual certainty.
        """

        if not chunks:
            return 0.0

        scores = [
            max(0.0, min(float(point.score), 1.0))
            for point in chunks
        ]

        average_similarity = mean(scores)
        strongest_similarity = max(scores)
        evidence_support = min(len(scores) / 5, 1.0)

        confidence = (
            average_similarity * 0.60
            + strongest_similarity * 0.25
            + evidence_support * 0.15
        )

        return round(min(confidence, 1.0), 3)

    @staticmethod
    def _confidence_level(score: float) -> str:
        if score >= 0.80:
            return "high"

        if score >= 0.60:
            return "moderate"

        return "low"

    @staticmethod
    def _build_sources(chunks: list) -> list[dict]:
        return [
            {
                "document_id": point.payload.get(
                    "document_id"
                ),
                "filename": point.payload.get("filename"),
                "file_hash": point.payload.get("file_hash"),
                "module": point.payload.get("module"),
                "topic": point.payload.get("topic"),
                "collection": point.payload.get(
                    "collection"
                ),
                "organization_id": point.payload.get(
                    "organization_id"
                ),
                "description": point.payload.get(
                    "description"
                ),
                "status": point.payload.get("status"),
                "chunk_index": point.payload.get(
                    "chunk_index"
                ),
                "score": round(float(point.score), 4),
            }
            for point in chunks
        ]

    @staticmethod
    def _related_knowledge(
        generated_topics: list[str],
        sources: list[dict],
    ) -> list[str]:
        """
        Merge model-derived topics with canonical source metadata.
        """

        candidates = list(generated_topics)

        for source in sources:
            candidates.extend(
                [
                    source.get("module"),
                    source.get("topic"),
                    source.get("collection"),
                ]
            )

        normalized = []
        seen = set()

        for value in candidates:
            if not value:
                continue

            label = str(value).strip()

            if not label:
                continue

            identity = label.casefold()

            if identity in seen:
                continue

            seen.add(identity)
            normalized.append(label)

        return normalized[:8]

    def answer_question(
        self,
        question: str,
        limit: int = 5,
        score_threshold: float = 0.45,
        module: str | None = None,
        topic: str | None = None,
        organization_id: str = "default",
    ):
        chunks = self.retrieval.search(
            question=question,
            limit=limit,
            score_threshold=score_threshold,
            module=module,
            topic=topic,
            organization_id=organization_id,
        )

        if not chunks:
            return {
                "answer": (
                    "I do not have enough evidence in the selected "
                    "knowledge workspace to answer that."
                ),
                "confidence": {
                    "score": 0.0,
                    "level": "low",
                    "basis": (
                        "No supporting evidence met the current "
                        "retrieval threshold."
                    ),
                },
                "recommended_next_step": (
                    "Teach Sentinel additional knowledge, select a "
                    "different workspace, or ask a narrower question."
                ),
                "suggested_follow_up": (
                    "What knowledge should be added to support this "
                    "question?"
                ),
                "related_knowledge": [],
                "sources": [],
                "module": module,
                "topic": topic,
            }

        prompt = self.context_builder.build_context(
            question,
            chunks,
        )

        generated = self.llm.generate_recall(prompt)
        sources = self._build_sources(chunks)

        confidence_score = self._confidence_score(chunks)

        return {
            "answer": generated.answer,
            "confidence": {
                "score": confidence_score,
                "level": self._confidence_level(
                    confidence_score
                ),
                "basis": generated.confidence_basis,
            },
            "recommended_next_step": (
                generated.recommended_next_step
            ),
            "suggested_follow_up": (
                generated.suggested_follow_up
            ),
            "related_knowledge": self._related_knowledge(
                generated.related_topics,
                sources,
            ),
            "sources": sources,
            "module": module,
            "topic": topic,
        }

