from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class TargetBase(BaseModel):
    name: str
    url: str

class TargetCreate(TargetBase):
    pass

class TargetUpdate(BaseModel):
    name: Optional[str] = None

class TargetResponse(TargetBase):
    id: int
    project_id: int
    created_at: datetime

    class Config:
        from_attributes = True
