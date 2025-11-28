from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_session
from app.schemas.nodes import OutlineNodeAssignmentRequest, OutlineNodeAssignment
from app.services.nodes_service import assign_outline_node


router = APIRouter()


@router.post("/assign-outline", response_model=OutlineNodeAssignment)
async def assign_outline(body: OutlineNodeAssignmentRequest, session: AsyncSession = Depends(get_session)):
    assignment = assign_outline_node(body.region_code)
    return assignment
