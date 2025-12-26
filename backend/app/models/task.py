from datetime import datetime, timezone
from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum

def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)

class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskType(str, Enum):
    CRAWL = "crawl"
    SCAN = "scan"

class TaskBase(SQLModel):
    project_id: int = Field(foreign_key="projects.id", nullable=False)
    target_id: Optional[int] = Field(default=None, foreign_key="targets.id")
    type: TaskType = Field(default=TaskType.CRAWL)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[str] = Field(default=None) # JSON string for result summary

class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
