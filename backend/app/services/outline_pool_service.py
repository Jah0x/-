from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.models.outline_node import OutlineNode
from app.models.outline_pool import OutlinePool
from app.models.outline_pool_node import OutlinePoolNode
from app.models.outline_pool_region import OutlinePoolRegion
from app.models.region import Region


class OutlinePoolNotFound(Exception):
    pass


async def get_active_pool(session: AsyncSession, pool_code: str) -> OutlinePool:
    query = select(OutlinePool).where(OutlinePool.code == pool_code, OutlinePool.is_active.is_(True))
    pool = await session.scalar(query)
    if not pool:
        raise OutlinePoolNotFound()
    return pool


async def list_pool_regions(session: AsyncSession, pool_id: int) -> list[Region]:
    result = await session.scalars(
        select(OutlinePoolRegion)
        .options(selectinload(OutlinePoolRegion.region))
        .where(OutlinePoolRegion.pool_id == pool_id, OutlinePoolRegion.is_active.is_(True))
        .order_by(OutlinePoolRegion.priority.is_(None), OutlinePoolRegion.priority, OutlinePoolRegion.id)
    )
    regions: list[Region] = []
    for mapping in result:
        if mapping.region:
            regions.append(mapping.region)
    return regions


async def list_pool_nodes(session: AsyncSession, pool_id: int, region: Region | None = None) -> list[OutlineNode]:
    query = (
        select(OutlineNode)
        .join(OutlinePoolNode, OutlinePoolNode.outline_node_id == OutlineNode.id)
        .options(selectinload(OutlineNode.region))
        .where(
            OutlinePoolNode.pool_id == pool_id,
            OutlinePoolNode.is_active.is_(True),
            OutlineNode.is_active.is_(True),
            OutlineNode.is_deleted.is_(False),
        )
        .order_by(
            OutlinePoolNode.priority.is_(None),
            OutlinePoolNode.priority,
            OutlineNode.priority.is_(None),
            OutlineNode.priority,
            OutlineNode.id,
        )
    )
    if region:
        result = await session.scalars(query.where(OutlineNode.region_id == region.id))
        return result.all()
    result = await session.scalars(query)
    return result.all()


async def collect_pool_nodes(session: AsyncSession, pool_code: str, region_code: str | None) -> tuple[OutlinePool, list[OutlineNode]]:
    pool = await get_active_pool(session, pool_code)
    selected_regions: list[Region] = []
    if region_code:
        region = await session.scalar(select(Region).where(Region.code == region_code))
        if region:
            selected_regions.append(region)
    if not selected_regions:
        selected_regions = await list_pool_regions(session, pool.id)
    nodes: list[OutlineNode] = []
    for region in selected_regions:
        nodes = await list_pool_nodes(session, pool.id, region)
        if nodes:
            break
    if not nodes:
        nodes = await list_pool_nodes(session, pool.id)
    return pool, nodes
