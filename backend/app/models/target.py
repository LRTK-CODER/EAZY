from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

from enum import Enum

class TargetScope(str, Enum):
    DOMAIN = "DOMAIN"
    SUBDOMAIN = "SUBDOMAIN"
    URL_ONLY = "URL_ONLY"

class TargetBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    url: str = Field(max_length=2048)
    description: Optional[str] = Field(default=None)
    scope: TargetScope = Field(default=TargetScope.DOMAIN)

class Target(TargetBase, table=True):
    __tablename__ = "targets"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    project_id: int = Field(foreign_key="projects.id", nullable=False)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class TargetCreate(TargetBase):
    pass

class TargetRead(TargetBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
