from typing import List
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.target import Target, TargetCreate

class TargetService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_target(self, project_id: int, target_in: TargetCreate) -> Target:
        db_target = Target(**target_in.model_dump(), project_id=project_id)
        self.session.add(db_target)
        await self.session.commit()
        await self.session.refresh(db_target)
        return db_target

    async def get_targets(self, project_id: int, skip: int = 0, limit: int = 100) -> List[Target]:
        query = select(Target).where(Target.project_id == project_id).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return result.all()
