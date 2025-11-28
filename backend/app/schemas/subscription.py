from datetime import datetime
from pydantic import BaseModel


class SubscriptionInfo(BaseModel):
    id: int
    status: str
    valid_until: datetime | None
    plan_id: int | None
