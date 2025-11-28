import pytest
from sqlalchemy import delete, select
from app.models.outline_access_key import OutlineAccessKey
from app.models.outline_node import OutlineNode
from app.models.region import Region


class DummyOutlineClient:
    deleted = []

    def __init__(self, api_url: str, api_key: str):
        self.api_url = api_url
        self.api_key = api_key

    async def delete_key(self, key_id: str) -> None:
        self.deleted.append((self.api_url, key_id))


@pytest.mark.asyncio
async def test_revoke_outline_marks_revoked(client, test_app, setup_device):
    DummyOutlineClient.deleted = []
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(OutlineAccessKey))
        region = Region(code="eu", name="Europe")
        session.add(region)
        await session.flush()
        node = OutlineNode(region_id=region.id, host="host1", port=1080, method="aes-256-gcm", password="pwd", api_url="https://api", api_key="key", is_active=True)
        session.add(node)
        await session.flush()
        access_key = OutlineAccessKey(device_id=setup_device.id, outline_node_id=node.id, access_key_id="key-1", password="pwd", method="aes-256-gcm", port=1080)
        session.add(access_key)
        await session.commit()
        key_id = access_key.id
    client._transport.app.state.outline_client_class = DummyOutlineClient
    resp = await client.post("/api/v1/nodes/revoke-outline", json={"device_id": setup_device.device_id})
    assert resp.status_code == 200
    assert resp.json()["revoked"] is True
    async with session_maker() as session:
        stored = await session.scalar(select(OutlineAccessKey).where(OutlineAccessKey.id == key_id))
        assert stored.revoked is True
    assert DummyOutlineClient.deleted == [("https://api", "key-1")]


@pytest.mark.asyncio
async def test_revoke_outline_without_key(client, test_app, setup_device):
    DummyOutlineClient.deleted = []
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(OutlineAccessKey))
        await session.commit()
    client._transport.app.state.outline_client_class = DummyOutlineClient
    resp = await client.post("/api/v1/nodes/revoke-outline", json={"device_id": setup_device.device_id})
    assert resp.status_code == 200
    assert resp.json()["revoked"] is False
    assert DummyOutlineClient.deleted == []


@pytest.mark.asyncio
async def test_revoke_outline_missing_device(client):
    resp = await client.post("/api/v1/nodes/revoke-outline", json={"device_id": "unknown"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "device_not_found"
