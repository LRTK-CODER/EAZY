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

    async def update_target(
        self, target_id: int, target_in: TargetUpdate
    ) -> Optional[Target]:
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
        """
        Target 삭제 (DB CASCADE로 관련 데이터 자동 삭제)

        CASCADE 삭제 체인:
        - Target 삭제 시 자동으로 다음 데이터가 삭제됨:
          1. tasks (target_id FK) - Target과 연결된 모든 크롤링/스캔 작업
          2. assets (target_id FK) - Target에서 발견된 모든 공격 표면
          3. asset_discoveries (asset_id FK) - Asset 삭제 시 함께 삭제되는 발견 이력
          4. asset_discoveries (task_id FK) - Task 삭제 시 함께 삭제되는 발견 이력

        Args:
            target_id: 삭제할 Target의 ID

        Returns:
            bool: 삭제 성공 시 True, Target이 존재하지 않으면 False
        """
        db_target = await self.get_target(target_id)
        if not db_target:
            return False

        await self.session.delete(db_target)
        await self.session.commit()
        return True

    async def get_targets(
        self, project_id: int, skip: int = 0, limit: int = 100
    ) -> List[Target]:
        query = (
            select(Target)
            .where(Target.project_id == project_id)
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.exec(query)
        return result.all()
