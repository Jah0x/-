from fastapi import APIRouter
from app.api.v1 import auth, nodes, usage, health, heartbeat, admin_outline_nodes, httvps


router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router, prefix="/auth")
router.include_router(nodes.router, prefix="/nodes")
router.include_router(usage.router)
router.include_router(heartbeat.router)
router.include_router(admin_outline_nodes.router)
router.include_router(httvps.router, prefix="/httvps")
