"""HTTP 응답 파서 모듈.

Strategy 패턴을 사용하여 Content-Type별 파싱 로직을 분리합니다.

Example:
    >>> from app.services.parsers import ResponseParserRegistry, ResponseData
    >>> registry = ResponseParserRegistry()
    >>> parser = registry.get_parser("application/json")
    >>> result = await parser.parse(response_data)
"""
from .base import (
    DefaultResponseParser,
    ResponseData,
    ResponseParser,
    ResponseParserRegistry,
)

__all__ = [
    "ResponseParser",
    "ResponseParserRegistry",
    "DefaultResponseParser",
    "ResponseData",
]
