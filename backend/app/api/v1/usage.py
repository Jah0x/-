from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.usage import UsageReport
from app.services.sessions_service import apply_usage


router = APIRouter()


@router.post("/usage/report")
async def report_usage(body: UsageReport, session: AsyncSession = Depends(get_session)):
    await apply_usage(session, body.session_id, body.bytes_up, body.bytes_down)
    return {"status": "accepted"}
