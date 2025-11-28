from datetime import datetime, timedelta, timezone
import jwt
from app.core.config import Settings


def create_token(payload: dict, settings: Settings) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    body = {**payload, "exp": exp}
    return jwt.encode(body, settings.secret_key, algorithm=settings.jwt_algorithm)


def verify_token(token: str, settings: Settings) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
