from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession


from app.models.project import Project, ProjectCreate

class ProjectService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_project(self, project_in: ProjectCreate) -> Project:
        db_project = Project.model_validate(project_in)
        self.session.add(db_project)
        await self.session.commit()
        await self.session.refresh(db_project)
        return db_project

    async def get_projects(self, skip: int = 0, limit: int = 100) -> List[Project]:
        query = select(Project).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return result.all()

    async def get_project(self, project_id: int) -> Optional[Project]:
        return await self.session.get(Project, project_id)
