from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.nodes import OutlineNodeAssignmentRequest, OutlineNodeAssignment
from app.services.nodes_service import assign_outline_node, NoOutlineNodesAvailable, OutlineProvisioningError


router = APIRouter()


@router.post("/assign-outline", response_model=OutlineNodeAssignment)
async def assign_outline(body: OutlineNodeAssignmentRequest, session: AsyncSession = Depends(get_session)):
    try:
        assignment = await assign_outline_node(session, body.region_code, body.device_id)
    except NoOutlineNodesAvailable:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="no_outline_nodes_available")
    except OutlineProvisioningError as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(exc))
    return assignment
