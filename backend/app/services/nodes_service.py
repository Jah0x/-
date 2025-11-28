import logging
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.clients.outline_client import OutlineClient, OutlineClientError
from app.models.device import Device
from app.models.outline_access_key import OutlineAccessKey
from app.models.outline_node import OutlineNode
from app.models.region import Region
from app.schemas.nodes import OutlineNodeAssignment


class NoOutlineNodesAvailable(Exception):
    pass


class OutlineProvisioningError(Exception):
    pass


logger = logging.getLogger(__name__)


async def assign_outline_node(session: AsyncSession, region_code: str | None, device_identifier: str, client_class: type[OutlineClient] = OutlineClient) -> OutlineNodeAssignment:
    device = await session.scalar(select(Device).where(Device.device_id == device_identifier))
    if not device:
        raise OutlineProvisioningError("device_not_found")
    region = None
    if region_code:
        region = await session.scalar(select(Region).where(Region.code == region_code))
    nodes: list[OutlineNode] = []
    query = (
        select(OutlineNode)
        .options(selectinload(OutlineNode.region))
        .where(OutlineNode.is_active.is_(True), OutlineNode.is_deleted.is_(False))
        .order_by(OutlineNode.priority.is_(None), OutlineNode.priority, OutlineNode.id)
    )
    if region:
        result = await session.scalars(query.where(OutlineNode.region_id == region.id))
        nodes = result.all()
    if not nodes:
        result = await session.scalars(query)
        nodes = result.all()
    if not nodes:
        raise NoOutlineNodesAvailable()
    node = nodes[0]
    method = node.method
    password = node.password
    port = node.port
    access_key_id = None
    access_url = None
    if node.api_url and node.api_key:
        client = client_class(node.api_url, node.api_key)
        try:
            key_data = await client.create_key(device_identifier)
        except OutlineClientError as exc:
            raise OutlineProvisioningError(str(exc))
        access_key_id = key_data.key_id
        password = key_data.password or password
        method = key_data.method or method or "chacha20-ietf-poly1305"
        port = key_data.port or port
        access_url = key_data.access_url
        outline_key = OutlineAccessKey(
            device_id=device.id,
            outline_node_id=node.id,
            access_key_id=access_key_id,
            password=password,
            method=method,
            port=port,
            access_url=access_url,
        )
        session.add(outline_key)
        await session.commit()
        await session.refresh(outline_key)
    region_value = node.region.code if node.region else None
    return OutlineNodeAssignment(
        node_id=node.id,
        host=node.host,
        port=port,
        method=method,
        password=password,
        region=region_value,
        access_key_id=access_key_id,
        access_url=access_url,
    )


async def revoke_outline_key(session: AsyncSession, device_identifier: str, client_class: type[OutlineClient] | None = OutlineClient) -> bool:
    device = await session.scalar(select(Device).where(Device.device_id == device_identifier))
    if not device:
        raise OutlineProvisioningError("device_not_found")
    query = (
        select(OutlineAccessKey)
        .options(selectinload(OutlineAccessKey.outline_node))
        .where(OutlineAccessKey.device_id == device.id, OutlineAccessKey.revoked.is_(False))
        .order_by(OutlineAccessKey.created_at.desc())
    )
    access_key = await session.scalar(query)
    if not access_key:
        return False
    access_key.revoked = True
    await session.commit()
    node = access_key.outline_node
    if node and node.api_url and node.api_key and client_class:
        client = client_class(node.api_url, node.api_key)
        try:
            await client.delete_key(access_key.access_key_id)
        except OutlineClientError:
            logger.warning("outline_delete_key_failed", exc_info=True)
    return True
