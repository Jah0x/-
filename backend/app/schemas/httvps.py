from datetime import datetime

from pydantic import BaseModel


class SessionRequest(BaseModel):
    device_id: str
    token: str
    region: str | None = None


class SessionResponse(BaseModel):
    session_token: str
    expires_at: datetime
    gateway_url: str
    max_streams: int


class ValidateSessionRequest(BaseModel):
    session_token: str


class ValidateSessionResponse(BaseModel):
    session_id: str
    device_id: str
    max_streams: int
    outline: dict
