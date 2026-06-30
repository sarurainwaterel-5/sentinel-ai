from app.services.retrieval_service import RetrievalService
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService

class ReasoningService:
    def __init__(self):
        self.retrieval = RetrievalService()
        self.context_builder = ContextBuilder()
        self.llm = LLMService()

    def answer_question(self, question: str, limit: int = 5, score_threshold: float = 0.45):
        chunks = self.retrieval.search(
            question=question,
            limit=limit,
            score_threshold=score_threshold
        )

        if not chunks:
            return {
                "answer": "I do not have enough evidence in the knowledge base to answer that.",
                "sources": []
            }

        prompt = self.context_builder.build_context(question, chunks)
        answer = self.llm.generate_answer(prompt)

        sources = [
            {
                "filename": point.payload.get("filename"),
                "chunk_index": point.payload.get("chunk_index"),
                "score": point.score
            }
            for point in chunks
        ]

        return {
            "answer": answer,
            "sources": sources
        }
