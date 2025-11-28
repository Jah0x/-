from pydantic import BaseModel


class ValidateDeviceRequest(BaseModel):
    device_id: str
    token: str


class ValidateDeviceResponse(BaseModel):
    allowed: bool
    user_id: int | None = None
    subscription_status: str | None = None
    reason: str | None = None
