from datetime import datetime
from pydantic import BaseModel


class OutlineNodeAssignmentRequest(BaseModel):
    region_code: str | None = None
    device_id: str


class OutlineNodeAssignment(BaseModel):
    node_id: int
    host: str
    port: int
    method: str | None = None
    password: str | None = None
    region: str | None = None
    access_key_id: str | None = None
    access_url: str | None = None


class OutlineRevokeRequest(BaseModel):
    device_id: str


class OutlineRevokeResponse(BaseModel):
    revoked: bool


class OutlineNodeStatus(BaseModel):
    id: int
    name: str | None = None
    host: str
    port: int
    region: str | None = None
    tag: str | None = None
    priority: int | None = None
    is_active: bool
    last_check_status: str | None = None
    last_check_at: datetime | None = None
    recent_latency_ms: int | None = None
    last_error: str | None = None
    active_access_keys: int | None = None
