from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


@contextmanager
def operation_span(
    name: str,
    *,
    kind: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[None]:
    """Create an OpenTelemetry span around an agent, tool, or LLM operation.

    Install optional dependencies with: pip install '.[otel]'.
    The helper deliberately avoids recording prompts, completions, and secrets.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.trace import Status, StatusCode
    except ImportError as exc:
        raise RuntimeError(
            "OpenTelemetry support is optional; install agentops-observability[otel]"
        ) from exc

    tracer = trace.get_tracer("agentops")
    with tracer.start_as_current_span(name) as span:
        span.set_attribute("agentops.operation.kind", kind)
        if attributes:
            span.set_attributes(attributes)
        try:
            yield
        except Exception as exc:
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR, str(exc)))
            raise


def agent_span(name: str = "agent.run", **attributes: Any):
    return operation_span(name, kind="agent", attributes=attributes)


def tool_span(name: str, **attributes: Any):
    return operation_span(name, kind="tool", attributes=attributes)


def llm_span(
    model: str,
    *,
    provider: str | None = None,
    input_tokens: int | None = None,
    output_tokens: int | None = None,
):
    attributes: dict[str, Any] = {"gen_ai.request.model": model}
    if provider:
        attributes["gen_ai.system"] = provider
    if input_tokens is not None:
        attributes["gen_ai.usage.input_tokens"] = input_tokens
    if output_tokens is not None:
        attributes["gen_ai.usage.output_tokens"] = output_tokens
    return operation_span("llm.call", kind="llm", attributes=attributes)
