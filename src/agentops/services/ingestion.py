from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from agentops.schemas.trace import TraceIn
from agentops.storage.models import Span, Trace


def persist_trace(session: Session, payload: TraceIn, *, commit: bool = True) -> bool:
    trace = session.scalar(select(Trace).where(Trace.id == payload.trace_id))
    created = trace is None
    if trace is None:
        trace = Trace(id=payload.trace_id, name=payload.name)
        session.add(trace)
    else:
        session.execute(delete(Span).where(Span.trace_id == payload.trace_id))
        session.flush()

    trace.name = payload.name
    trace.agent_name = payload.agent_name
    trace.status = payload.status
    trace.started_at = payload.started_at
    trace.ended_at = payload.ended_at
    trace.duration_ms = payload.duration_ms
    trace.input_tokens = payload.input_tokens
    trace.output_tokens = payload.output_tokens
    trace.total_tokens = payload.total_tokens or payload.input_tokens + payload.output_tokens
    trace.metadata_json = payload.metadata

    for item in payload.spans:
        session.add(
            Span(
                trace_id=payload.trace_id,
                span_id=item.span_id,
                parent_span_id=item.parent_span_id,
                name=item.name,
                kind=item.kind,
                status=item.status,
                started_at=item.started_at,
                ended_at=item.ended_at,
                duration_ms=item.duration_ms,
                input_tokens=item.input_tokens,
                output_tokens=item.output_tokens,
                total_tokens=item.total_tokens or item.input_tokens + item.output_tokens,
                model=item.model,
                provider=item.provider,
                error_type=item.error_type,
                error_message=item.error_message,
                attributes=item.attributes,
            )
        )
    session.flush()
    if commit:
        session.commit()
    return created
