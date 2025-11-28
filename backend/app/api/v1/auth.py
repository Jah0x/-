from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.database import get_session
from app.schemas.auth import ValidateDeviceRequest, ValidateDeviceResponse
from app.services.auth_service import validate_device


router = APIRouter()


@router.post("/validate-device", response_model=ValidateDeviceResponse)
async def validate_device_endpoint(body: ValidateDeviceRequest, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    result = await validate_device(session, body.device_id, body.token, settings)
    if not result.get("allowed"):
        raise HTTPException(status_code=403, detail=result)
    return ValidateDeviceResponse(**result)
