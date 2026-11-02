import secrets
from typing import Annotated

from fastapi import Header, HTTPException, status

from agentops.core.config import get_settings


async def require_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")] = "",
) -> None:
    expected = get_settings().agentops_api_key.get_secret_value()
    if not secrets.compare_digest(x_api_key, expected):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid API key")
