from datetime import datetime
from pydantic import BaseModel
from pydantic.config import ConfigDict


class OperationStatus(BaseModel):
    status: str


class AdminAuditEntry(BaseModel):
    id: int
    actor: str
    action: str
    resource_type: str
    resource_id: str | None = None
    payload: dict | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
