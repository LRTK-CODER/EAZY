from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "EAZY Backend"
    API_V1_STR: str = "/api/v1"
    
    # DATABASE
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/eazy_db"
    
    # REDIS
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # SECURITY
    SECRET_KEY: str = "CHANGE_THIS_TO_A_SECURE_KEY_IN_PRODUCTION"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    
    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings()
