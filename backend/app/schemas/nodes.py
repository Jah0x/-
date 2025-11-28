from datetime import datetime
from pydantic import BaseModel
from pydantic.config import ConfigDict


class OutlineNodeAssignmentRequest(BaseModel):
    region_code: str | None = None
    pool_code: str | None = None
    device_id: str


class OutlineNodeAssignment(BaseModel):
    node_id: int
    host: str
    port: int
    method: str | None = None
    password: str | None = None
    region: str | None = None
    pool: str | None = None
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


class OutlineNodeCreate(BaseModel):
    name: str | None = None
    region_code: str | None = None
    host: str
    port: int
    method: str | None = None
    password: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    tag: str | None = None
    priority: int | None = None
    is_active: bool = True


class OutlineNodeUpdate(BaseModel):
    name: str | None = None
    region_code: str | None = None
    host: str | None = None
    port: int | None = None
    method: str | None = None
    password: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    tag: str | None = None
    priority: int | None = None
    is_active: bool | None = None


class OutlineNodeInfo(BaseModel):
    id: int
    name: str | None = None
    region: str | None = None
    host: str
    port: int
    method: str | None = None
    password: str | None = None
    api_url: str | None = None
    api_key: str | None = None
    tag: str | None = None
    priority: int | None = None
    is_active: bool
    is_deleted: bool

    model_config = ConfigDict(from_attributes=True)


class GatewayNodeCreate(BaseModel):
    region_code: str | None = None
    host: str
    port: int
    is_active: bool = True


class GatewayNodeUpdate(BaseModel):
    region_code: str | None = None
    host: str | None = None
    port: int | None = None
    is_active: bool | None = None


class GatewayNodeInfo(BaseModel):
    id: int
    region: str | None = None
    host: str
    port: int
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
