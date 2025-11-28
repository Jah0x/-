from fastapi import APIRouter, Header, HTTPException
from app.core.config import get_settings
from app.schemas.httvps import ValidateSessionRequest, ValidateSessionResponse
from app.services.httvps_session_service import validate_session_token


router = APIRouter(prefix="/internal")


@router.post("/httvps/validate-session", response_model=ValidateSessionResponse)
async def validate_session(body: ValidateSessionRequest, x_internal_secret: str | None = Header(default=None)):
    settings = get_settings()
    if settings.gateway_internal_secret and settings.gateway_internal_secret != (x_internal_secret or ""):
        raise HTTPException(status_code=403, detail={"reason": "forbidden"})
    descriptor = await validate_session_token(body.session_token)
    if not descriptor:
        raise HTTPException(status_code=403, detail={"reason": "invalid_session"})
    outline = descriptor.get("outline") or {}
    return ValidateSessionResponse(
        session_id=descriptor.get("session_token"),
        device_id=descriptor.get("device_id"),
        max_streams=descriptor.get("max_streams", 0),
        outline=outline,
    )
