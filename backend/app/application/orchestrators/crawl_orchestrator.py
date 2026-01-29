"""CrawlOrchestrator - 파이프라인 조율자."""

import logging
import time
from typing import Any, List, Optional

from sqlmodel.ext.asyncio.session import AsyncSession

from app.application.context.pipeline_context import OrchestratorResult, PipelineContext

logger = logging.getLogger(__name__)


class CrawlOrchestrator:
    """파이프라인 조율자.

    Stage들을 순서대로 실행하며 에러 처리, 취소 확인,
    파이프라인 흐름 제어를 담당합니다.
    """

    def __init__(
        self,
        stages: List[Any],
        cancellation: Optional[Any] = None,
    ):
        """CrawlOrchestrator 초기화.

        Args:
            stages: 실행할 Stage 목록 (순서대로)
            cancellation: ICancellation 호환 객체 (선택)
        """
        self._stages = stages
        self._cancellation = cancellation

    async def execute(
        self,
        task: Any,
        target_id: int,
        session: Optional[AsyncSession] = None,
    ) -> OrchestratorResult:
        """파이프라인 실행.

        Args:
            task: Task 객체
            target_id: Target ID
            session: AsyncSession (선택) - LoadTargetStage 등에 전달할 수 있음

        Returns:
            OrchestratorResult: 실행 결과
        """
        context = PipelineContext(task=task, target_id=target_id)
        start_time = time.monotonic()

        logger.info(
            "Pipeline started: task_id=%s, target_id=%d, stages=%d",
            getattr(task, "id", "?"),
            target_id,
            len(self._stages),
        )

        for stage in self._stages:
            # Stage 실행
            try:
                result = await stage.process(context)

                if result.should_stop:
                    if not result.success:
                        # 실패로 인한 중단 - 에러 기록
                        context.add_error(
                            stage.name, Exception(result.error or "Stage failed")
                        )
                    logger.info(
                        "Pipeline stopped at stage '%s': reason=%s",
                        stage.name,
                        result.reason or result.error or "stop requested",
                    )
                    break

            except Exception as e:
                context.add_error(stage.name, e)

                if stage.can_continue_on_error:
                    logger.warning(
                        "Stage '%s' error (continuing): %s", stage.name, str(e)
                    )
                else:
                    logger.error("Stage '%s' error (stopping): %s", stage.name, str(e))
                    break

            # 취소 확인 (Stage 실행 후)
            if self._cancellation:
                task_id = getattr(task, "id", 0)
                if await self._cancellation.is_cancelled(task_id):
                    context.mark_cancelled()
                    logger.info("Pipeline cancelled: task_id=%s", task_id)
                    break

        duration_ms = (time.monotonic() - start_time) * 1000
        orchestrator_result = context.to_result()

        logger.info(
            "Pipeline completed: task_id=%s, success=%s, saved=%d, spawned=%d, errors=%d, duration=%.1fms",
            getattr(task, "id", "?"),
            orchestrator_result.success,
            orchestrator_result.saved_assets,
            orchestrator_result.child_tasks_spawned,
            len(orchestrator_result.errors),
            duration_ms,
        )

        return orchestrator_result
