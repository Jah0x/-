from fastapi import FastAPI
from app.api.v1 import router as v1_router
from app.core.config import get_settings
from app.core.logging import configure_logging

settings = get_settings()
configure_logging("DEBUG" if settings.debug else "INFO")
app = FastAPI()
app.include_router(v1_router)
