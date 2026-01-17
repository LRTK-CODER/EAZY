"""HtmlResponseParser - HTML/CSS/JavaScript 응답 파서.

text/html, text/css, text/javascript, application/javascript
Content-Type을 처리하는 Strategy 패턴 구현체입니다.
"""

from typing import Optional

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData
from app.types.http import ParsedContent


class HtmlResponseParser:
    """HTML/CSS/JavaScript 텍스트 응답 파서.

    text/html, text/css, text/javascript, application/javascript
    Content-Type의 HTTP 응답을 파싱합니다.
    ResponseParser Protocol을 구조적으로 만족합니다.

    Example:
        >>> parser = HtmlResponseParser()
        >>> if parser.supports("text/html"):
        ...     result = await parser.parse(response)
    """

    # 지원하는 Content-Type 목록
    SUPPORTED_TYPES: frozenset[str] = frozenset(
        [
            "text/html",
            "text/css",
            "text/javascript",
            "application/javascript",
            "application/x-javascript",
        ]
    )

    def supports(self, content_type: str) -> bool:
        """텍스트 기반 Content-Type 지원 여부 확인.

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            지원하는 타입이면 True
        """
        # charset 제거 후 확인 (예: "text/html; charset=utf-8" -> "text/html")
        base_type = content_type.split(";")[0].strip().lower()
        return base_type in self.SUPPORTED_TYPES

    async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        """텍스트 응답 본문 파싱.

        Args:
            response: HTTP 응답 데이터

        Returns:
            ParsedContent 또는 None
        """
        original_size = len(response.body)

        # bytes를 문자열로 디코딩
        try:
            body_text = response.body.decode("utf-8")
        except UnicodeDecodeError:
            body_text = response.body.decode("utf-8", errors="replace")

        # 빈 body 처리
        if not body_text:
            return ParsedContent(
                content_type=response.content_type,
                body="",
                truncated=False,
                original_size=original_size,
            )

        # 크기 제한 확인 및 truncate
        truncated = False
        if len(body_text) > MAX_BODY_SIZE:
            body_text = body_text[:MAX_BODY_SIZE] + "... [TRUNCATED]"
            truncated = True

        return ParsedContent(
            content_type=response.content_type,
            body=body_text,
            truncated=truncated,
            original_size=original_size,
        )
