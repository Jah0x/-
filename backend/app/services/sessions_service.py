from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session


async def get_session_by_id(session: AsyncSession, session_id: int) -> Session | None:
    return await session.scalar(select(Session).where(Session.id == session_id))


async def apply_usage(session: AsyncSession, session_id: int | None, bytes_up: int, bytes_down: int) -> None:
    if session_id is None:
        return
    record = await get_session_by_id(session, session_id)
    if not record:
        return
    record.bytes_up = (record.bytes_up or 0) + bytes_up
    record.bytes_down = (record.bytes_down or 0) + bytes_down
    await session.commit()
