import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.config import get_settings
from app.core.security import create_token
from app.models.user import User
from app.models.device import Device
from app.models.subscription import Subscription, SubscriptionStatus
from app.models.plan import Plan


async def create_fixture_data(session: AsyncSession):
    user = User(email="user@example.com")
    plan = Plan(name="basic")
    session.add_all([user, plan])
    await session.flush()
    device = Device(user_id=user.id, device_id="device-1")
    subscription = Subscription(user_id=user.id, plan_id=plan.id, status=SubscriptionStatus.active.value)
    session.add_all([device, subscription])
    await session.commit()
    return user, device, subscription


@pytest.mark.asyncio
async def test_validate_device_success(test_app, client):
    settings = get_settings()
    TestSession = test_app.state.test_session_maker
    async with TestSession() as session:
        user, device, subscription = await create_fixture_data(session)
    token = create_token({"device_id": device.device_id}, settings)
    response = await client.post("/api/v1/auth/validate-device", json={"device_id": device.device_id, "token": token})
    assert response.status_code == 200
    body = response.json()
    assert body["allowed"] is True
    assert body["user_id"] == user.id
    assert body["subscription_status"] == subscription.status


@pytest.mark.asyncio
async def test_validate_device_failure(test_app, client):
    settings = get_settings()
    token = create_token({"device_id": "other"}, settings)
    response = await client.post("/api/v1/auth/validate-device", json={"device_id": "missing", "token": token})
    assert response.status_code == 403
    body = response.json()
    assert body["detail"]["allowed"] is False
