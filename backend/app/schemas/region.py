from pydantic import BaseModel
from pydantic.config import ConfigDict


class RegionInfo(BaseModel):
    id: int
    code: str
    name: str

    model_config = ConfigDict(from_attributes=True)


class RegionCreate(BaseModel):
    code: str
    name: str


class RegionUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
