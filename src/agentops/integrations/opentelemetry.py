from typing import Any


def configure_otel(
    *,
    service_name: str = "agentops-client",
    traces_endpoint: str | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    """Configure an OpenTelemetry SDK provider with an OTLP/HTTP trace exporter.

    Pass the full OTLP traces endpoint (usually ending in /v1/traces). If no
    endpoint is given, the exporter uses its environment-based configuration.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
    except ImportError as exc:
        raise RuntimeError("Install OpenTelemetry extras: pip install '.[otel]'") from exc

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    exporter_args: dict[str, Any] = {}
    if traces_endpoint:
        exporter_args["endpoint"] = traces_endpoint
    if headers:
        exporter_args["headers"] = headers
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(**exporter_args)))
    trace.set_tracer_provider(provider)
    return provider
