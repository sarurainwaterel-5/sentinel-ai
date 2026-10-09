"""Fail-closed constitutional authority until an evaluated assessor is installed.

Presence of principle text is evidence of context, not evidence of semantic
admissibility. No unexamined result receives a perfect constitutional score.
"""
from app.schemas.cognition.reasoning import CoherenceResult


class CoherenceEngine:
    def evaluate(self, question: str, identity_context: str, knowledge_context: str | None = None) -> CoherenceResult:
        return CoherenceResult(
            evaluation_status="not_evaluated",
            coherent=False,
            constitutional_score=0.0,
            articles_consulted=[],
            conflicts=["Constitutional semantic admissibility has not been assessed by a verified evaluator."],
            recommendations=["Review the structured result against Sentinel's principles before making a decision. No execution is authorized."],
        )
