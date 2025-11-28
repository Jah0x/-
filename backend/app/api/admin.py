from fastapi import Header, HTTPException, status
from app.core.config import get_settings


def require_admin(token: str | None = Header(default=None, alias="X-Admin-Token")) -> str:
    settings = get_settings()
    if token != settings.secret_key:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="unauthorized")
    return token
