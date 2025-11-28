import asyncio
import logging
import time
from datetime import datetime, timezone
from enum import StrEnum
import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.clients.outline_client import OutlineClient, OutlineClientError
from app.core.config import Settings
from app.core.database import SessionLocal
from app.models.outline_node import OutlineNode


class OutlineHealthStatus(StrEnum):
    healthy = "healthy"
    degraded = "degraded"
    down = "down"
    unknown = "unknown"


logger = logging.getLogger(__name__)


def evaluate_status(latency_ms: float | None, error: str | None, settings: Settings) -> str:
    if error or latency_ms is None:
        return OutlineHealthStatus.down.value
    if latency_ms > settings.outline_healthcheck_degraded_threshold_ms:
        return OutlineHealthStatus.degraded.value
    return OutlineHealthStatus.healthy.value


async def check_outline_node(node: OutlineNode, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> tuple[str, float | None, str | None]:
    if not node.api_url or not node.api_key:
        return OutlineHealthStatus.down.value, None, "outline_api_not_configured"
    start = time.perf_counter()
    client = OutlineClient(
        node.api_url,
        node.api_key,
        timeout=settings.outline_healthcheck_timeout_seconds,
        transport=transport,
    )
    latency_ms = None
    error_text = None
    try:
        await client.health_check()
        latency_ms = (time.perf_counter() - start) * 1000
    except OutlineClientError as exc:
        error_text = str(exc)
    except httpx.HTTPError as exc:
        error_text = str(exc)
    status = evaluate_status(latency_ms, error_text, settings)
    return status, latency_ms, error_text


async def update_node_health(
    session: AsyncSession,
    node: OutlineNode,
    status: str,
    latency_ms: float | None,
    error_text: str | None,
) -> None:
    previous_status = node.last_check_status
    node.last_check_at = datetime.now(timezone.utc)
    node.last_check_status = status
    node.recent_latency_ms = int(latency_ms) if latency_ms is not None else None
    node.last_error = error_text
    await session.flush()
    if previous_status != status:
        logger.info("outline_node_status_changed", extra={"node_id": node.id, "from": previous_status, "to": status})


async def run_healthcheck_cycle(session: AsyncSession, settings: Settings, transport: httpx.AsyncBaseTransport | None = None) -> None:
    result = await session.scalars(
        select(OutlineNode).where(OutlineNode.is_active.is_(True), OutlineNode.is_deleted.is_(False))
    )
    nodes = result.all()
    for node in nodes:
        status, latency_ms, error_text = await check_outline_node(node, settings, transport=transport)
        await update_node_health(session, node, status, latency_ms, error_text)
    await session.commit()


async def outline_healthcheck_loop(settings: Settings) -> None:
    if settings.outline_healthcheck_interval_seconds <= 0:
        return
    while True:
        try:
            async with SessionLocal() as session:
                await run_healthcheck_cycle(session, settings)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("outline_healthcheck_failed")
        await asyncio.sleep(settings.outline_healthcheck_interval_seconds)


async def start_outline_healthcheck_background(settings: Settings) -> asyncio.Task | None:
    if settings.outline_healthcheck_interval_seconds <= 0:
        return None
    task = asyncio.create_task(outline_healthcheck_loop(settings))
    return task


async def trigger_outline_healthcheck(
    session: AsyncSession, node_id: int, settings: Settings, transport: httpx.AsyncBaseTransport | None = None
) -> OutlineNode | None:
    node = await session.scalar(
        select(OutlineNode).where(OutlineNode.id == node_id, OutlineNode.is_deleted.is_(False))
    )
    if not node:
        return None
    status, latency_ms, error_text = await check_outline_node(node, settings, transport=transport)
    await update_node_health(session, node, status, latency_ms, error_text)
    await session.commit()
    await session.refresh(node)
    return node
