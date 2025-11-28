from pydantic import BaseModel
from pydantic.config import ConfigDict


class PlanInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    traffic_limit: int | None = None
    period_days: int | None = None
    price: float | None = None

    model_config = ConfigDict(from_attributes=True)


class PlanCreate(BaseModel):
    name: str
    description: str | None = None
    traffic_limit: int | None = None
    period_days: int | None = None
    price: float | None = None


class PlanUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    traffic_limit: int | None = None
    period_days: int | None = None
    price: float | None = None
