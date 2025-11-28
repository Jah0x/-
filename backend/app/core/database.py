from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import get_settings
from app.db import Base

settings = get_settings()
engine = create_async_engine(settings.db_dsn, echo=settings.debug, future=True)
SessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_session() -> AsyncSession:
    async with SessionLocal() as session:
        yield session


__all__ = ["engine", "SessionLocal", "Base", "get_session"]
