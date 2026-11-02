from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from agentops.core.security import require_api_key
from agentops.schemas.trace import IngestResult, TraceBatchIn, TraceIn, TraceOut
from agentops.services.ingestion import persist_trace
from agentops.storage.database import get_session
from agentops.storage.models import Trace

router = APIRouter(
    prefix="/api/v1/traces",
    tags=["traces"],
    dependencies=[Depends(require_api_key)],
)


@router.post("", response_model=IngestResult)
def ingest_trace(payload: TraceIn, session: Session = Depends(get_session)):
    created = persist_trace(session, payload)
    return IngestResult(trace_id=payload.trace_id, span_count=len(payload.spans), created=created)


@router.post("/batch", response_model=list[IngestResult])
def ingest_batch(payload: TraceBatchIn, session: Session = Depends(get_session)):
    results = []
    try:
        for trace in payload.traces:
            created = persist_trace(session, trace, commit=False)
            results.append(
                IngestResult(trace_id=trace.trace_id, span_count=len(trace.spans), created=created)
            )
        session.commit()
    except Exception:
        session.rollback()
        raise
    return results


@router.get("", response_model=list[TraceOut])
def list_traces(
    limit: int = Query(default=50, ge=1, le=500),
    session: Session = Depends(get_session),
):
    query = (
        select(Trace)
        .options(selectinload(Trace.spans))
        .order_by(Trace.started_at.desc())
        .limit(limit)
    )
    return list(session.scalars(query).unique())


@router.get("/{trace_id}", response_model=TraceOut)
def get_trace(trace_id: str, session: Session = Depends(get_session)):
    trace = session.scalar(
        select(Trace).options(selectinload(Trace.spans)).where(Trace.id == trace_id)
    )
    if trace is None:
        raise HTTPException(status_code=404, detail="Trace not found")
    return trace
