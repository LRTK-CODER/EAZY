from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class LLMConfigBase(BaseModel):
    model_name: str
    api_key_id: int

class LLMConfigCreate(LLMConfigBase):
    pass

class LLMConfigUpdate(BaseModel):
    model_name: Optional[str] = None
    api_key_id: Optional[int] = None

class LLMConfigResponse(LLMConfigBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
