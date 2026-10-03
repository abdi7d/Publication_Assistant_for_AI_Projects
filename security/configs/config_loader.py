from __future__ import annotations
import os
from typing import Optional, Sequence

try:
    from pydantic import BaseModel, Field, ValidationError
except Exception:  # pragma: no cover
    from pydantic.v1 import BaseModel, Field, ValidationError  # type: ignore


def _env_list(name: str, default: Sequence[str]) -> list[str]:
    value = os.getenv(name)
    if not value:
        return list(default)
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings(BaseModel):
    APP_NAME: str = Field(default_factory=lambda: os.getenv(
        "APP_NAME", "Publication Assistant"))
    APP_ENV: str = Field(
        default_factory=lambda: os.getenv("APP_ENV", "development"))
    DEBUG: bool = Field(default_factory=lambda: os.getenv(
        "APP_ENV", "development").lower() == "development")

    JWT_SECRET: str = Field(
        default_factory=lambda: os.getenv("JWT_SECRET", "dev-secret"))
    JWT_ALGORITHM: str = Field(
        default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    ACCESS_TOKEN_EXPIRE_SECONDS: int = Field(default_factory=lambda: int(
        os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", "3600")))

    SECRET_KEY: str = Field(
        default_factory=lambda: os.getenv("SECRET_KEY", "dev-secret"))
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default_factory=lambda: int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60")))
    REFRESH_TOKEN_EXPIRE_DAYS: int = Field(
        default_factory=lambda: int(os.getenv("REFRESH_TOKEN_EXPIRE_DAYS", "7")))

    REDIS_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("REDIS_URL"))
    SENTRY_DSN: Optional[str] = Field(
        default_factory=lambda: os.getenv("SENTRY_DSN"))

    LOG_DIR: str = Field(default_factory=lambda: os.getenv("LOG_DIR", "logs"))
    LOG_LEVEL: str = Field(
        default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    MODEL_API_KEY: Optional[str] = Field(
        default_factory=lambda: os.getenv("MODEL_API_KEY"))
    DATABASE_URL: Optional[str] = Field(
        default_factory=lambda: os.getenv("DATABASE_URL"))

    MAX_PROMPT_LENGTH: int = Field(default_factory=lambda: int(
        os.getenv("MAX_PROMPT_LENGTH", "5000")))
    MAX_UPLOAD_BYTES: int = Field(default_factory=lambda: int(
        os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024))))
    RATE_LIMIT_PER_MINUTE: int = Field(default_factory=lambda: int(
        os.getenv("RATE_LIMIT_PER_MINUTE", "60")))
    RATE_LIMIT_BURST: int = Field(default_factory=lambda: int(
        os.getenv("RATE_LIMIT_BURST", "20")))

    CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: _env_list("CORS_ORIGINS", ["*"]))
    ALLOWED_HOSTS: list[str] = Field(
        default_factory=lambda: _env_list("ALLOWED_HOSTS", ["*"]))


settings = Settings()
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


__all__ = ["Settings", "get_settings", "settings"]
