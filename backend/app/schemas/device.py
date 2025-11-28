from pydantic import BaseModel


class DeviceInfo(BaseModel):
    id: int
    user_id: int
    device_id: str
