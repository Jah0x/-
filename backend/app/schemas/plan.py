from pydantic import BaseModel


class PlanInfo(BaseModel):
    id: int
    name: str
    description: str | None = None
    traffic_limit: int | None = None
    period_days: int | None = None
    price: float | None = None
