from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
    ExportTraceServiceRequest,
    ExportTraceServiceResponse,
)


def test_otlp_http_trace_export_is_persisted(client):
    export_request = ExportTraceServiceRequest()
    resource_spans = export_request.resource_spans.add()
    service = resource_spans.resource.attributes.add()
    service.key = "service.name"
    service.value.string_value = "demo-agent"

    scope = resource_spans.scope_spans.add()
    root = scope.spans.add()
    root.trace_id = bytes.fromhex("1234567890abcdef1234567890abcdef")
    root.span_id = bytes.fromhex("1234567890abcdef")
    root.name = "agent.run"
    root.start_time_unix_nano = 1_700_000_000_000_000_000
    root.end_time_unix_nano = 1_700_000_000_250_000_000
    root.status.code = 1
    root_kind = root.attributes.add()
    root_kind.key = "agentops.operation.kind"
    root_kind.value.string_value = "agent"

    llm = scope.spans.add()
    llm.trace_id = root.trace_id
    llm.span_id = bytes.fromhex("abcdef1234567890")
    llm.parent_span_id = root.span_id
    llm.name = "llm.call"
    llm.start_time_unix_nano = 1_700_000_000_010_000_000
    llm.end_time_unix_nano = 1_700_000_000_200_000_000
    llm.status.code = 1
    llm_kind = llm.attributes.add()
    llm_kind.key = "agentops.operation.kind"
    llm_kind.value.string_value = "llm"
    input_tokens = llm.attributes.add()
    input_tokens.key = "gen_ai.usage.input_tokens"
    input_tokens.value.int_value = 12
    output_tokens = llm.attributes.add()
    output_tokens.key = "gen_ai.usage.output_tokens"
    output_tokens.value.int_value = 8
    model = llm.attributes.add()
    model.key = "gen_ai.request.model"
    model.value.string_value = "test-model"

    response = client.post(
        "/v1/traces",
        content=export_request.SerializeToString(),
        headers={
            "X-API-Key": "test-key",
            "Content-Type": "application/x-protobuf",
        },
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/x-protobuf"
    assert response.headers["x-agentops-accepted-spans"] == "2"
    ExportTraceServiceResponse.FromString(response.content)

    trace = client.get(
        "/api/v1/traces/1234567890abcdef1234567890abcdef",
        headers={"X-API-Key": "test-key"},
    )
    assert trace.status_code == 200
    payload = trace.json()
    assert payload["agent_name"] == "demo-agent"
    assert payload["total_tokens"] == 20
    assert len(payload["spans"]) == 2
    assert next(item for item in payload["spans"] if item["kind"] == "llm")["model"] == "test-model"
