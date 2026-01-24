"""Network Capturer Module.

브라우저 네트워크 트래픽을 캡처하여 동적으로 로드되는 자산을 발견합니다:
- XHR/Fetch 요청 캡처
- CORS preflight 요청 분석
- GraphQL 쿼리/뮤테이션 추출
- WebSocket 연결 탐지
"""

import json
import re
from collections.abc import AsyncIterator
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set
from urllib.parse import parse_qs, urlparse

from app.services.discovery.base import BaseDiscoveryModule
from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile

# ============================================================================
# Data Classes
# ============================================================================


@dataclass
class CapturedRequest:
    """캡처된 요청 정보."""

    url: str
    method: str
    headers: Dict[str, str] = field(default_factory=dict)
    body: Optional[str] = None
    resource_type: str = ""
    is_xhr: bool = False
    is_fetch: bool = False
    is_api: bool = True


@dataclass
class CorsRequestAnalysis:
    """CORS 요청 분석 결과."""

    is_preflight: bool = False
    is_cors_request: bool = False
    origin: Optional[str] = None
    requested_method: Optional[str] = None
    requested_headers: List[str] = field(default_factory=list)


@dataclass
class CorsResponseAnalysis:
    """CORS 응답 분석 결과."""

    allowed_origin: Optional[str] = None
    allowed_methods: List[str] = field(default_factory=list)
    allowed_headers: List[str] = field(default_factory=list)
    is_wildcard: bool = False
    allow_credentials: bool = False
    exposed_headers: List[str] = field(default_factory=list)


@dataclass
class GraphQLResult:
    """GraphQL 탐지 결과."""

    is_graphql: bool = False
    is_graphql_endpoint: bool = False
    operation_type: Optional[str] = None  # query, mutation, subscription
    operation_name: Optional[str] = None
    query: str = ""
    has_variables: bool = False
    variables: Optional[Dict[str, Any]] = None
    is_introspection: bool = False
    introspection_type: Optional[str] = None  # __schema, __type


@dataclass
class WebSocketResult:
    """WebSocket 추적 결과."""

    url: str
    is_secure: bool = False
    path: str = ""
    query_params: Dict[str, str] = field(default_factory=dict)
    protocol: str = ""  # ws, wss
    subprotocol: Optional[str] = None


# Aliases for test compatibility
CorsRequestInfo = CorsRequestAnalysis
CorsResponseInfo = CorsResponseAnalysis
GraphQLInfo = GraphQLResult
WebSocketInfo = WebSocketResult


# ============================================================================
# RequestInterceptor
# ============================================================================


class RequestInterceptor:
    """네트워크 요청 인터셉터."""

    # API가 아닌 리소스 타입
    NON_API_TYPES = {"image", "stylesheet", "font", "media", "manifest"}

    def __init__(self) -> None:
        """Initialize RequestInterceptor."""
        self._requests: List[CapturedRequest] = []

    def capture(self, request: Any) -> Optional[CapturedRequest]:
        """요청 캡처.

        Args:
            request: Playwright Request 객체 또는 Mock

        Returns:
            CapturedRequest 또는 None (필터링된 경우)
        """
        try:
            url = request.url
            method = request.method
            headers = dict(request.headers) if request.headers else {}
            resource_type = getattr(request, "resource_type", "") or ""
            post_data = getattr(request, "post_data", None)

            # API 여부 판단
            is_api = resource_type not in self.NON_API_TYPES

            # XHR/Fetch 여부
            is_xhr = resource_type == "xhr"
            is_fetch = resource_type == "fetch"

            # 비 API 요청은 None 반환
            if not is_api:
                return None

            captured = CapturedRequest(
                url=url,
                method=method,
                headers=headers,
                body=post_data,
                resource_type=resource_type,
                is_xhr=is_xhr,
                is_fetch=is_fetch,
                is_api=is_api,
            )

            self._requests.append(captured)
            return captured

        except Exception:
            return None

    def get_requests(self) -> List[CapturedRequest]:
        """캡처된 요청 반환."""
        return self._requests.copy()

    def clear(self) -> None:
        """캡처된 데이터 초기화."""
        self._requests.clear()


# ============================================================================
# CorsAnalyzer
# ============================================================================


