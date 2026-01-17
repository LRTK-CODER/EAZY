from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EAZY Backend"

    # === Crawler Settings (from constants.py) ===
    CRAWLER_MAX_BODY_SIZE: int = Field(
        default=10 * 1024,  # 10KB
        ge=1024,  # 최소 1KB
        description="Maximum HTTP body size in bytes",
    )
    CRAWLER_PAGE_TIMEOUT_MS: int = Field(
        default=30000,  # 30초
        ge=1000,  # 최소 1초
        le=300000,  # 최대 5분
        description="Page load timeout in milliseconds",
    )

    # === Worker Settings (from constants.py) ===
    WORKER_LOCK_TTL: int = Field(
        default=600,  # 10분
        ge=60,  # 최소 1분
        description="Distributed lock TTL in seconds",
    )
    WORKER_CANCELLATION_CHECK_INTERVAL: float = Field(
        default=5.0,  # 5초
        ge=1.0,  # 최소 1초
        description="Task cancellation check interval in seconds",
    )

    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: str = "5432"
    POSTGRES_DB: str = "eazy_db"

    @property
    def DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    # REDIS
    REDIS_URL: str = "redis://localhost:6379/0"

    # SECURITY
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days

    # WORKER POOL (Phase 4)
    WORKER_NUM_WORKERS: int = 4
    WORKER_SHUTDOWN_TIMEOUT: int = 30
    WORKER_MAX_RESTARTS: int = 5

    # WORKER POOL - Aging (Sprint 3.1)
    WORKER_AGING_ENABLED: bool = False
    WORKER_AGING_INTERVAL: int = 60  # seconds

    # CORS (Sprint 2.5)
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS: str = "*"

    # ENVIRONMENT
    ENVIRONMENT: str = "development"  # development, staging, production

    model_config = SettingsConfigDict(case_sensitive=True, env_file=".env")


settings = Settings()
