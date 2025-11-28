from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.heartbeat import HeartbeatPayload, HeartbeatResponse
from app.services.heartbeat_service import record_gateway_heartbeat, record_outline_heartbeat


router = APIRouter()


@router.post("/gateway/heartbeat", response_model=HeartbeatResponse)
async def gateway_heartbeat(payload: HeartbeatPayload, session: AsyncSession = Depends(get_session)):
    recorded = await record_gateway_heartbeat(session, payload.node_id)
    return HeartbeatResponse(status="ok" if recorded else "ignored")


@router.post("/outline/heartbeat", response_model=HeartbeatResponse)
async def outline_heartbeat(payload: HeartbeatPayload, session: AsyncSession = Depends(get_session)):
    recorded = await record_outline_heartbeat(session, payload.node_id)
    return HeartbeatResponse(status="ok" if recorded else "ignored")
