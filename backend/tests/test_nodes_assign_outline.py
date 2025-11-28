import pytest
import pytest
from sqlalchemy import delete
from app.models.outline_node import OutlineNode
from app.models.region import Region
from app.services.outline_health_service import OutlineHealthStatus


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


@pytest.mark.asyncio
async def test_assign_prefers_healthy_status(client, test_app, setup_device):
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(Region))
        node_down = OutlineNode(host="down", port=1000, method="m", password="p", is_active=True, last_check_status=OutlineHealthStatus.down.value)
        node_healthy = OutlineNode(host="ok", port=1001, method="m", password="p", is_active=True, last_check_status=OutlineHealthStatus.healthy.value)
        session.add_all([node_down, node_healthy])
        await session.commit()
        await session.refresh(node_healthy)
    resp = await client.post("/api/v1/nodes/assign-outline", json={"region_code": "us", "device_id": setup_device.device_id})
    assert resp.status_code == 200
    assert resp.json()["node_id"] == node_healthy.id


@pytest.mark.asyncio
async def test_assign_fails_without_healthy_nodes(client, test_app, setup_device):
    session_maker = test_app.state.test_session_maker
    async with session_maker() as session:
        await session.execute(delete(OutlineNode))
        await session.execute(delete(Region))
        node_down = OutlineNode(host="down", port=1000, method="m", password="p", is_active=True, last_check_status=OutlineHealthStatus.down.value)
        session.add(node_down)
        await session.commit()
    resp = await client.post("/api/v1/nodes/assign-outline", json={"region_code": "us", "device_id": setup_device.device_id})
    assert resp.status_code == 503
    assert resp.json()["detail"] == "no_healthy_outline_nodes"
