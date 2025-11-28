import json
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.admin_audit_log import AdminAuditLog


async def record_admin_action(
    session: AsyncSession,
    actor: str,
    action: str,
    resource_type: str,
    resource_id: str | None,
    payload: dict | None,
) -> None:
    record = AdminAuditLog(
        actor=actor,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=json.loads(json.dumps(payload)) if payload is not None else None,
    )
    session.add(record)
    await session.commit()


async def list_audit_logs(session: AsyncSession, limit: int = 100) -> list[AdminAuditLog]:
    result = await session.scalars(
        select(AdminAuditLog).order_by(AdminAuditLog.id.desc()).limit(limit)
    )
    return result.all()
