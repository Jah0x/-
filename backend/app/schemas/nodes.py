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
