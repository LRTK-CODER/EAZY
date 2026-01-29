"""CrawlStage - 웹 크롤링 Stage."""

import logging
import time
from typing import Any

from app.application.stages.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


class CrawlStage(PipelineStage):
    """웹 크롤링 Stage.

    ICrawler 포트를 통해 URL을 크롤링하고
    결과를 PipelineContext에 저장합니다.
    """

    def __init__(self, crawler: Any):
        """CrawlStage 초기화.

        Args:
            crawler: ICrawler 호환 크롤러 객체
        """
        self._crawler = crawler

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "crawl"

    async def process(self, context: Any) -> StageResult:
        """URL 크롤링 수행.

        Args:
            context: PipelineContext

        Returns:
            StageResult: 크롤링 결과
        """
        # 취소 확인
        if context.is_cancelled:
            return StageResult.stop("Task cancelled")

        url = context.crawl_url
        start_time = time.monotonic()

        try:
            crawl_data = await self._crawler.crawl(url)
            context.set_crawl_data(crawl_data)

            duration_ms = (time.monotonic() - start_time) * 1000
            logger.info(
                "Crawl completed: url=%s, links=%d, duration=%.1fms",
                url,
                len(crawl_data.links),
                duration_ms,
            )

            return StageResult.ok()

        except Exception as e:
            duration_ms = (time.monotonic() - start_time) * 1000
            logger.error(
                "Crawl failed: url=%s, error=%s, duration=%.1fms",
                url,
                str(e),
                duration_ms,
            )
            return StageResult.fail(f"Crawl failed: {e}")
