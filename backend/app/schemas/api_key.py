from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ApiKeyBase(BaseModel):
    name: str
    provider: str
    api_base: Optional[str] = None

class ApiKeyCreate(ApiKeyBase):
    key: str  # Raw key from user

class ApiKeyUpdate(BaseModel):
    name: Optional[str] = None
    provider: Optional[str] = None
    key: Optional[str] = None
    api_base: Optional[str] = None

class ApiKeyResponse(ApiKeyBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # We never return the key itself in response

    class Config:
        from_attributes = True
