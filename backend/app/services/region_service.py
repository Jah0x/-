from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.region import Region


class RegionNotFound(Exception):
    pass


class RegionCodeAlreadyExists(Exception):
    pass


async def list_regions(session: AsyncSession) -> list[Region]:
    result = await session.scalars(select(Region).order_by(Region.id))
    return result.all()


async def get_region(session: AsyncSession, region_id: int) -> Region:
    region = await session.get(Region, region_id)
    if not region:
        raise RegionNotFound()
    return region


async def find_region_by_code(session: AsyncSession, code: str) -> Region | None:
    return await session.scalar(select(Region).where(Region.code == code))


async def create_region(session: AsyncSession, data: dict) -> Region:
    existing = await find_region_by_code(session, data.get("code")) if data.get("code") else None
    if existing:
        raise RegionCodeAlreadyExists()
    region = Region(**data)
    session.add(region)
    await session.commit()
    await session.refresh(region)
    return region


async def update_region(session: AsyncSession, region_id: int, data: dict) -> Region:
    region = await get_region(session, region_id)
    if "code" in data and data["code"] != region.code:
        existing = await find_region_by_code(session, data["code"])
        if existing:
            raise RegionCodeAlreadyExists()
    for key, value in data.items():
        setattr(region, key, value)
    await session.commit()
    await session.refresh(region)
    return region


async def delete_region(session: AsyncSession, region_id: int) -> None:
    region = await get_region(session, region_id)
    await session.delete(region)
    await session.commit()
