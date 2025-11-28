from pydantic import BaseModel


class RegionInfo(BaseModel):
    id: int
    code: str
    name: str
