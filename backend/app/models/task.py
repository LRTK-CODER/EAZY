from datetime import datetime
from typing import Optional
from sqlmodel import Field, SQLModel, Column
from sqlalchemy import ForeignKey
from enum import Enum

from app.core.utils import utc_now


class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class TaskType(str, Enum):
    CRAWL = "crawl"
    SCAN = "scan"


class TaskBase(SQLModel):
    project_id: int = Field(foreign_key="projects.id", nullable=False)
    target_id: Optional[int] = Field(
        default=None, sa_column=Column(ForeignKey("targets.id", ondelete="CASCADE"))
    )
    type: TaskType = Field(default=TaskType.CRAWL)
    status: TaskStatus = Field(default=TaskStatus.PENDING)
    result: Optional[str] = Field(default=None)  # JSON string for result summary


class Task(TaskBase, table=True):
    __tablename__ = "tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
    started_at: Optional[datetime] = Field(default=None)
    completed_at: Optional[datetime] = Field(default=None)


class TaskRead(TaskBase):
    id: int
    created_at: datetime
    updated_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
