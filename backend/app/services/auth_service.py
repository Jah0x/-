from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import Settings
from app.core.security import verify_token
from app.models.device import Device
from app.models.subscription import Subscription, SubscriptionStatus


async def validate_device(session: AsyncSession, device_id: str, token: str, settings: Settings) -> dict:
    try:
        payload = verify_token(token, settings)
    except Exception:
        return {"allowed": False, "reason": "invalid_token"}
    token_device_id = payload.get("device_id")
    if token_device_id and token_device_id != device_id:
        return {"allowed": False, "reason": "device_mismatch"}
    device = await session.scalar(select(Device).where(Device.device_id == device_id))
    if not device:
        return {"allowed": False, "reason": "device_not_found"}
    now = datetime.now(timezone.utc)
    subscription = await session.scalar(
        select(Subscription).where(
            Subscription.user_id == device.user_id,
            Subscription.status == SubscriptionStatus.active.value,
            Subscription.valid_until.is_(None) | (Subscription.valid_until > now),
        )
    )
    if not subscription:
        return {"allowed": False, "reason": "no_active_subscription", "user_id": device.user_id}
    return {
        "allowed": True,
        "user_id": device.user_id,
        "subscription_status": subscription.status,
    }
