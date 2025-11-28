from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.admin import require_admin
from app.core.database import get_session
from app.schemas.admin import OperationStatus, AdminAuditEntry
from app.schemas.plan import PlanInfo, PlanCreate, PlanUpdate
from app.schemas.region import RegionInfo, RegionCreate, RegionUpdate
from app.schemas.nodes import (
    OutlineNodeCreate,
    OutlineNodeUpdate,
    OutlineNodeInfo,
    GatewayNodeCreate,
    GatewayNodeUpdate,
    GatewayNodeInfo,
)
from app.services.plan_service import list_plans, create_plan, update_plan, delete_plan, get_plan, PlanNotFound
from app.services.region_service import (
    list_regions,
    create_region,
    update_region,
    delete_region,
    get_region,
    RegionNotFound,
    RegionCodeAlreadyExists,
)
from app.services.admin_nodes_service import (
    list_outline_nodes_full,
    create_outline_node,
    update_outline_node,
    delete_outline_node,
    get_outline_node,
    list_gateway_nodes,
    create_gateway_node,
    update_gateway_node,
    delete_gateway_node,
    get_gateway_node,
    NodeNotFound,
    RegionForNodeNotFound,
)
from app.services.audit_service import record_admin_action, list_audit_logs


router = APIRouter(prefix="/admin")


def build_outline_info(node) -> OutlineNodeInfo:
    region_value = node.region.code if node.region else None
    return OutlineNodeInfo(
        id=node.id,
        name=node.name,
        region=region_value,
        host=node.host,
        port=node.port,
        method=node.method,
        password=node.password,
        api_url=node.api_url,
        api_key=node.api_key,
        tag=node.tag,
        priority=node.priority,
        is_active=node.is_active,
        is_deleted=node.is_deleted,
    )


def build_gateway_info(node) -> GatewayNodeInfo:
    region_value = node.region.code if node.region else None
    return GatewayNodeInfo(
        id=node.id,
        region=region_value,
        host=node.host,
        port=node.port,
        is_active=node.is_active,
    )


@router.get("/plans", response_model=list[PlanInfo], dependencies=[Depends(require_admin)])
async def admin_list_plans(session: AsyncSession = Depends(get_session)):
    plans = await list_plans(session)
    return plans


