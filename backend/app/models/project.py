from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class ProjectBase(SQLModel):
    name: str = Field(index=True, max_length=255)
    description: Optional[str] = Field(default=None)

class Project(ProjectBase, table=True):
    __tablename__ = "projects"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class ProjectCreate(ProjectBase):
    pass

class ProjectRead(ProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime
