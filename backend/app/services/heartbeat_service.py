from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.gateway_node import GatewayNode
from app.models.outline_node import OutlineNode


async def record_gateway_heartbeat(session: AsyncSession, node_id: int | None) -> bool:
    if node_id is None:
        return False
    node = await session.scalar(select(GatewayNode).where(GatewayNode.id == node_id))
    if not node:
        return False
    node.last_heartbeat_at = datetime.now(timezone.utc)
    await session.commit()
    return True


async def record_outline_heartbeat(session: AsyncSession, node_id: int | None) -> bool:
    if node_id is None:
        return False
    node = await session.scalar(select(OutlineNode).where(OutlineNode.id == node_id))
    if not node:
        return False
    node.last_heartbeat_at = datetime.now(timezone.utc)
    await session.commit()
    return True
