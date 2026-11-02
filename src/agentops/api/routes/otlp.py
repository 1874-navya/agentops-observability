import zlib
from collections import defaultdict
from datetime import UTC, datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from agentops.core.security import require_api_key
from agentops.schemas.trace import SpanIn, TraceIn
from agentops.services.ingestion import persist_trace
from agentops.storage.database import get_session

router = APIRouter(tags=["opentelemetry"], dependencies=[Depends(require_api_key)])

MAX_OTLP_BODY_BYTES = 64 * 1024 * 1024
_SENSITIVE_ATTRIBUTE_PARTS = (
    "authorization",
    "password",
    "secret",
    "api_key",
    "access_token",
    "refresh_token",
    "cookie",
    "prompt",
    "completion",
    "stacktrace",
)


def _any_value_to_python(value: Any) -> Any:
    field = value.WhichOneof("value")
    if field == "string_value":
        return value.string_value[:2048]
    if field == "bool_value":
        return value.bool_value
    if field == "int_value":
        return value.int_value
    if field == "double_value":
        return value.double_value
    if field == "array_value":
        return [_any_value_to_python(item) for item in value.array_value.values[:50]]
    if field == "kvlist_value":
        return _attributes_to_dict(value.kvlist_value.values[:100])
    if field == "bytes_value":
        return value.bytes_value[:512].hex()
    return None


def _attributes_to_dict(attributes: Any) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for item in attributes:
        key = item.key[:256]
        if any(part in key.lower() for part in _SENSITIVE_ATTRIBUTE_PARTS):
            continue
        if len(result) >= 100:
            break
        result[key] = _any_value_to_python(item.value)
    return result


