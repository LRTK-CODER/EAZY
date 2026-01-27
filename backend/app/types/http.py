"""
HTTP Type Definitions - TypedDict for HTTP request/response data structures.

이 모듈은 크롤러와 Asset 서비스에서 사용하는 HTTP 데이터 구조를 정의합니다.
"""

from typing import Any, Dict, Optional, TypedDict, Union


class HttpRequestData(TypedDict, total=False):
    """
    HTTP 요청 데이터 구조.

    Attributes:
        method: HTTP 메서드 (GET, POST, PUT, PATCH, DELETE 등)
        headers: HTTP 요청 헤더 딕셔너리
        body: 요청 본문 (POST/PUT/PATCH 요청에서 사용, 없으면 None)
        resource_type: Playwright resource_type (document, xhr, fetch, script 등)
    """

    method: str
    headers: Dict[str, str]
    body: Optional[str]
    resource_type: str


class HttpResponseData(TypedDict):
    """
    HTTP 응답 데이터 구조.

    Attributes:
        status: HTTP 상태 코드 (200, 404, 500 등)
        headers: HTTP 응답 헤더 딕셔너리
        body: 응답 본문 (텍스트, JSON 파싱된 dict, 또는 base64 인코딩된 바이너리)
    """

    status: int
    headers: Dict[str, str]
    body: Optional[Union[str, Dict[str, Any]]]


class HttpData(TypedDict, total=False):
    """
    URL별 HTTP 데이터 컨테이너.

    total=False로 설정하여 부분적인 키만 가질 수 있습니다.
    예: request만 있거나, response만 있거나, parameters만 있는 경우.

    Attributes:
        request: HTTP 요청 데이터
        response: HTTP 응답 데이터
        parameters: URL/폼 파라미터 (파싱된 쿼리스트링 등)
    """

    request: HttpRequestData
    response: HttpResponseData
    parameters: Optional[Dict[str, Any]]


class ParsedContent(TypedDict):
    """HTTP 응답 파싱 결과.

    ResponseParser가 반환하는 파싱된 콘텐츠 구조입니다.

    Attributes:
        content_type: 원본 응답의 Content-Type
        body: 파싱된 본문 (텍스트, JSON 문자열, base64 등) 또는 None
        truncated: 본문이 크기 제한으로 잘렸는지 여부
        original_size: 원본 본문의 바이트 크기
    """

    content_type: str
    body: Optional[str]
    truncated: bool
    original_size: int


class JsContent(TypedDict, total=False):
    """JavaScript 파일 content 구조.

    CrawlerService에서 수집한 JavaScript 파일의 content를 저장합니다.
    외부 .js 파일과 인라인 <script> 태그 모두 포함됩니다.

    Attributes:
        url: JavaScript 파일의 URL (인라인: {source_url}#inline-{index})
        content: JavaScript 코드 내용
        content_type: HTTP Content-Type 헤더 값 (인라인: text/javascript)
        is_inline: 인라인 스크립트 여부 (True: <script> 태그, False: 외부 파일)
        source_url: 인라인 스크립트의 부모 페이지 URL (외부 파일은 없음)
    """

    url: str
    content: str
    content_type: str
    is_inline: bool
    source_url: str
