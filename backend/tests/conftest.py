import os
os.environ.setdefault("BACKEND_DB_DSN", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("BACKEND_SECRET_KEY", "test")
os.environ.setdefault("BACKEND_DEBUG", "false")
os.environ.setdefault("BACKEND_HOST", "0.0.0.0")
os.environ.setdefault("BACKEND_PORT", "8000")
os.environ.setdefault("JWT_ALGORITHM", "HS256")
os.environ.setdefault("JWT_EXPIRE_MINUTES", "60")
os.environ.setdefault("OUTLINE_HEALTHCHECK_INTERVAL_SECONDS", "0")
os.environ.setdefault("OUTLINE_HEALTHCHECK_TIMEOUT_SECONDS", "1")
os.environ.setdefault("OUTLINE_HEALTHCHECK_DEGRADED_THRESHOLD_MS", "500")

import pytest_asyncio
import httpx
from httpx import ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db import Base
from app.core.config import get_settings
from app.core.database import get_session
from app.main import app
from app.models.user import User
from app.models.device import Device

get_settings.cache_clear()


@pytest_asyncio.fixture
async def test_app():
    engine = create_async_engine(os.environ["BACKEND_DB_DSN"], future=True)
    TestSession = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async def override_session():
        async with TestSession() as session:
            yield session
    app.dependency_overrides[get_session] = override_session
    app.state.test_session_maker = TestSession
    yield app
    await engine.dispose()


@pytest_asyncio.fixture
async def client(test_app):
    transport = ASGITransport(app=test_app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def setup_device(test_app):
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        user = User(email="user@example.com", is_active=True)
        session.add(user)
        await session.flush()
        device = Device(user_id=user.id, device_id="dev")
        session.add(device)
        await session.commit()
        await session.refresh(device)
        return device
