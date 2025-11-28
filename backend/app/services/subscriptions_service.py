from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.subscription import Subscription, SubscriptionStatus


async def get_active_subscription(session: AsyncSession, user_id: int) -> Subscription | None:
    now = datetime.now(timezone.utc)
    return await session.scalar(
        select(Subscription).where(
            Subscription.user_id == user_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.valid_until.is_(None) | (Subscription.valid_until > now),
        )
    )