@router.post("/plans", response_model=PlanInfo)
async def admin_create_plan(
    body: PlanCreate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    plan = await create_plan(session, body.model_dump())
    await record_admin_action(
        session,
        admin_token,
        "create",
        "plan",
        str(plan.id),
        body.model_dump(),
    )
    return plan


@router.get("/plans/{plan_id}", response_model=PlanInfo)
async def admin_get_plan(plan_id: int, session: AsyncSession = Depends(get_session), admin_token: str = Depends(require_admin)):
    try:
        plan = await get_plan(session, plan_id)
    except PlanNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return plan


@router.put("/plans/{plan_id}", response_model=PlanInfo)
async def admin_update_plan(
    plan_id: int,
    body: PlanUpdate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_body")
    try:
        plan = await update_plan(session, plan_id, update_data)
    except PlanNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await record_admin_action(
        session,
        admin_token,
        "update",
        "plan",
        str(plan.id),
        update_data,
    )
    return plan


@router.delete("/plans/{plan_id}", response_model=OperationStatus)
async def admin_delete_plan(
    plan_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        await delete_plan(session, plan_id)
    except PlanNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await record_admin_action(session, admin_token, "delete", "plan", str(plan_id), None)
    return OperationStatus(status="deleted")


@router.get("/regions", response_model=list[RegionInfo], dependencies=[Depends(require_admin)])
async def admin_list_regions(session: AsyncSession = Depends(get_session)):
    regions = await list_regions(session)
    return regions


@router.post("/regions", response_model=RegionInfo)
async def admin_create_region(
    body: RegionCreate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        region = await create_region(session, body.model_dump())
    except RegionCodeAlreadyExists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="region_code_exists")
    await record_admin_action(
        session,
        admin_token,
        "create",
        "region",
        str(region.id),
        body.model_dump(),
    )
    return region


@router.get("/regions/{region_id}", response_model=RegionInfo)
async def admin_get_region(
    region_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        region = await get_region(session, region_id)
    except RegionNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return region


@router.put("/regions/{region_id}", response_model=RegionInfo)
async def admin_update_region(
    region_id: int,
    body: RegionUpdate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_body")
    try:
        region = await update_region(session, region_id, update_data)
    except RegionNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    except RegionCodeAlreadyExists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="region_code_exists")
    await record_admin_action(
        session,
        admin_token,
        "update",
        "region",
        str(region.id),
        update_data,
    )
    return region


@router.delete("/regions/{region_id}", response_model=OperationStatus)
async def admin_delete_region(
    region_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        await delete_region(session, region_id)
    except RegionNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await record_admin_action(session, admin_token, "delete", "region", str(region_id), None)
    return OperationStatus(status="deleted")


@router.get("/outline-nodes", response_model=list[OutlineNodeInfo], dependencies=[Depends(require_admin)])
async def admin_list_outline_nodes(session: AsyncSession = Depends(get_session)):
    nodes = await list_outline_nodes_full(session)
    return [build_outline_info(node) for node in nodes]


@router.post("/outline-nodes", response_model=OutlineNodeInfo)
async def admin_create_outline_node(
    body: OutlineNodeCreate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        node = await create_outline_node(session, body.model_dump(exclude_none=True))
    except RegionForNodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="region_not_found")
    await record_admin_action(
        session,
        admin_token,
        "create",
        "outline_node",
        str(node.id),
        body.model_dump(exclude_none=True),
    )
    return build_outline_info(node)


@router.get("/outline-nodes/{node_id}", response_model=OutlineNodeInfo)
async def admin_get_outline_node(
    node_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        node = await get_outline_node(session, node_id)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return build_outline_info(node)


@router.put("/outline-nodes/{node_id}", response_model=OutlineNodeInfo)
async def admin_update_outline_node(
    node_id: int,
    body: OutlineNodeUpdate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_body")
    try:
        node = await update_outline_node(session, node_id, update_data)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    except RegionForNodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="region_not_found")
    await record_admin_action(
        session,
        admin_token,
        "update",
        "outline_node",
        str(node.id),
        update_data,
    )
    return build_outline_info(node)


@router.delete("/outline-nodes/{node_id}", response_model=OperationStatus)
async def admin_delete_outline_node(
    node_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        await delete_outline_node(session, node_id)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await record_admin_action(session, admin_token, "delete", "outline_node", str(node_id), None)
    return OperationStatus(status="deleted")


@router.get("/gateway-nodes", response_model=list[GatewayNodeInfo], dependencies=[Depends(require_admin)])
async def admin_list_gateway_nodes(session: AsyncSession = Depends(get_session)):
    nodes = await list_gateway_nodes(session)
    return [build_gateway_info(node) for node in nodes]


@router.post("/gateway-nodes", response_model=GatewayNodeInfo)
async def admin_create_gateway_node(
    body: GatewayNodeCreate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        node = await create_gateway_node(session, body.model_dump(exclude_none=True))
    except RegionForNodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="region_not_found")
    await record_admin_action(
        session,
        admin_token,
        "create",
        "gateway_node",
        str(node.id),
        body.model_dump(exclude_none=True),
    )
    return build_gateway_info(node)


@router.get("/gateway-nodes/{node_id}", response_model=GatewayNodeInfo)
async def admin_get_gateway_node(
    node_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        node = await get_gateway_node(session, node_id)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    return build_gateway_info(node)


@router.put("/gateway-nodes/{node_id}", response_model=GatewayNodeInfo)
async def admin_update_gateway_node(
    node_id: int,
    body: GatewayNodeUpdate,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    update_data = body.model_dump(exclude_unset=True)
    if not update_data:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="empty_body")
    try:
        node = await update_gateway_node(session, node_id, update_data)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    except RegionForNodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="region_not_found")
    await record_admin_action(
        session,
        admin_token,
        "update",
        "gateway_node",
        str(node.id),
        update_data,
    )
    return build_gateway_info(node)


@router.delete("/gateway-nodes/{node_id}", response_model=OperationStatus)
async def admin_delete_gateway_node(
    node_id: int,
    session: AsyncSession = Depends(get_session),
    admin_token: str = Depends(require_admin),
):
    try:
        await delete_gateway_node(session, node_id)
    except NodeNotFound:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="not_found")
    await record_admin_action(session, admin_token, "delete", "gateway_node", str(node_id), None)
    return OperationStatus(status="deleted")


@router.get("/audit", response_model=list[AdminAuditEntry], dependencies=[Depends(require_admin)])
async def admin_list_audit_logs(
    session: AsyncSession = Depends(get_session),
    limit: int = Query(default=100, ge=1, le=1000),
):
    logs = await list_audit_logs(session, limit)
    return logs