class CorsAnalyzer:
    """CORS 요청/응답 분석기."""

    def analyze_request(self, request: Any) -> CorsRequestAnalysis:
        """요청의 CORS 분석.

        Args:
            request: Playwright Request 객체 또는 Mock

        Returns:
            CorsRequestAnalysis 결과
        """
        result = CorsRequestAnalysis()

        headers = dict(request.headers) if request.headers else {}
        method = getattr(request, "method", "GET")

        # Origin 헤더 확인
        origin = headers.get("Origin") or headers.get("origin")
        if origin:
            result.origin = origin
            result.is_cors_request = True

        # OPTIONS + Origin = preflight
        if method == "OPTIONS" and origin:
            result.is_preflight = True

            # Access-Control-Request-Method 추출
            requested_method = headers.get(
                "Access-Control-Request-Method"
            ) or headers.get("access-control-request-method")
            if requested_method:
                result.requested_method = requested_method

            # Access-Control-Request-Headers 추출
            requested_headers = headers.get(
                "Access-Control-Request-Headers"
            ) or headers.get("access-control-request-headers")
            if requested_headers:
                result.requested_headers = [
                    h.strip() for h in requested_headers.split(",")
                ]

        return result

    def analyze_response(self, response: Any) -> CorsResponseAnalysis:
        """응답의 CORS 분석.

        Args:
            response: Playwright Response 객체 또는 Mock

        Returns:
            CorsResponseAnalysis 결과
        """
        result = CorsResponseAnalysis()

        headers = dict(response.headers) if response.headers else {}

        # Access-Control-Allow-Origin
        allowed_origin = headers.get("Access-Control-Allow-Origin") or headers.get(
            "access-control-allow-origin"
        )
        if allowed_origin:
            result.allowed_origin = allowed_origin
            result.is_wildcard = allowed_origin == "*"

        # Access-Control-Allow-Methods
        allowed_methods = headers.get("Access-Control-Allow-Methods") or headers.get(
            "access-control-allow-methods"
        )
        if allowed_methods:
            result.allowed_methods = [m.strip() for m in allowed_methods.split(",")]

        # Access-Control-Allow-Headers
        allowed_headers = headers.get("Access-Control-Allow-Headers") or headers.get(
            "access-control-allow-headers"
        )
        if allowed_headers:
            result.allowed_headers = [h.strip() for h in allowed_headers.split(",")]

        # Access-Control-Allow-Credentials
        allow_credentials = headers.get(
            "Access-Control-Allow-Credentials"
        ) or headers.get("access-control-allow-credentials")
        if allow_credentials and allow_credentials.lower() == "true":
            result.allow_credentials = True

        # Access-Control-Expose-Headers
        exposed_headers = headers.get("Access-Control-Expose-Headers") or headers.get(
            "access-control-expose-headers"
        )
        if exposed_headers:
            result.exposed_headers = [h.strip() for h in exposed_headers.split(",")]

        return result

    def is_overly_permissive(self, result: CorsResponseAnalysis) -> bool:
        """CORS 설정이 과도하게 허용적인지 확인.

        Args:
            result: CORS 응답 분석 결과

        Returns:
            True if overly permissive
        """
        return result.is_wildcard


# ============================================================================
# GraphQLDetector
# ============================================================================


class GraphQLDetector:
    """GraphQL 요청 탐지기."""

    # GraphQL 엔드포인트 패턴
    ENDPOINT_PATTERNS = [
        re.compile(r"/graphql/?$", re.IGNORECASE),
        re.compile(r"/gql/?$", re.IGNORECASE),
        re.compile(r"/api/graphql/?$", re.IGNORECASE),
        re.compile(r"/v\d+/graphql/?$", re.IGNORECASE),
    ]

    # Operation 타입 패턴
    OPERATION_PATTERN = re.compile(
        r"(query|mutation|subscription)\s+(\w+)?", re.IGNORECASE
    )

    # Introspection 패턴
    INTROSPECTION_SCHEMA = re.compile(r"__schema\s*\{")
    INTROSPECTION_TYPE = re.compile(r"__type\s*\(")

    def is_graphql_endpoint(self, url: str) -> bool:
        """GraphQL 엔드포인트 여부 확인.

        Args:
            url: URL 문자열

        Returns:
            True if GraphQL endpoint
        """
        for pattern in self.ENDPOINT_PATTERNS:
            if pattern.search(url):
                return True
        return False

    def detect(self, request: Any) -> GraphQLResult:
        """요청에서 GraphQL 탐지.

        Args:
            request: Playwright Request 객체 또는 Mock

        Returns:
            GraphQLResult
        """
        result = GraphQLResult()
        url = getattr(request, "url", "")
        post_data = getattr(request, "post_data", None)

        # 엔드포인트 확인
        result.is_graphql_endpoint = self.is_graphql_endpoint(url)

        if not post_data:
            return result

        try:
            body = json.loads(post_data)
        except (json.JSONDecodeError, TypeError):
            return result

        query = body.get("query", "")
        if not query:
            return result

        result.is_graphql = True
        result.query = query

        # Variables 추출
        variables = body.get("variables")
        if variables:
            result.has_variables = True
            result.variables = variables

        # Operation 타입 및 이름 추출
        match = self.OPERATION_PATTERN.search(query)
        if match:
            result.operation_type = match.group(1).lower()
            if match.group(2):
                result.operation_name = match.group(2)
        else:
            # 기본값: query
            result.operation_type = "query"

        # Introspection 탐지
        if self.INTROSPECTION_SCHEMA.search(query):
            result.is_introspection = True
            result.introspection_type = "__schema"
        elif self.INTROSPECTION_TYPE.search(query):
            result.is_introspection = True
            result.introspection_type = "__type"

        return result


