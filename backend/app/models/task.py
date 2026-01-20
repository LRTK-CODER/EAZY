from datetime import datetime
from enum import Enum
from typing import Optional

from sqlalchemy import ForeignKey, Index
from sqlmodel import Column, Field, SQLModel

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

    # 재귀 크롤링 필드
    depth: int = Field(default=0, description="현재 크롤링 깊이")
    max_depth: int = Field(default=3, description="최대 크롤링 깊이")
    parent_task_id: Optional[int] = Field(
        default=None,
        sa_column=Column(
            ForeignKey("tasks.id", ondelete="SET NULL"),
            nullable=True,
            index=True,
        ),
    )


class Task(TaskBase, table=True):
    __tablename__ = "tasks"
    __table_args__ = (
        Index("ix_tasks_target_depth", "target_id", "depth"),
        Index("ix_tasks_target_created", "target_id", "created_at"),
    )

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
