from pydantic import BaseModel
from datetime import datetime


class HeartbeatPayload(BaseModel):
    node_id: int | None = None
    region: str | None = None
    status: str | None = None
    uptime_sec: int | None = None
    active_sessions: int | None = None
    cpu_load: float | None = None
    mem_load: float | None = None
    bytes_up: int | None = None
    bytes_down: int | None = None
    last_error: str | None = None
    timestamp: datetime | None = None


class HeartbeatResponse(BaseModel):
    status: str
