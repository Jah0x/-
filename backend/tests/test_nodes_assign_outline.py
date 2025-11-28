import pytest
from sqlalchemy import delete
from app.models.outline_node import OutlineNode
from app.models.region import Region


@pytest.mark.asyncio
async def test_assign_outline_with_region(client, test_app, setup_device):
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(Region))
        region = Region(code="us", name="United States")
        session.add(region)
        await session.flush()
        node = OutlineNode(region_id=region.id, host="host1", port=1080, method="aes-256-gcm", password="pwd", is_active=True)
        session.add(node)
        await session.commit()
        node_id = node.id
    resp = await client.post("/api/v1/nodes/assign-outline", json={"region_code": "us", "device_id": setup_device.device_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == node_id
    assert data["region"] == "us"
    assert data["host"] == "host1"


@pytest.mark.asyncio
async def test_assign_outline_with_fallback(client, test_app, setup_device):
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(Region))
        region = Region(code="us", name="United States")
        session.add(region)
        await session.flush()
        node = OutlineNode(region_id=region.id, host="host2", port=2080, method="aes-256-gcm", password="pwd", is_active=True)
        session.add(node)
        await session.commit()
        node_id = node.id
    resp = await client.post("/api/v1/nodes/assign-outline", json={"region_code": "eu", "device_id": setup_device.device_id})
    assert resp.status_code == 200
    data = resp.json()
    assert data["node_id"] == node_id
    assert data["region"] == "us"


@pytest.mark.asyncio
async def test_assign_outline_without_nodes(client, setup_device):
    session_maker = client._transport.app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(Region))
        await session.commit()
    resp = await client.post("/api/v1/nodes/assign-outline", json={"region_code": "us", "device_id": setup_device.device_id})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "no_outline_nodes_available"
