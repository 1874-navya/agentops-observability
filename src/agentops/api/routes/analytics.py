from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from agentops.core.security import require_api_key
from agentops.services.analytics import overview
from agentops.storage.database import get_session

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["analytics"],
    dependencies=[Depends(require_api_key)],
)


@router.get("/overview")
def get_overview(session: Session = Depends(get_session)):
    return overview(session)
