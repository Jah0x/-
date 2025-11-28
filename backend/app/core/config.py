from functools import lru_cache
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    db_dsn: str = Field(alias="BACKEND_DB_DSN")
    secret_key: str = Field(alias="BACKEND_SECRET_KEY")
    debug: bool = Field(default=False, alias="BACKEND_DEBUG")
    host: str = Field(default="0.0.0.0", alias="BACKEND_HOST")
    port: int = Field(default=8000, alias="BACKEND_PORT")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_expire_minutes: int = Field(default=60, alias="JWT_EXPIRE_MINUTES")
    outline_healthcheck_interval_seconds: int = Field(default=60, alias="OUTLINE_HEALTHCHECK_INTERVAL_SECONDS")
    outline_healthcheck_timeout_seconds: float = Field(default=5.0, alias="OUTLINE_HEALTHCHECK_TIMEOUT_SECONDS")
    outline_healthcheck_degraded_threshold_ms: int = Field(default=1500, alias="OUTLINE_HEALTHCHECK_DEGRADED_THRESHOLD_MS")
    httvps_gateway_url: str = Field(default="https://localhost:8443/ws", alias="HTTVPS_GATEWAY_URL")
    httvps_session_ttl_seconds: int = Field(default=600, alias="HTTVPS_SESSION_TTL_SECONDS")
    httvps_max_streams: int = Field(default=8, alias="HTTVPS_MAX_STREAMS")
    gateway_internal_secret: str = Field(default="", alias="BACKEND_GATEWAY_SECRET")
    outline_default_pool_code: str | None = Field(default=None, alias="OUTLINE_DEFAULT_POOL_CODE")


@lru_cache
def get_settings() -> Settings:
    return Settings()
