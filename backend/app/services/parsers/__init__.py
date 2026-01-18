"""HTTP 응답 파서 모듈.

Strategy 패턴을 사용하여 Content-Type별 파싱 로직을 분리합니다.

Example:
    >>> from app.services.parsers import ResponseParserRegistry, JsonResponseParser
    >>> registry = ResponseParserRegistry()
    >>> registry.register(JsonResponseParser())
    >>> parser = registry.get_parser("application/json")
    >>> result = await parser.parse(response_data)
"""

from .base import ResponseData, ResponseParser, ResponseParserRegistry
from .default_parser import DefaultResponseParser
from .html_parser import HtmlResponseParser
from .image_parser import ImageResponseParser
from .json_parser import JsonResponseParser

__all__ = [
    "ResponseParser",
    "ResponseParserRegistry",
    "DefaultResponseParser",
    "ResponseData",
    "JsonResponseParser",
    "HtmlResponseParser",
    "ImageResponseParser",
]