# ============================================================================
# WebSocketTracker
# ============================================================================


class WebSocketTracker:
    """WebSocket 연결 추적기."""

    def __init__(self) -> None:
        """Initialize WebSocketTracker."""
        self._connections: List[WebSocketResult] = []

    def track(self, ws: Any) -> WebSocketResult:
        """WebSocket 연결 추적.

        Args:
            ws: Playwright WebSocket 객체 또는 Mock

        Returns:
            WebSocketResult
        """
        url = getattr(ws, "url", "")
        parsed = urlparse(url)

        # 프로토콜 (ws or wss)
        protocol = parsed.scheme  # ws or wss
        is_secure = protocol == "wss"

        # 경로
        path = parsed.path

        # 쿼리 파라미터
        query_params: Dict[str, str] = {}
        if parsed.query:
            qs = parse_qs(parsed.query)
            query_params = {k: v[0] if v else "" for k, v in qs.items()}

        # Subprotocol
        subprotocol = getattr(ws, "subprotocol", None)

        result = WebSocketResult(
            url=url,
            is_secure=is_secure,
            path=path,
            query_params=query_params,
            protocol=protocol,
            subprotocol=subprotocol,
        )

        self._connections.append(result)
        return result

    def get_connections(self) -> List[WebSocketResult]:
        """캡처된 WebSocket 연결 반환."""
        return self._connections.copy()

    def clear(self) -> None:
        """캡처된 데이터 초기화."""
        self._connections.clear()


# ============================================================================
# NetworkCapturerModule
# ============================================================================


