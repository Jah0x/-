from pydantic import BaseModel


class UsageReport(BaseModel):
    session_id: int | None = None
    device_id: str
    bytes_up: int
    bytes_down: int
