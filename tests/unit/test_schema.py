import pytest
from pydantic import ValidationError

from agentops.schemas.trace import TraceIn


def test_trace_accepts_token_counts_and_spans():
    payload = TraceIn(
        trace_id="t1",
        name="agent",
        input_tokens=10,
        output_tokens=5,
        spans=[{"span_id": "root", "name": "agent.run"}],
    )
    assert payload.input_tokens + payload.output_tokens == 15


def test_duplicate_span_ids_are_rejected():
    with pytest.raises(ValidationError):
        TraceIn(
            trace_id="t1",
            name="agent",
            spans=[
                {"span_id": "same", "name": "root"},
                {"span_id": "same", "name": "tool"},
            ],
        )


def test_parent_span_can_be_external_to_this_payload():
    trace = TraceIn(
        trace_id="t1",
        name="agent",
        spans=[{"span_id": "child", "parent_span_id": "upstream-parent", "name": "tool"}],
    )
    assert trace.spans[0].parent_span_id == "upstream-parent"
