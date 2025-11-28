import asyncio
from contextlib import suppress, asynccontextmanager
from fastapi import FastAPI
from app.api.v1 import router as v1_router
from app.api import internal as internal_router
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.services.outline_health_service import start_outline_healthcheck_background

settings = get_settings()
configure_logging("DEBUG" if settings.debug else "INFO")


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = await start_outline_healthcheck_background(settings)
    if task:
        app.state.outline_healthcheck_task = task
    yield
    if task:
        task.cancel()
        with suppress(asyncio.CancelledError):
            await task


app = FastAPI(lifespan=lifespan)
app.include_router(v1_router)
app.include_router(internal_router.router)
