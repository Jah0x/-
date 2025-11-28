from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.httvps import SessionRequest, SessionResponse
from app.services.httvps_session_service import issue_session_descriptor


router = APIRouter()


@router.post("/session", response_model=SessionResponse)
async def create_session(body: SessionRequest, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    descriptor = await issue_session_descriptor(session, body.device_id, body.token, body.region, settings)
    if not descriptor.get("allowed"):
        raise HTTPException(status_code=403, detail=descriptor)
    return SessionResponse(
        session_token=descriptor["session_token"],
        expires_at=descriptor["expires_at"],
        gateway_url=descriptor["gateway_url"],
        max_streams=descriptor["max_streams"],
    )
