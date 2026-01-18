"""DefaultResponseParser - 알 수 없는 Content-Type 처리.

모든 Content-Type에 대해 메타데이터만 반환하는 fallback 파서입니다.
Registry에서 적합한 파서를 찾지 못했을 때 사용됩니다.
"""

import logging
from typing import Optional

from app.services.parsers.base import ResponseData
from app.types.http import ParsedContent

logger = logging.getLogger(__name__)


class DefaultResponseParser:
    """기본 파서 - 모든 Content-Type에 대해 메타데이터만 반환.

    알 수 없는 Content-Type에 대한 fallback으로 사용됩니다.
    body는 None으로, content_type과 original_size는 보존합니다.

    Example:
        >>> parser = DefaultResponseParser()
        >>> parser.supports("application/octet-stream")
        True
        >>> result = await parser.parse(response)
        >>> result["body"] is None
        True
    """

    def supports(self, content_type: str) -> bool:
        """모든 Content-Type 지원 (fallback).

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            항상 True
        """
        return True

    async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        """메타데이터만 포함한 ParsedContent 반환.

        실제 body 파싱은 수행하지 않고, content_type과 original_size만
        보존하여 반환합니다. 알 수 없는 Content-Type 처리 시 INFO 레벨로 로깅합니다.

        Args:
            response: HTTP 응답 데이터

        Returns:
            ParsedContent with body=None
        """
        logger.info(
            "Unhandled content-type '%s' for URL: %s - returning metadata only",
            response.content_type,
            response.url,
        )
        return {
            "content_type": response.content_type,
            "body": None,
            "truncated": False,
            "original_size": len(response.body),
        }
