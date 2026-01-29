"""DiscoveryStage - 자산 발견 Stage."""

import logging
from typing import Any

from app.application.stages.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


class DiscoveryStage(PipelineStage):
    """자산 발견 Stage.

    크롤링된 데이터에서 자산(API 엔드포인트, 폼 등)을 발견합니다.
    에러 발생 시에도 파이프라인을 계속 진행합니다 (can_continue_on_error=True).
    """

    def __init__(
        self,
        discovery_service: Any,
        data_transformer: Any,
    ):
        """DiscoveryStage 초기화.

        Args:
            discovery_service: DiscoveryService 호환 객체 (run() 메서드)
            data_transformer: DataTransformer 호환 객체
        """
        self._discovery = discovery_service
        self._transformer = data_transformer

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "discovery"

    @property
    def can_continue_on_error(self) -> bool:
        """에러 시에도 계속 진행."""
        return True

    async def process(self, context: Any) -> StageResult:
        """자산 발견 수행.

        Args:
            context: PipelineContext

        Returns:
            StageResult: 발견 결과
        """
        # 취소 확인
        if context.is_cancelled:
            return StageResult.stop("Task cancelled")

        # crawl_data 없으면 스킵
        if not context.crawl_data:
            logger.info("No crawl data available, skipping discovery")
            context.set_discovered_assets([])
            return StageResult.ok()

        try:
            # CrawlData → DiscoveryContext 변환
            discovery_context = self._transformer.to_discovery_context(
                target_url=context.crawl_url,
                http_data=context.crawl_data.http_data,
                http_client=None,  # Unit tests don't need real HTTP client
                js_contents=context.crawl_data.js_contents,
            )

            # Discovery 실행
            assets = await self._discovery.run(discovery_context)
            context.set_discovered_assets(assets)

            logger.info(
                "Discovery completed: url=%s, assets_found=%d",
                context.crawl_url,
                len(assets),
            )

            return StageResult.ok()

        except Exception as e:
            logger.warning(
                "Discovery error (continuing): url=%s, error=%s",
                context.crawl_url,
                str(e),
            )
            context.add_error(self.name, e)
            context.set_discovered_assets([])
            return StageResult.ok()  # can_continue_on_error=True
