from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.nodes import OutlineNodeStatus
from app.services.nodes_service import list_outline_nodes, build_outline_node_status
from app.services.outline_health_service import trigger_outline_healthcheck
from app.api.admin import require_admin


router = APIRouter(prefix="/admin/outline-nodes")


@router.get("/", response_model=list[OutlineNodeStatus], dependencies=[Depends(require_admin)])
async def list_nodes(session: AsyncSession = Depends(get_session)):
    nodes = await list_outline_nodes(session)
    statuses = []
    for node in nodes:
        statuses.append(await build_outline_node_status(session, node))
    return statuses


@router.get("/{node_id}", response_model=OutlineNodeStatus, dependencies=[Depends(require_admin)])
async def get_node(node_id: int, session: AsyncSession = Depends(get_session)):
    nodes = await list_outline_nodes(session)
    node = next((item for item in nodes if item.id == node_id), None)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return await build_outline_node_status(session, node)


@router.post("/{node_id}/check", response_model=OutlineNodeStatus, dependencies=[Depends(require_admin)])
async def manual_check(node_id: int, session: AsyncSession = Depends(get_session)):
    settings = get_settings()
    node = await trigger_outline_healthcheck(session, node_id, settings)
    if not node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return await build_outline_node_status(session, node)
