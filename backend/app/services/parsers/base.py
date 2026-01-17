"""ResponseParser Protocol 및 Registry 정의.

HTTP 응답 파싱을 위한 Strategy 패턴 인터페이스를 제공합니다.
Phase 3에서 구체적인 파서 구현(Json, Html, Image, Default)이 추가됩니다.
"""
from dataclasses import dataclass
from typing import Dict, List, Optional, Protocol

from app.types.http import ParsedContent


@dataclass(frozen=True)
class ResponseData:
    """HTTP 응답 데이터 추상화.

    Playwright Response 객체 대신 사용하여 테스트 용이성을 높입니다.
    frozen=True로 불변성을 보장합니다.

    Attributes:
        url: 요청 URL
        status: HTTP 상태 코드
        content_type: Content-Type 헤더 값
        headers: HTTP 응답 헤더
        body: 응답 본문 (바이트)

    Example:
        >>> data = ResponseData(
        ...     url="http://example.com",
        ...     status=200,
        ...     content_type="application/json",
        ...     headers={"Content-Type": "application/json"},
        ...     body=b'{"key": "value"}'
        ... )
    """

    url: str
    status: int
    content_type: str
    headers: Dict[str, str]
    body: bytes


class ResponseParser(Protocol):
    """HTTP 응답 파서 인터페이스.

    Strategy 패턴을 사용하여 Content-Type별 파싱 로직을 캡슐화합니다.
    구현체는 이 Protocol을 구조적으로 만족하면 됩니다.

    Example:
        >>> class JsonResponseParser:
        ...     def supports(self, content_type: str) -> bool:
        ...         return "application/json" in content_type
        ...
        ...     async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        ...         import json
        ...         data = json.loads(response.body)
        ...         return {"content_type": response.content_type, "body": json.dumps(data), "truncated": False, "original_size": len(response.body)}
    """

    def supports(self, content_type: str) -> bool:
        """주어진 Content-Type을 처리할 수 있는지 확인.

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            처리 가능하면 True, 아니면 False
        """
        ...

    async def parse(self, response: ResponseData) -> Optional[ParsedContent]:
        """응답 본문을 파싱하여 구조화된 데이터로 변환.

        Args:
            response: HTTP 응답 데이터

        Returns:
            ParsedContent 또는 None (파싱 불가 시)
        """
        ...


class ResponseParserRegistry:
    """파서 레지스트리 - Content-Type에 맞는 파서를 찾아 반환.

    Strategy 패턴의 Context 역할을 합니다.
    등록된 파서 중 supports()가 True를 반환하는 첫 번째 파서를 선택합니다.

    Example:
        >>> registry = ResponseParserRegistry()
        >>> registry.register(JsonResponseParser())
        >>> registry.register(HtmlResponseParser())
        >>> parser = registry.get_parser("application/json")
        >>> result = await parser.parse(response)
    """

    def __init__(self) -> None:
        """레지스트리 초기화."""
        # Lazy import to avoid circular dependency
        from app.services.parsers.default_parser import DefaultResponseParser

        self._parsers: List[ResponseParser] = []
        self._default: ResponseParser = DefaultResponseParser()

    def register(self, parser: ResponseParser) -> None:
        """파서를 레지스트리에 등록.

        파서는 등록 순서대로 검색됩니다.
        먼저 등록된 파서가 우선순위가 높습니다.

        Args:
            parser: 등록할 파서 인스턴스
        """
        self._parsers.append(parser)

    def get_parser(self, content_type: str) -> ResponseParser:
        """Content-Type에 맞는 파서 반환.

        등록된 파서를 순회하면서 supports()가 True를 반환하는
        첫 번째 파서를 선택합니다.

        Args:
            content_type: HTTP Content-Type 헤더 값

        Returns:
            적합한 파서. 없으면 DefaultResponseParser 반환.
        """
        for parser in self._parsers:
            if parser.supports(content_type):
                return parser
        return self._default
