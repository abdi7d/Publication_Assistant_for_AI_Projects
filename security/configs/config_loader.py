from __future__ import annotations
import os
from typing import Optional

try:
    from pydantic import BaseModel, Field, ValidationError
except Exception:  # pragma: no cover
    from pydantic.v1 import BaseModel, Field, ValidationError  # type: ignore


class Settings(BaseModel):
    APP_ENV: str = Field("production")
    DEBUG: bool = Field(False)

    JWT_SECRET: str = Field("dev-secret")
    JWT_ALGORITHM: str = Field("HS256")
    ACCESS_TOKEN_EXPIRE_SECONDS: int = Field(3600)

    SECRET_KEY: str = Field("dev-secret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60)
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(7)

    REDIS_URL: Optional[str] = Field(None)
    SENTRY_DSN: Optional[str] = Field(None)

    LOG_DIR: str = Field("logs")
    LOG_LEVEL: str = Field("INFO")
    MODEL_API_KEY: Optional[str] = Field(None)
    DATABASE_URL: Optional[str] = Field(None)

    MAX_PROMPT_LENGTH: int = Field(5000)
    MAX_UPLOAD_BYTES: int = Field(10 * 1024 * 1024)
    RATE_LIMIT_PER_MINUTE: int = Field(60)
    RATE_LIMIT_BURST: int = Field(20)


settings = Settings()
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


__all__ = ["Settings", "get_settings", "settings"]
