"""
HTTP Type Definitions - TypedDict for HTTP request/response data structures.

이 모듈은 크롤러와 Asset 서비스에서 사용하는 HTTP 데이터 구조를 정의합니다.
"""

from typing import TypedDict, Dict, Optional, Union, Any


class HttpRequestData(TypedDict):
    """
    HTTP 요청 데이터 구조.

    Attributes:
        method: HTTP 메서드 (GET, POST, PUT, PATCH, DELETE 등)
        headers: HTTP 요청 헤더 딕셔너리
        body: 요청 본문 (POST/PUT/PATCH 요청에서 사용, 없으면 None)
    """

    method: str
    headers: Dict[str, str]
    body: Optional[str]


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
