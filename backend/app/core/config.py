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


@lru_cache
def get_settings() -> Settings:
    return Settings()
