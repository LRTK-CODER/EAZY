"""LoadTargetStage - Target 로딩 Stage."""

import logging
from typing import Any

from sqlmodel.ext.asyncio.session import AsyncSession

from app.application.stages.base import PipelineStage, StageResult
from app.models.target import Target

logger = logging.getLogger(__name__)


class LoadTargetStage(PipelineStage):
    """Target 로딩 Stage.

    DB에서 Target을 로드하여 PipelineContext에 설정합니다.
    Target을 찾지 못하면 파이프라인이 실패합니다.
    """

    def __init__(self, session: AsyncSession):
        """LoadTargetStage 초기화.

        Args:
            session: AsyncSession 인스턴스
        """
        self._session = session

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "load_target"

    async def process(self, context: Any) -> StageResult:
        """Target 로딩 수행.

        1. context.target_id를 사용하여 DB에서 Target 조회
        2. Target을 찾지 못하면 실패
        3. Target을 context에 설정하여 후속 Stage에서 사용 가능하게 함

        Args:
            context: PipelineContext

        Returns:
            StageResult: 로딩 결과
        """
        target_id = context.target_id

        # DB에서 Target 로드
        logger.debug("Loading target: target_id=%d", target_id)
        target = await self._session.get(Target, target_id)

        if not target:
            logger.error("Target not found: target_id=%d", target_id)
            return StageResult.fail(f"Target not found: {target_id}")

        # Context에 Target 설정
        context.set_target(target)
        logger.info(
            "Target loaded successfully: target_id=%d, url=%s", target_id, target.url
        )

        return StageResult.ok()
