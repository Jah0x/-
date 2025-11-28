from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.plan import Plan


class PlanNotFound(Exception):
    pass


async def list_plans(session: AsyncSession) -> list[Plan]:
    result = await session.scalars(select(Plan).order_by(Plan.id))
    return result.all()


async def get_plan(session: AsyncSession, plan_id: int) -> Plan:
    plan = await session.get(Plan, plan_id)
    if not plan:
        raise PlanNotFound()
    return plan


async def create_plan(session: AsyncSession, data: dict) -> Plan:
    plan = Plan(**data)
    session.add(plan)
    await session.commit()
    await session.refresh(plan)
    return plan


async def update_plan(session: AsyncSession, plan_id: int, data: dict) -> Plan:
    plan = await get_plan(session, plan_id)
    for key, value in data.items():
        setattr(plan, key, value)
    await session.commit()
    await session.refresh(plan)
    return plan


async def delete_plan(session: AsyncSession, plan_id: int) -> None:
    plan = await get_plan(session, plan_id)
    await session.delete(plan)
    await session.commit()
