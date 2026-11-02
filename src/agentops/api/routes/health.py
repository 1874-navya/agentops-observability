from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from agentops.storage.database import get_session

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/ready")
def ready(session: Session = Depends(get_session)):
    session.execute(text("SELECT 1"))
    return {"status": "ready", "database": "ok"}