def _timestamp(value: int) -> datetime | None:
    if not value:
        return None
    seconds, nanos = divmod(int(value), 1_000_000_000)
    return datetime.fromtimestamp(seconds, UTC).replace(microsecond=nanos // 1000)


def _nonnegative_int(value: Any) -> int:
    try:
        return min(max(int(value), 0), 2_147_483_647)
    except (TypeError, ValueError, OverflowError):
        return 0


def _span_to_model(span: Any) -> SpanIn:
    attributes = _attributes_to_dict(span.attributes)
    kind_value = attributes.get("agentops.operation.kind")
    allowed_kinds = {"agent", "tool", "llm", "retrieval", "chain", "custom"}
    kind = (
        kind_value
        if isinstance(kind_value, str) and kind_value in allowed_kinds
        else "custom"
    )

    started_at = _timestamp(span.start_time_unix_nano) or datetime.now(UTC)
    ended_at = _timestamp(span.end_time_unix_nano)
    duration_ms = None
    if ended_at is not None and ended_at >= started_at:
        duration_ms = (ended_at - started_at).total_seconds() * 1000

    status_code = int(span.status.code)
    span_status = "error" if status_code == 2 else ("ok" if status_code == 1 else "unset")
    input_tokens = _nonnegative_int(attributes.get("gen_ai.usage.input_tokens", 0))
    output_tokens = _nonnegative_int(attributes.get("gen_ai.usage.output_tokens", 0))
    parent_id = bytes(span.parent_span_id).hex() if span.parent_span_id else None
    if parent_id and int(parent_id, 16) == 0:
        parent_id = None

    return SpanIn(
        span_id=bytes(span.span_id).hex(),
        parent_span_id=parent_id,
        name=span.name or "unnamed",
        kind=kind,
        status=span_status,
        started_at=started_at,
        ended_at=ended_at,
        duration_ms=duration_ms,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=input_tokens + output_tokens,
        model=(
            str(attributes["gen_ai.request.model"])[:128]
            if attributes.get("gen_ai.request.model") is not None
            else None
        ),
        provider=(
            str(attributes["gen_ai.system"])[:128]
            if attributes.get("gen_ai.system") is not None
            else None
        ),
        error_type=attributes.get("exception.type"),
        # Exception messages and stack traces are intentionally not persisted.
        attributes=attributes,
    )


def _build_traces(message: Any) -> list[TraceIn]:
    grouped: dict[str, list[SpanIn]] = defaultdict(list)
    resources: dict[str, dict[str, Any]] = {}

    for resource_spans in message.resource_spans:
        resource_attributes = _attributes_to_dict(resource_spans.resource.attributes)
        for scope_spans in resource_spans.scope_spans:
            for otel_span in scope_spans.spans:
                trace_id = bytes(otel_span.trace_id).hex()
                span_id = bytes(otel_span.span_id).hex()
                if len(trace_id) != 32 or int(trace_id, 16) == 0:
                    raise ValueError("OTLP span has an invalid trace ID")
                if len(span_id) != 16 or int(span_id, 16) == 0:
                    raise ValueError("OTLP span has an invalid span ID")
                grouped[trace_id].append(_span_to_model(otel_span))
                resources.setdefault(trace_id, resource_attributes)

    traces: list[TraceIn] = []
    for trace_id, spans in grouped.items():
        spans.sort(key=lambda item: item.started_at)
        start = min(item.started_at for item in spans)
        ends = [item.ended_at for item in spans if item.ended_at is not None]
        end = max(ends) if ends else None
        llm_spans = [item for item in spans if item.kind == "llm"]
        token_spans = llm_spans or spans
        root = next((item for item in spans if not item.parent_span_id), spans[0])
        service_name = resources[trace_id].get("service.name", "unknown-service")
        traces.append(
            TraceIn(
                trace_id=trace_id,
                name=root.name,
                agent_name=str(service_name)[:255],
                status=(
                    "error"
                    if any(item.status == "error" for item in spans)
                    else ("ok" if any(item.status == "ok" for item in spans) else "unset")
                ),
                started_at=start,
                ended_at=end,
                duration_ms=(end - start).total_seconds() * 1000 if end else None,
                input_tokens=sum(item.input_tokens for item in token_spans),
                output_tokens=sum(item.output_tokens for item in token_spans),
                total_tokens=sum(item.total_tokens for item in token_spans),
                metadata=resources[trace_id],
                spans=spans,
            )
        )
    return traces


@router.post("/v1/traces")
async def receive_otlp_traces(
    request: Request,
    session: Session = Depends(get_session),  # noqa: B008
):
    """Receive OTLP/HTTP binary Protobuf traces and persist them as AgentOps traces."""
    try:
        from opentelemetry.proto.collector.trace.v1.trace_service_pb2 import (
            ExportTraceServiceRequest,
            ExportTraceServiceResponse,
        )
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OTLP receiver requires the optional 'otel' dependencies",
        ) from exc

    content_type = request.headers.get("content-type", "").split(";", 1)[0].strip().lower()
    if content_type != "application/x-protobuf":
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="OTLP receiver currently accepts application/x-protobuf",
        )

    body = await request.body()
    if len(body) > MAX_OTLP_BODY_BYTES:
        raise HTTPException(status_code=413, detail="OTLP request body exceeds 64 MiB")

    if request.headers.get("content-encoding", "").lower() == "gzip":
        try:
            decompressor = zlib.decompressobj(16 + zlib.MAX_WBITS)
            body = decompressor.decompress(body, MAX_OTLP_BODY_BYTES + 1)
            if len(body) > MAX_OTLP_BODY_BYTES or decompressor.unconsumed_tail:
                raise HTTPException(status_code=413, detail="Decompressed OTLP body exceeds 64 MiB")
            body += decompressor.flush()
        except zlib.error as exc:
            raise HTTPException(status_code=400, detail="Invalid gzip OTLP body") from exc
        if len(body) > MAX_OTLP_BODY_BYTES:
            raise HTTPException(status_code=413, detail="Decompressed OTLP body exceeds 64 MiB")

    export_request = ExportTraceServiceRequest()
    try:
        export_request.ParseFromString(body)
        traces = _build_traces(export_request)
    except (ValueError, ValidationError) as exc:
        raise HTTPException(status_code=400, detail=f"Invalid OTLP trace payload: {exc}") from exc
    except Exception as exc:
        raise HTTPException(
            status_code=400,
            detail="Unable to decode OTLP Protobuf request",
        ) from exc

    try:
        accepted_spans = 0
        for trace in traces:
            persist_trace(session, trace, commit=False)
            accepted_spans += len(trace.spans)
        session.commit()
    except Exception:
        session.rollback()
        raise

    export_response = ExportTraceServiceResponse()
    return Response(
        content=export_response.SerializeToString(),
        media_type="application/x-protobuf",
        status_code=200,
        headers={"X-AgentOps-Accepted-Spans": str(accepted_spans)},
    )
