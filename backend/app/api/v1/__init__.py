from fastapi import APIRouter
from app.api.v1 import auth, nodes, usage, health, heartbeat


router = APIRouter(prefix="/api/v1")
router.include_router(health.router)
router.include_router(auth.router, prefix="/auth")
router.include_router(nodes.router, prefix="/nodes")
router.include_router(usage.router)
router.include_router(heartbeat.router)
