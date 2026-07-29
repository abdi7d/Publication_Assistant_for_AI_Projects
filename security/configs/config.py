from pydantic import BaseSettings, AnyUrl
from typing import List


class Settings(BaseSettings):
    APP_ENV: str = "production"
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = 3600
    REDIS_URL: str | None = None
    MAX_UPLOAD_SIZE: int = 5 * 1024 * 1024  # 5MB
    ALLOWED_FILE_EXTENSIONS: List[str] = [".md", ".txt", ".pdf", ".png", ".jpg", ".jpeg"]
    RATE_LIMIT_RPS: int = 5
    RATE_LIMIT_BURST: int = 10

    class Config:
        env_file = ".env"


settings = Settings()
from pydantic import BaseSettings, Field
from typing import Optional, Tuple


class Settings(BaseSettings):
    APP_NAME: str = "Publication Assistant"
    ENV: str = "development"
    DEBUG: bool = False

    # Auth
    JWT_SECRET: str = Field(..., env="JWT_SECRET")
    JWT_ALGORITHM: str = "HS256"
    API_KEY: Optional[str] = None

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 20

    # File upload limits
    MAX_UPLOAD_SIZE_BYTES: int = 5 * 1024 * 1024  # 5 MB
    ALLOWED_EXTENSIONS: Tuple[str, ...] = (".md", ".txt", ".py", ".ipynb", ".pdf")

    # Monitoring
    ENABLE_METRICS: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
