"""
EAZY Models Package.

Import all models here to ensure they are registered with SQLAlchemy metadata.
This is required for foreign key relationships to work correctly.
"""

from app.models.asset import Asset, AssetDiscovery, AssetSource, AssetType
from app.models.project import Project, ProjectCreate, ProjectRead, ProjectUpdate
from app.models.target import Target, TargetCreate, TargetRead
from app.models.task import Task, TaskRead, TaskStatus, TaskType

__all__ = [
    # Project
    "Project",
    "ProjectCreate",
    "ProjectUpdate",
    "ProjectRead",
    # Target
    "Target",
    "TargetCreate",
    "TargetRead",
    # Task
    "Task",
    "TaskRead",
    "TaskStatus",
    "TaskType",
    # Asset
    "Asset",
    "AssetDiscovery",
    "AssetType",
    "AssetSource",
]