class NetworkCapturerModule(BaseDiscoveryModule):
    """네트워크 트래픽 캡처 Discovery 모듈.

    브라우저 네트워크 트래픽을 캡처하여 동적으로 로드되는 자산을 발견합니다.
    STANDARD, FULL 프로필에서 활성화됩니다.
    """

    def __init__(self) -> None:
        """Initialize NetworkCapturerModule."""
        self._request_interceptor = RequestInterceptor()
        self._cors_analyzer = CorsAnalyzer()
        self._graphql_detector = GraphQLDetector()
        self._ws_tracker = WebSocketTracker()

    @property
    def name(self) -> str:
        """모듈 고유 이름."""
        return "network_capturer"

    @property
    def profiles(self) -> Set[ScanProfile]:
        """지원하는 스캔 프로필 집합."""
        return {ScanProfile.STANDARD, ScanProfile.FULL}

    async def discover(
        self, context: DiscoveryContext
    ) -> AsyncIterator[DiscoveredAsset]:
        """자산 발견 수행.

        Args:
            context: Discovery 실행 컨텍스트

        Yields:
            발견된 자산
        """
        # crawl_data에서 캡처된 네트워크 데이터 가져오기
        # 두 가지 형식 지원: network_data.requests 또는 직접 network_requests
        network_data = context.crawl_data.get("network_data", {})
        requests = network_data.get("requests", []) or context.crawl_data.get(
            "network_requests", []
        )
        responses = network_data.get("responses", []) or context.crawl_data.get(
            "network_responses", []
        )
        websockets = network_data.get("websockets", []) or context.crawl_data.get(
            "websockets", []
        )

        # 응답 URL -> 응답 매핑
        response_map: Dict[str, Dict[str, Any]] = {}
        for resp in responses:
            if isinstance(resp, dict):
                response_map[resp.get("url", "")] = resp

        # 중복 제거용 집합
        seen_urls: Set[str] = set()

        # 요청 처리
        for req_data in requests:
            if not isinstance(req_data, dict):
                continue

            url = req_data.get("url", "")
            method = req_data.get("method", "GET")
            headers = req_data.get("headers", {})
            body = req_data.get("body") or req_data.get("post_data")
            resource_type = req_data.get("resource_type", "")

            # XHR/Fetch 요청
            if resource_type in ("xhr", "fetch"):
                if url not in seen_urls:
                    seen_urls.add(url)
                    yield DiscoveredAsset(
                        url=url,
                        asset_type="api_endpoint",
                        source=self.name,
                        metadata={
                            "method": method,
                            "resource_type": resource_type,
                        },
                    )

            # CORS 분석 (Mock 객체 생성)
            class MockRequest:
                pass

            mock_req = MockRequest()
            mock_req.headers = headers  # type: ignore
            mock_req.method = method  # type: ignore

            cors_result = self._cors_analyzer.analyze_request(mock_req)
            if cors_result.is_preflight or cors_result.is_cors_request:
                cors_url = f"cors://{url}"
                if cors_url not in seen_urls:
                    seen_urls.add(cors_url)

                    # 응답에서 CORS 헤더 분석
                    resp_data = response_map.get(url)
                    cors_response = None
                    if resp_data:

                        class MockResponse:
                            pass

                        mock_resp = MockResponse()
                        mock_resp.headers = resp_data.get("headers", {})  # type: ignore
                        cors_response = self._cors_analyzer.analyze_response(mock_resp)

                    yield DiscoveredAsset(
                        url=url,
                        asset_type="cors_endpoint",
                        source=self.name,
                        metadata={
                            "is_preflight": cors_result.is_preflight,
                            "origin": cors_result.origin,
                            "allowed_origin": (
                                cors_response.allowed_origin if cors_response else None
                            ),
                            "is_overly_permissive": (
                                self._cors_analyzer.is_overly_permissive(cors_response)
                                if cors_response
                                else False
                            ),
                        },
                    )

            # GraphQL 탐지
            class MockGqlRequest:
                pass

            mock_gql = MockGqlRequest()
            mock_gql.url = url  # type: ignore
            mock_gql.post_data = body  # type: ignore

            graphql_result = self._graphql_detector.detect(mock_gql)
            if graphql_result.is_graphql:
                graphql_url = (
                    f"graphql://{url}#{graphql_result.operation_name or 'anonymous'}"
                )
                if graphql_url not in seen_urls:
                    seen_urls.add(graphql_url)
                    yield DiscoveredAsset(
                        url=url,
                        asset_type="graphql_endpoint",
                        source=self.name,
                        metadata={
                            "operation_type": graphql_result.operation_type,
                            "operation_name": graphql_result.operation_name,
                            "is_introspection": graphql_result.is_introspection,
                            "has_variables": graphql_result.has_variables,
                        },
                    )

        # CORS 응답 분석 (security_issues 포함)
        for resp_data in responses:
            if not isinstance(resp_data, dict):
                continue

            resp_url = resp_data.get("url", "")
            resp_headers = resp_data.get("headers", {})

            # CORS 헤더가 있는 경우만 분석
            if "Access-Control-Allow-Origin" not in resp_headers:
                continue

            cors_key = f"cors_config://{resp_url}"
            if cors_key in seen_urls:
                continue
            seen_urls.add(cors_key)

            # Mock response 생성
            class MockCorsResponse:
                pass

            mock_cors_resp = MockCorsResponse()
            mock_cors_resp.headers = resp_headers  # type: ignore

            cors_resp_result = self._cors_analyzer.analyze_response(mock_cors_resp)

            # Security issues 탐지
            security_issues: List[str] = []
            if cors_resp_result.is_wildcard and cors_resp_result.allow_credentials:
                security_issues.append("wildcard_with_credentials")

            yield DiscoveredAsset(
                url=resp_url,
                asset_type="cors_config",
                source=self.name,
                metadata={
                    "allowed_origin": cors_resp_result.allowed_origin,
                    "is_wildcard": cors_resp_result.is_wildcard,
                    "allow_credentials": cors_resp_result.allow_credentials,
                    "allowed_methods": cors_resp_result.allowed_methods,
                    "allowed_headers": cors_resp_result.allowed_headers,
                    "exposed_headers": cors_resp_result.exposed_headers,
                    "security_issues": security_issues,
                },
            )

        # WebSocket 연결 처리
        for ws_data in websockets:
            if not isinstance(ws_data, dict):
                continue

            ws_url = ws_data.get("url", "")
            if ws_url and ws_url not in seen_urls:
                seen_urls.add(ws_url)

                # Mock WebSocket
                class MockWs:
                    pass

                mock_ws = MockWs()
                mock_ws.url = ws_url  # type: ignore

                ws_result = self._ws_tracker.track(mock_ws)

                yield DiscoveredAsset(
                    url=ws_url,
                    asset_type="websocket_endpoint",
                    source=self.name,
                    metadata={
                        "is_secure": ws_result.is_secure,
                        "path": ws_result.path,
                        "query_params": ws_result.query_params,
                        "protocol": ws_result.protocol,
                        "subprotocol": ws_result.subprotocol,
                    },
                )
