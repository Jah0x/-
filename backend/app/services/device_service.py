from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.device import Device


async def get_device_by_identifier(session: AsyncSession, device_identifier: str) -> Device | None:
    return await session.scalar(select(Device).where(Device.device_id == device_identifier))
