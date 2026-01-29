"""AssetStage - 자산 저장 Stage."""

import logging
from typing import Any

from app.application.stages.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


class AssetStage(PipelineStage):
    """자산 저장 Stage.

    발견된 자산을 배치 저장합니다.
    IntegrityError 발생 시 개별 저장으로 fallback합니다.
    """

    def __init__(self, asset_repository: Any):
        """AssetStage 초기화.

        Args:
            asset_repository: IAssetRepository 호환 객체
        """
        self._repository = asset_repository

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "asset"

    async def process(self, context: Any) -> StageResult:
        """자산 저장 수행.

        Args:
            context: PipelineContext

        Returns:
            StageResult: 저장 결과
        """
        # 취소 확인
        if context.is_cancelled:
            return StageResult.stop("Task cancelled")

        assets = context.discovered_assets
        crawler_links = context.crawl_data.links if context.crawl_data else []

        # Skip only if both are empty
        if not assets and not crawler_links:
            logger.info("No assets to save")
            context.set_saved_count(0)
            return StageResult.ok()

        task_id = context.task.id

        try:
            # 배치 저장 시도 (crawler links + discovered assets)
            http_data = context.crawl_data.http_data if context.crawl_data else {}

            saved_count = await self._repository.save_batch(
                assets, task_id, crawler_links=crawler_links, http_data=http_data
            )
            context.set_saved_count(saved_count)
            logger.info("Assets saved: count=%d, task_id=%d", saved_count, task_id)
            return StageResult.ok()

        except Exception as batch_error:
            # IntegrityError면 개별 저장으로 fallback
            from sqlalchemy.exc import IntegrityError

            if isinstance(batch_error, IntegrityError):
                logger.warning(
                    "Batch save IntegrityError, falling back to individual saves: %s",
                    str(batch_error),
                )
                return await self._save_individually(context, assets, task_id)

            # 다른 에러는 실패
            logger.error("Asset save failed: error=%s", str(batch_error))
            return StageResult.fail(f"Asset save failed: {batch_error}")

    async def _save_individually(
        self, context: Any, assets: list[Any], task_id: int
    ) -> StageResult:
        """개별 자산 저장 (IntegrityError fallback).

        Args:
            context: PipelineContext
            assets: 저장할 자산 목록
            task_id: Task ID

        Returns:
            StageResult: 저장 결과
        """
        from app.models.asset import AssetSource, AssetType

        saved_count = 0

        # 1. Save crawler links individually
        if context.crawl_data:
            crawler_links = context.crawl_data.links
            http_data = context.crawl_data.http_data

            for link in crawler_links:
                try:
                    link_http_data = http_data.get(link, {})
                    request_data = link_http_data.get("request")
                    response_data = link_http_data.get("response")
                    parameters_data = link_http_data.get("parameters")
                    http_method = (
                        request_data.get("method", "GET") if request_data else "GET"
                    )

                    await self._repository.save_link(
                        target_id=context.target_id,
                        task_id=task_id,
                        url=link,
                        method=http_method,
                        type=AssetType.URL,
                        source=AssetSource.HTML,
                        request_spec=request_data,
                        response_spec=response_data,
                        parameters=parameters_data,
                    )
                    saved_count += 1
                except Exception as e:
                    logger.debug(
                        "Individual link save failed: link=%s, error=%s", link, str(e)
                    )

        # 2. Save discovered assets individually
        for asset in assets:
            try:
                result = await self._repository.save_individual(asset, task_id)
                if result:
                    saved_count += 1
            except Exception as e:
                logger.debug(
                    "Individual save failed: asset=%s, error=%s",
                    getattr(asset, "url", "?"),
                    str(e),
                )

        context.set_saved_count(saved_count)
        logger.info(
            "Individual save completed: saved=%d, task_id=%d", saved_count, task_id
        )
        return StageResult.ok()
