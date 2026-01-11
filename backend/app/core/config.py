from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    API_V1_STR: str = "/api/v1"
    PROJECT_NAME: str = "EAZY Backend"

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
