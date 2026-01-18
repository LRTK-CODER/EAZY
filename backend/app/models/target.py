from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

from app.core.utils import utc_now

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


class TargetUpdate(SQLModel):
    name: Optional[str] = None
    url: Optional[str] = None
    description: Optional[str] = None
    scope: Optional[TargetScope] = None


class TargetRead(TargetBase):
    id: int
    project_id: int
    created_at: datetime
    updated_at: datetime
    asset_count: int = 0
