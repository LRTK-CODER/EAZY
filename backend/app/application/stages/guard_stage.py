"""GuardStage - URL 보안 검증 Stage."""

import logging
from typing import Any

from app.application.stages.base import PipelineStage, StageResult

logger = logging.getLogger(__name__)


class GuardStage(PipelineStage):
    """보안 검증 Stage.

    SSRF 방지와 Scope 검증을 수행합니다.
    이 Stage를 통과하지 못하면 크롤링이 중단됩니다.
    """

    def __init__(
        self,
        url_validator: Any,
        scope_checker: Any,
    ):
        """GuardStage 초기화.

        Args:
            url_validator: URL 안전성 검증기 (UrlValidator 또는 호환 객체)
            scope_checker: Scope 검증기 (ScopeChecker 또는 호환 객체)
        """
        self._url_validator = url_validator
        self._scope_checker = scope_checker

    @property
    def name(self) -> str:
        """Stage 이름."""
        return "guard"

    async def process(self, context: Any) -> StageResult:
        """URL 보안 검증 수행.

        1. 취소 여부 확인
        2. URL 유효성 확인
        3. SSRF 검증 (UrlValidator)
        4. Scope 검증 (ScopeChecker)

        Args:
            context: PipelineContext

        Returns:
            StageResult: 검증 결과
        """
        url = context.crawl_url

        # 취소 확인
        if context.is_cancelled:
            return StageResult.stop("Task cancelled")

        # 빈 URL 확인
        if not url:
            return StageResult.stop("Empty URL")

        # SSRF 검증
        if not self._url_validator.is_safe(url):
            logger.warning("Blocked unsafe URL: %s", url)
            return StageResult.stop(f"Unsafe URL blocked: {url}")

        # Scope 검증
        if not self._scope_checker.is_in_scope(url, context.target):
            logger.info("URL out of scope: %s", url)
            return StageResult.stop(f"URL out of scope: {url}")

        return StageResult.ok()
