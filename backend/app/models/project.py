from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel

from app.core.utils import utc_now

class ProjectBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None)

class Project(ProjectBase, table=True):
    __tablename__ = "projects"

    id: Optional[int] = Field(default=None, primary_key=True)
    is_archived: bool = Field(default=False, index=True)
    archived_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class ProjectCreate(ProjectBase):
    pass

class ProjectUpdate(SQLModel):
    name: Optional[str] = None
    description: Optional[str] = None

class ProjectRead(ProjectBase):
    id: int
    is_archived: bool
    archived_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
