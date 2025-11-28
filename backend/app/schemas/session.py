from datetime import datetime
from pydantic import BaseModel


class SessionInfo(BaseModel):
    id: int
    device_id: int
    outline_node_id: int | None
    gateway_node_id: int | None
    started_at: datetime
    ended_at: datetime | None
    bytes_up: int
    bytes_down: int
    status: str
