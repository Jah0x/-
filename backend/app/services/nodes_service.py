from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.outline_node import OutlineNode
from app.models.region import Region
from app.schemas.nodes import OutlineNodeAssignment


class NoOutlineNodesAvailable(Exception):
    pass


async def assign_outline_node(session: AsyncSession, region_code: str | None) -> OutlineNodeAssignment:
    region = None
    if region_code:
        region = await session.scalar(select(Region).where(Region.code == region_code))
    nodes: list[OutlineNode] = []
    if region:
        result = await session.scalars(
            select(OutlineNode)
            .options(selectinload(OutlineNode.region))
            .where(OutlineNode.region_id == region.id, OutlineNode.is_active.is_(True))
            .order_by(OutlineNode.id)
        )
        nodes = result.all()
    if not nodes:
        result = await session.scalars(
            select(OutlineNode)
            .options(selectinload(OutlineNode.region))
            .where(OutlineNode.is_active.is_(True))
            .order_by(OutlineNode.id)
        )
        nodes = result.all()
    if not nodes:
        raise NoOutlineNodesAvailable()
    node = nodes[0]
    region_value = node.region.code if node.region else None
    return OutlineNodeAssignment(
        node_id=node.id,
        host=node.host,
        port=node.port,
        method=node.method,
        password=node.password,
        region=region_value,
    )
