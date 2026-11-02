"""Generate nested agent/tool/LLM spans and export them to AgentOps over OTLP/HTTP."""

import os

from agentops.instrumentation.spans import agent_span, llm_span, tool_span
from agentops.integrations.opentelemetry import configure_otel


def main() -> None:
    api_key = os.environ["AGENTOPS_API_KEY"]
    endpoint = os.getenv("AGENTOPS_OTLP_ENDPOINT", "http://localhost:8000/v1/traces")
    provider = configure_otel(
        service_name="agentops-example-agent",
        traces_endpoint=endpoint,
        headers={"X-API-Key": api_key},
    )

    with agent_span("agent.run", agent_name="example-agent"):
        with tool_span("knowledge.search", tool_name="search"):
            pass
        with llm_span("demo-model", provider="demo", input_tokens=40, output_tokens=12):
            pass

    provider.force_flush()
    provider.shutdown()


if __name__ == "__main__":
    main()
