from pydantic import BaseModel
from fastapi import APIRouter
from app.schemas.usage import UsageReport


class Heartbeat(BaseModel):
    node_id: int | None = None
    region: str | None = None
    status: str | None = None


router = APIRouter()


@router.post("/usage/report")
async def report_usage(body: UsageReport):
    return {"status": "accepted"}


@router.post("/gateway/heartbeat")
async def gateway_heartbeat(payload: Heartbeat):
    return {"status": "ok"}


@router.post("/outline/heartbeat")
async def outline_heartbeat(payload: Heartbeat):
    return {"status": "ok"}
