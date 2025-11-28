from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.nodes import OutlineNodeAssignmentRequest, OutlineNodeAssignment, OutlineRevokeRequest, OutlineRevokeResponse
from app.services.nodes_service import (
    assign_outline_node,
    revoke_outline_key,
    NoOutlineNodesAvailable,
    NoHealthyOutlineNodesError,
    OutlineProvisioningError,
)


router = APIRouter()


@router.post("/assign-outline", response_model=OutlineNodeAssignment)
async def assign_outline(body: OutlineNodeAssignmentRequest, session: AsyncSession = Depends(get_session)):
    try:
        assignment = await assign_outline_node(session, body.region_code, body.device_id, pool_code=body.pool_code)
    except NoOutlineNodesAvailable:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="no_outline_nodes_available")
    except NoHealthyOutlineNodesError:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="no_healthy_outline_nodes")
    except OutlineProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return assignment


@router.post("/revoke-outline", response_model=OutlineRevokeResponse)
async def revoke_outline(body: OutlineRevokeRequest, request: Request, session: AsyncSession = Depends(get_session)):
    client_class = getattr(request.app.state, "outline_client_class", None)
    try:
        revoked = await revoke_outline_key(session, body.device_id, client_class=client_class or None)
    except OutlineProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return OutlineRevokeResponse(revoked=revoked)
