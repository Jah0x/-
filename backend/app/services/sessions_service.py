from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.session import Session


async def get_session_by_id(session: AsyncSession, session_id: int) -> Session | None:
    return await session.scalar(select(Session).where(Session.id == session_id))
