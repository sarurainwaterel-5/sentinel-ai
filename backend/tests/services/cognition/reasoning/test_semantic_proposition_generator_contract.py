from app.services.cognition.reasoning.models import (
    CandidateProposition,
)
from app.services.cognition.reasoning.semantic_proposition_generator import (
    SemanticPropositionGenerator,
)


class TestSemanticGenerator:
    def generate(
        self,
        *,
        premises,
        relationships,
    ):
        return CandidateProposition(
            statement="Generated candidate.",
            premise_ids=[
                premises[0].premise_id,
                premises[1].premise_id,
            ],
        )


def test_semantic_generator_contract_is_structural():
    generator: SemanticPropositionGenerator = (
        TestSemanticGenerator()
    )

    assert hasattr(generator, "generate")
