from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.gateway_node import GatewayNode
from app.models.outline_node import OutlineNode
from app.services.region_service import find_region_by_code


class NodeNotFound(Exception):
    pass


class RegionForNodeNotFound(Exception):
    pass


async def list_outline_nodes_full(session: AsyncSession) -> list[OutlineNode]:
    result = await session.scalars(
        select(OutlineNode)
        .options(selectinload(OutlineNode.region))
        .where(OutlineNode.is_deleted.is_(False))
        .order_by(OutlineNode.id)
    )
    return result.all()


async def get_outline_node(session: AsyncSession, node_id: int) -> OutlineNode:
    node = await session.scalar(
        select(OutlineNode)
        .options(selectinload(OutlineNode.region))
        .where(OutlineNode.id == node_id, OutlineNode.is_deleted.is_(False))
    )
    if not node:
        raise NodeNotFound()
    return node


async def create_outline_node(session: AsyncSession, data: dict) -> OutlineNode:
    region = None
    if data.get("region_code"):
        region = await find_region_by_code(session, data["region_code"])
        if not region:
            raise RegionForNodeNotFound()
    payload = data.copy()
    payload.pop("region_code", None)
    payload["region_id"] = region.id if region else None
    node = OutlineNode(**payload)
    session.add(node)
    await session.commit()
    await session.refresh(node)
    await session.refresh(node, attribute_names=["region"])
    return node


async def update_outline_node(session: AsyncSession, node_id: int, data: dict) -> OutlineNode:
    node = await get_outline_node(session, node_id)
    if "region_code" in data:
        region_value = data.pop("region_code")
        if region_value:
            region = await find_region_by_code(session, region_value)
            if not region:
                raise RegionForNodeNotFound()
            node.region_id = region.id
        else:
            node.region_id = None
    for key, value in data.items():
        setattr(node, key, value)
    await session.commit()
    await session.refresh(node)
    await session.refresh(node, attribute_names=["region"])
    return node


async def delete_outline_node(session: AsyncSession, node_id: int) -> None:
    node = await get_outline_node(session, node_id)
    node.is_deleted = True
    node.is_active = False
    await session.commit()


async def list_gateway_nodes(session: AsyncSession) -> list[GatewayNode]:
    result = await session.scalars(
        select(GatewayNode).options(selectinload(GatewayNode.region)).order_by(GatewayNode.id)
    )
    return result.all()


async def get_gateway_node(session: AsyncSession, node_id: int) -> GatewayNode:
    node = await session.scalar(
        select(GatewayNode).options(selectinload(GatewayNode.region)).where(GatewayNode.id == node_id)
    )
    if not node:
        raise NodeNotFound()
    return node


async def create_gateway_node(session: AsyncSession, data: dict) -> GatewayNode:
    region = None
    if data.get("region_code"):
        region = await find_region_by_code(session, data["region_code"])
        if not region:
            raise RegionForNodeNotFound()
    payload = data.copy()
    payload.pop("region_code", None)
    payload["region_id"] = region.id if region else None
    node = GatewayNode(**payload)
    session.add(node)
    await session.commit()
    await session.refresh(node)
    await session.refresh(node, attribute_names=["region"])
    return node


async def update_gateway_node(session: AsyncSession, node_id: int, data: dict) -> GatewayNode:
    node = await get_gateway_node(session, node_id)
    if "region_code" in data:
        region_value = data.pop("region_code")
        if region_value:
            region = await find_region_by_code(session, region_value)
            if not region:
                raise RegionForNodeNotFound()
            node.region_id = region.id
        else:
            node.region_id = None
    for key, value in data.items():
        setattr(node, key, value)
    await session.commit()
    await session.refresh(node)
    await session.refresh(node, attribute_names=["region"])
    return node


async def delete_gateway_node(session: AsyncSession, node_id: int) -> None:
    node = await get_gateway_node(session, node_id)
    await session.delete(node)
    await session.commit()
