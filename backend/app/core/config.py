from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "EAZY"
    API_V1_STR: str = "/api/v1"

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "eazy_db"
    POSTGRES_PORT: str = "5432"

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        return f"postgresql://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    # Crawler Settings
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36 EAZY-Crawler"
    CRAWLER_TIMEOUT_MS: int = 15000
    CRAWLER_RENDER_WAIT_MS: int = 2000

    # Security
    # Default key for dev only. In prod, this must be set via env var.
    # Generated using: Fernet.generate_key().decode()
    ENCRYPTION_KEY: str = "J1qK1_M4dD-V9_Z5g4B5k5_L6rT7_X8n9_M0pQ1rS2t=" 

    class Config:
        env_file = ".env"

settings = Settings()
