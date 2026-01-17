"""ImageResponseParser - 이미지 응답 파서.

image/* Content-Type을 처리하는 Strategy 패턴 구현체입니다.
바이너리 이미지 데이터를 Base64로 인코딩합니다.
"""

import base64
from typing import Optional

from app.core.constants import MAX_BODY_SIZE
from app.services.parsers.base import ResponseData
from app.types.http import ParsedContent


class ImageResponseParser:
    """이미지 응답 파서.

    image/* Content-Type의 HTTP 응답을 Base64로 인코딩합니다.
    ResponseParser Protocol을 구조적으로 만족합니다.

    Example:
        >>> parser = ImageResponseParser()
        >>> if parser.supports("image/png"):
        ...     result = await parser.parse(response)
    """

    # 지원하는 이미지 Content-Type 목록
    SUPPORTED_TYPES: frozenset[str] = frozenset(
        [
            "image/png",
            "image/jpeg",
            "image/gif",
            "image/webp",
            "image/svg+xml",
            "image/x-icon",
            "image/bmp",
            "image/tiff",
        ]
    )

    def supports(self, content_type: str) -> bool:
        """이미지 Content-Type 지원 여부 확인.

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            지원하는 이미지 타입이면 True
        """
        # charset 등 파라미터 제거 (예: "image/png; charset=..." -> "image/png")
        base_type = content_type.split(";")[0].strip().lower()
        return base_type in self.SUPPORTED_TYPES

    async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        """이미지 응답 본문을 Base64로 인코딩.

        Args:
            response: HTTP 응답 데이터

        Returns:
            ParsedContent (body는 raw Base64 문자열)
        """
        original_size = len(response.body)

        # 빈 body 처리
        if not response.body:
            return ParsedContent(
                content_type=response.content_type,
                body="",
                truncated=False,
                original_size=original_size,
            )

        # 바이너리 크기 기준 truncation (Base64 인코딩 전)
        truncated = original_size > MAX_BODY_SIZE
        body_data = response.body[:MAX_BODY_SIZE] if truncated else response.body

        # Base64 인코딩 (raw Base64, data URL 아님)
        body = base64.b64encode(body_data).decode("ascii")

        return ParsedContent(
            content_type=response.content_type,
            body=body,
            truncated=truncated,
            original_size=original_size,
        )
