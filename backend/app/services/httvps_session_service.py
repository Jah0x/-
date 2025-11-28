import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.auth_service import validate_device
from app.services.nodes_service import assign_outline_node, OutlineProvisioningError, NoOutlineNodesAvailable, NoHealthyOutlineNodesError


class SessionDescriptorStore:
    def __init__(self):
        self._storage: dict[str, dict[str, Any]] = {}

    def put(self, token: str, payload: dict[str, Any]) -> None:
        self._storage[token] = payload

    def get(self, token: str) -> dict[str, Any] | None:
        return self._storage.get(token)

    def delete(self, token: str) -> None:
        self._storage.pop(token, None)


store = SessionDescriptorStore()


async def issue_session_descriptor(db: AsyncSession, device_id: str, token: str, region: str | None, settings: Settings) -> dict[str, Any]:
    validation = await validate_device(db, device_id, token, settings)
    if not validation.get("allowed"):
        return {"allowed": False, "reason": validation.get("reason", "not_allowed"), "subscription_status": validation.get("subscription_status")}
    try:
        assignment = await assign_outline_node(db, region, device_id, pool_code=settings.outline_default_pool_code)
    except (OutlineProvisioningError, NoOutlineNodesAvailable, NoHealthyOutlineNodesError) as exc:
        return {"allowed": False, "reason": str(exc)}
    session_token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=max(settings.httvps_session_ttl_seconds, 60))
    descriptor = {
        "allowed": True,
        "session_token": session_token,
        "expires_at": expires_at,
        "gateway_url": settings.httvps_gateway_url,
        "max_streams": settings.httvps_max_streams,
        "device_id": device_id,
        "user_id": validation.get("user_id"),
        "outline": assignment.model_dump(),
    }
    store.put(session_token, descriptor)
    return descriptor


async def validate_session_token(session_token: str) -> dict[str, Any] | None:
    descriptor = store.get(session_token)
    if not descriptor:
        return None
    expires_at = descriptor.get("expires_at")
    if expires_at and datetime.now(timezone.utc) > expires_at:
        store.delete(session_token)
        return None
    return descriptor
