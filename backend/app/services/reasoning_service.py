from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.retrieval_service import RetrievalService


class ReasoningService:
    """
    Evidence-grounded answer construction.

    Reasoning coordinates retrieval, context assembly, and language
    generation while preserving domain context and source traceability.
    """

    def __init__(self):
        self.retrieval = RetrievalService()
        self.context_builder = ContextBuilder()
        self.llm = LLMService()

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
                "sources": [],
                "module": module,
                "topic": topic,
            }

        prompt = self.context_builder.build_context(
            question,
            chunks,
        )

        answer = self.llm.generate_answer(prompt)

        sources = [
            {
                "document_id": point.payload.get("document_id"),
                "filename": point.payload.get("filename"),
                "chunk_index": point.payload.get("chunk_index"),
                "score": point.score,
                "module": point.payload.get("module"),
                "topic": point.payload.get("topic"),
            }
            for point in chunks
        ]

        return {
            "answer": answer,
            "sources": sources,
            "module": module,
            "topic": topic,
        }
