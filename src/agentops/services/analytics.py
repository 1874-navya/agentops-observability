from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from agentops.storage.models import Span, Trace


def overview(session: Session) -> dict[str, int | float]:
    count, failures, tokens, avg_ms, max_ms = session.execute(
        select(
            func.count(Trace.id),
            func.coalesce(func.sum(case((Trace.status == "error", 1), else_=0)), 0),
            func.coalesce(func.sum(Trace.total_tokens), 0),
            func.coalesce(func.avg(Trace.duration_ms), 0.0),
            func.coalesce(func.max(Trace.duration_ms), 0.0),
        )
    ).one()
    span_count = session.scalar(select(func.count()).select_from(Span)) or 0
    return {
        "total_traces": int(count or 0),
        "failed_traces": int(failures or 0),
        "total_tokens": int(tokens or 0),
        "average_latency_ms": float(avg_ms or 0.0),
        "max_latency_ms": float(max_ms or 0.0),
        "total_spans": int(span_count),
    }
