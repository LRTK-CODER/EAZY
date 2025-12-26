from typing import List, Optional
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.models.target import Target, TargetCreate, TargetUpdate

class TargetService:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create_target(self, project_id: int, target_in: TargetCreate) -> Target:
        db_target = Target(**target_in.model_dump(), project_id=project_id)
        self.session.add(db_target)
        await self.session.commit()
        await self.session.refresh(db_target)
        return db_target

    async def get_target(self, target_id: int) -> Optional[Target]:
        return await self.session.get(Target, target_id)

    async def update_target(self, target_id: int, target_in: TargetUpdate) -> Optional[Target]:
        db_target = await self.get_target(target_id)
        if not db_target:
            return None
        
        target_data = target_in.model_dump(exclude_unset=True)
        for key, value in target_data.items():
            setattr(db_target, key, value)
        
        self.session.add(db_target)
        await self.session.commit()
        await self.session.refresh(db_target)
        return db_target

    async def delete_target(self, target_id: int) -> bool:
        db_target = await self.get_target(target_id)
        if not db_target:
            return False
        
        await self.session.delete(db_target)
        await self.session.commit()
        return True

    async def get_targets(self, project_id: int, skip: int = 0, limit: int = 100) -> List[Target]:
        query = select(Target).where(Target.project_id == project_id).offset(skip).limit(limit)
        result = await self.session.exec(query)
        return result.all()
