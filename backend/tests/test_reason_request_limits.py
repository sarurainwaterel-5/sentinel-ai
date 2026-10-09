import pytest
from pydantic import ValidationError
from app.schemas.cognition.reasoning import ReasoningRequest


@pytest.mark.parametrize("field,size", [("question", 10001), ("topic", 201), ("module", 201), ("organization_id", 201), ("mission_id", 201), ("session_id", 201), ("workspace", 101)])
def test_unbounded_reason_requests_are_rejected(field, size):
    with pytest.raises(ValidationError):
        ReasoningRequest.model_validate({"question": "Investigate recorded evidence", field: "x" * size})


def test_valid_reason_controls_and_cross_domain_scope_remain_available():
    request = ReasoningRequest(question=" Investigate evidence ", module=" ", topic="  operations  ", limit=25, score_threshold=0)
    assert request.question == "Investigate evidence"
    assert request.module is None
    assert request.topic == "operations"
    assert request.limit == 25
