"""JsonResponseParser - JSON 응답 파서.

application/json Content-Type을 처리하는 Strategy 패턴 구현체입니다.
"""

import json
from typing import Optional

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData
from app.types.http import ParsedContent


class JsonResponseParser:
    """JSON 응답 파서.

    application/json Content-Type의 HTTP 응답을 파싱합니다.
    ResponseParser Protocol을 구조적으로 만족합니다.

    Example:
        >>> parser = JsonResponseParser()
        >>> if parser.supports("application/json"):
        ...     result = await parser.parse(response)
    """

    def supports(self, content_type: str) -> bool:
        """application/json Content-Type 지원 여부 확인.

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            "application/json"이 포함되어 있으면 True
        """
        return "application/json" in content_type

    async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        """JSON 응답 본문 파싱.

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

        # JSON 파싱 시도
        if not truncated:
            try:
                parsed = json.loads(body_text)
                # 파싱 성공 시 json.dumps로 정규화된 문자열 반환
                body_text = json.dumps(parsed, ensure_ascii=False)
            except json.JSONDecodeError:
                # 파싱 실패 시 원본 텍스트 그대로 반환
                pass

        return ParsedContent(
            content_type=response.content_type,
            body=body_text,
            truncated=truncated,
            original_size=original_size,
        )
