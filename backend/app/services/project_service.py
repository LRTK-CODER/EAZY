from typing import List, Optional

from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.utils import utc_now
from app.models.project import Project, ProjectCreate, ProjectUpdate


class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(self, project_in: ProjectCreate) -> Project:
        db_project = Project.model_validate(project_in)
        self.session.add(db_project)
        await self.session.commit()
        await self.session.refresh(db_project)
        return db_project

    async def get_projects(
        self, skip: int = 0, limit: int = 100, archived: bool = False
    ) -> List[Project]:
        """Get projects, by default excludes archived"""
        query = (
            select(Project)
            .where(Project.is_archived == archived)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(query)
        return result.all()

    async def get_project(self, project_id: int) -> Optional[Project]:
        return await self.session.get(Project, project_id)

    async def update_project(
        self, project_id: int, project_update: ProjectUpdate
    ) -> Optional[Project]:
        """Update project and return updated instance, or None if not found"""
        db_project = await self.session.get(Project, project_id)
        if not db_project:
            return None

        # Update only provided fields
        update_data = project_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_project, key, value)

        # Update timestamp
        db_project.updated_at = utc_now()

        self.session.add(db_project)
        await self.session.commit()
        await self.session.refresh(db_project)
        return db_project

    async def archive_project(self, project_id: int) -> bool:
        """Archive project (soft delete) and return True if successful, False if not found"""
        db_project = await self.session.get(Project, project_id)
        if not db_project:
            return False

        db_project.is_archived = True
        db_project.archived_at = utc_now()
        db_project.updated_at = utc_now()

        self.session.add(db_project)
        await self.session.commit()
        return True

    async def delete_project_permanent(self, project_id: int) -> bool:
        """Permanently delete project from DB (hard delete), return True if deleted, False if not found"""
        db_project = await self.session.get(Project, project_id)
        if not db_project:
            return False

        await self.session.delete(db_project)
        await self.session.commit()
        return True

    async def restore_project(self, project_id: int) -> bool:
        """Restore archived project (set is_archived=False, archived_at=None)"""
        db_project = await self.session.get(Project, project_id)
        if not db_project:
            return False

        db_project.is_archived = False
        db_project.archived_at = None
        db_project.updated_at = utc_now()

        self.session.add(db_project)
        await self.session.commit()
        return True

    async def restore_projects(self, project_ids: List[int]) -> int:
        """Bulk restore projects, return count of restored projects"""
        count = 0
        for project_id in project_ids:
            if await self.restore_project(project_id):
                count += 1
        return count
