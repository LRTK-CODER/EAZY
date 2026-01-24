"""NetworkCapturerModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- XHR/Fetch 요청 캡처
- CORS preflight/allowed origins 분석
- GraphQL 엔드포인트 탐지
- WebSocket 연결 추적
"""

from typing import Dict
from unittest.mock import AsyncMock, MagicMock, PropertyMock

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.network_capturer import (
    CorsAnalyzer,
    GraphQLDetector,
    NetworkCapturerModule,
    RequestInterceptor,
    WebSocketTracker,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    client = MagicMock()
    client.get = AsyncMock()
    return client


@pytest.fixture
def discovery_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Create a test discovery context."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.STANDARD,
        http_client=mock_http_client,
    )


@pytest.fixture
def network_capturer_module() -> NetworkCapturerModule:
    """Create NetworkCapturerModule instance."""
    return NetworkCapturerModule()


@pytest.fixture
def request_interceptor() -> RequestInterceptor:
    """Create RequestInterceptor instance."""
    return RequestInterceptor()


@pytest.fixture
def cors_analyzer() -> CorsAnalyzer:
    """Create CorsAnalyzer instance."""
    return CorsAnalyzer()


@pytest.fixture
def graphql_detector() -> GraphQLDetector:
    """Create GraphQLDetector instance."""
    return GraphQLDetector()


@pytest.fixture
def websocket_tracker() -> WebSocketTracker:
    """Create WebSocketTracker instance."""
    return WebSocketTracker()


def create_mock_request(
    url: str,
    method: str = "GET",
    headers: Dict[str, str] | None = None,
    resource_type: str = "xhr",
    post_data: str | None = None,
) -> MagicMock:
    """Create a mock Playwright Request object."""
    mock_request = MagicMock()
    mock_request.url = url
    mock_request.method = method
    mock_request.headers = headers or {}
    mock_request.resource_type = resource_type
    mock_request.post_data = post_data
    return mock_request


def create_mock_response(
    url: str,
    status: int = 200,
    headers: Dict[str, str] | None = None,
) -> MagicMock:
    """Create a mock Playwright Response object."""
    mock_response = MagicMock()
    mock_response.url = url
    mock_response.status = status
    mock_response.headers = headers or {}
    mock_request = MagicMock()
    mock_request.url = url
    mock_request.method = "GET"
    mock_response.request = mock_request
    return mock_response


def create_mock_websocket(
    url: str,
) -> MagicMock:
    """Create a mock Playwright WebSocket object."""
    mock_ws = MagicMock()
    mock_ws.url = url
    mock_ws.is_closed.return_value = False
    return mock_ws


# ============================================================================
# Test 1: XHR Request Capture
# ============================================================================


class TestXhrRequestCapture:
    """XHR 요청 캡처 테스트."""

    def test_xhr_request_capture(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """XHR 요청 URL, method, headers 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/users",
            method="GET",
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer token123",
            },
            resource_type="xhr",
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert result.url == "https://api.example.com/users"
        assert result.method == "GET"
        assert result.headers["Accept"] == "application/json"
        assert result.is_xhr is True

    def test_xhr_post_request_capture(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """XHR POST 요청 및 body 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/users",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="xhr",
            post_data='{"name": "John", "email": "john@example.com"}',
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert result.method == "POST"
        assert result.body is not None
        assert "John" in result.body

    def test_xhr_put_request_capture(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """XHR PUT 요청 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/users/1",
            method="PUT",
            headers={"Content-Type": "application/json"},
            resource_type="xhr",
            post_data='{"name": "Updated"}',
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert result.method == "PUT"
        assert result.url == "https://api.example.com/users/1"

    def test_non_api_request_filtering(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """비 API 요청 (이미지, 스타일시트 등) 필터링."""
        mock_request = create_mock_request(
            url="https://example.com/image.png",
            method="GET",
            resource_type="image",
        )

        result = request_interceptor.capture(mock_request)

        # Image requests should be filtered out or marked as non-API
        assert result is None or result.is_api is False


# ============================================================================
# Test 2: Fetch Request Capture
# ============================================================================


class TestFetchRequestCapture:
    """Fetch 요청 캡처 테스트."""

    def test_fetch_request_capture(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """fetch() 호출 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/data",
            method="GET",
            headers={"Accept": "application/json"},
            resource_type="fetch",
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert result.url == "https://api.example.com/data"
        assert result.is_fetch is True

    def test_fetch_post_with_json_body(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """fetch() POST 요청 JSON body 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/submit",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"action": "submit", "data": [1, 2, 3]}',
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert result.method == "POST"
        assert result.body is not None
        assert "action" in result.body

    def test_fetch_with_custom_headers(
        self,
        request_interceptor: RequestInterceptor,
    ) -> None:
        """fetch() 커스텀 헤더 캡처."""
        mock_request = create_mock_request(
            url="https://api.example.com/secure",
            method="GET",
            headers={
                "X-API-Key": "secret-key-123",
                "X-Request-ID": "uuid-value",
            },
            resource_type="fetch",
        )

        result = request_interceptor.capture(mock_request)

        assert result is not None
        assert "X-API-Key" in result.headers
        assert result.headers["X-API-Key"] == "secret-key-123"


# ============================================================================
# Test 3: CORS Preflight Detection
# ============================================================================


class TestCorsPreflightDetection:
    """CORS preflight 탐지 테스트."""

    def test_cors_preflight_detection(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """OPTIONS 요청 (preflight) 탐지."""
        mock_request = create_mock_request(
            url="https://api.example.com/users",
            method="OPTIONS",
            headers={
                "Origin": "https://app.example.com",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type, Authorization",
            },
            resource_type="xhr",
        )

        result = cors_analyzer.analyze_request(mock_request)

        assert result.is_preflight is True
        assert result.origin == "https://app.example.com"
        assert result.requested_method == "POST"
        assert "Content-Type" in result.requested_headers
        assert "Authorization" in result.requested_headers

    def test_non_preflight_options_request(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """일반 OPTIONS 요청 (preflight가 아닌 경우) 처리."""
        mock_request = create_mock_request(
            url="https://api.example.com/users",
            method="OPTIONS",
            headers={},  # No CORS headers
            resource_type="xhr",
        )

        result = cors_analyzer.analyze_request(mock_request)

        # Without Origin header, it's not a CORS preflight
        assert result.is_preflight is False

    def test_simple_request_with_origin(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """Origin 헤더가 있는 단순 요청 처리."""
        mock_request = create_mock_request(
            url="https://api.example.com/data",
            method="GET",
            headers={
                "Origin": "https://app.example.com",
            },
            resource_type="fetch",
        )

        result = cors_analyzer.analyze_request(mock_request)

        assert result.is_preflight is False
        assert result.is_cors_request is True
        assert result.origin == "https://app.example.com"


# ============================================================================
# Test 4: CORS Allowed Origins
# ============================================================================


class TestCorsAllowedOrigins:
    """CORS 허용 origin 추출 테스트."""

    def test_cors_allowed_origins(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """Access-Control-Allow-Origin 추출."""
        mock_response = create_mock_response(
            url="https://api.example.com/users",
            status=200,
            headers={
                "Access-Control-Allow-Origin": "https://app.example.com",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
                "Access-Control-Allow-Headers": "Content-Type, Authorization",
            },
        )

        result = cors_analyzer.analyze_response(mock_response)

        assert result.allowed_origin == "https://app.example.com"
        assert "GET" in result.allowed_methods
        assert "POST" in result.allowed_methods
        assert "Content-Type" in result.allowed_headers

    def test_cors_wildcard_origin(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """와일드카드 origin (*) 탐지."""
        mock_response = create_mock_response(
            url="https://api.example.com/public",
            status=200,
            headers={
                "Access-Control-Allow-Origin": "*",
            },
        )

        result = cors_analyzer.analyze_response(mock_response)

        assert result.allowed_origin == "*"
        assert result.is_wildcard is True

    def test_cors_allow_credentials(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """Access-Control-Allow-Credentials 탐지."""
        mock_response = create_mock_response(
            url="https://api.example.com/secure",
            status=200,
            headers={
                "Access-Control-Allow-Origin": "https://app.example.com",
                "Access-Control-Allow-Credentials": "true",
            },
        )

        result = cors_analyzer.analyze_response(mock_response)

        assert result.allow_credentials is True

    def test_cors_expose_headers(
        self,
        cors_analyzer: CorsAnalyzer,
    ) -> None:
        """Access-Control-Expose-Headers 추출."""
        mock_response = create_mock_response(
            url="https://api.example.com/data",
            status=200,
            headers={
                "Access-Control-Allow-Origin": "https://app.example.com",
                "Access-Control-Expose-Headers": "X-Custom-Header, X-Request-Id",
            },
        )

        result = cors_analyzer.analyze_response(mock_response)

        assert "X-Custom-Header" in result.exposed_headers
        assert "X-Request-Id" in result.exposed_headers


# ============================================================================
# Test 5: GraphQL Query Extraction
# ============================================================================


class TestGraphQLQueryExtraction:
    """GraphQL query 추출 테스트."""

    def test_graphql_query_extraction(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL query 추출."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "query GetUsers { users { id name email } }"}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.operation_type == "query"
        assert result.operation_name == "GetUsers"
        assert "users" in result.query

    def test_graphql_query_with_variables(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL query with variables 추출."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "query GetUser($id: ID!) { user(id: $id) { name } }", "variables": {"id": "123"}}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.has_variables is True
        assert result.variables is not None
        assert result.variables.get("id") == "123"

    def test_graphql_endpoint_detection(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL 엔드포인트 패턴 탐지."""
        endpoints = [
            "https://api.example.com/graphql",
            "https://api.example.com/api/graphql",
            "https://api.example.com/v1/graphql",
            "https://api.example.com/gql",
        ]

        for endpoint in endpoints:
            mock_request = create_mock_request(
                url=endpoint,
                method="POST",
                headers={"Content-Type": "application/json"},
                resource_type="fetch",
                post_data='{"query": "{ __typename }"}',
            )

            result = graphql_detector.detect(mock_request)
            assert result.is_graphql_endpoint is True, f"Failed for {endpoint}"


# ============================================================================
# Test 6: GraphQL Mutation Extraction
# ============================================================================


class TestGraphQLMutationExtraction:
    """GraphQL mutation 추출 테스트."""

    def test_graphql_mutation_extraction(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL mutation 추출."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "mutation CreateUser { createUser(name: \\"John\\") { id } }"}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.operation_type == "mutation"
        assert result.operation_name == "CreateUser"

    def test_graphql_mutation_with_input(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL mutation with input object 추출."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "mutation UpdateUser($input: UpdateUserInput!) { updateUser(input: $input) { id name } }", "variables": {"input": {"id": "1", "name": "Jane"}}}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.operation_type == "mutation"
        assert result.has_variables is True

    def test_graphql_subscription_detection(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """GraphQL subscription 탐지."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "subscription OnMessage { messageAdded { id content } }"}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.operation_type == "subscription"


# ============================================================================
# Test 7: GraphQL Introspection
# ============================================================================


class TestGraphQLIntrospection:
    """GraphQL introspection 탐지 테스트."""

    def test_graphql_introspection_schema(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """__schema 쿼리 탐지."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "{ __schema { types { name } } }"}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.is_introspection is True
        assert result.introspection_type == "__schema"

    def test_graphql_introspection_type(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """__type 쿼리 탐지."""
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data='{"query": "{ __type(name: \\"User\\") { name fields { name } } }"}',
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.is_introspection is True
        assert result.introspection_type == "__type"

    def test_graphql_full_introspection_query(
        self,
        graphql_detector: GraphQLDetector,
    ) -> None:
        """전체 introspection 쿼리 탐지."""
        import json

        introspection_query = (
            "query IntrospectionQuery { "
            "__schema { queryType { name } mutationType { name } types { name kind } } "
            "}"
        )
        mock_request = create_mock_request(
            url="https://api.example.com/graphql",
            method="POST",
            headers={"Content-Type": "application/json"},
            resource_type="fetch",
            post_data=json.dumps({"query": introspection_query}),
        )

        result = graphql_detector.detect(mock_request)

        assert result.is_graphql is True
        assert result.is_introspection is True


# ============================================================================
# Test 8: WebSocket URL Capture
# ============================================================================


class TestWebSocketUrlCapture:
    """WebSocket 연결 URL 캡처 테스트."""

    def test_websocket_url_capture(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """WebSocket 연결 URL 캡처."""
        mock_ws = create_mock_websocket("wss://ws.example.com/socket")

        result = websocket_tracker.track(mock_ws)

        assert result.url == "wss://ws.example.com/socket"
        assert result.is_secure is True

    def test_websocket_with_path(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """WebSocket URL 경로 캡처."""
        mock_ws = create_mock_websocket("wss://ws.example.com/chat/room/123")

        result = websocket_tracker.track(mock_ws)

        assert result.url == "wss://ws.example.com/chat/room/123"
        assert "/chat/room/123" in result.path

    def test_websocket_with_query_params(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """WebSocket URL 쿼리 파라미터 캡처."""
        mock_ws = create_mock_websocket(
            "wss://ws.example.com/socket?token=abc123&room=general"
        )

        result = websocket_tracker.track(mock_ws)

        assert "token" in result.query_params
        assert result.query_params["token"] == "abc123"
        assert result.query_params["room"] == "general"


# ============================================================================
# Test 9: WebSocket Protocol Detection
# ============================================================================


class TestWebSocketProtocolDetection:
    """WebSocket 프로토콜 탐지 테스트."""

    def test_websocket_wss_protocol(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """wss:// 프로토콜 탐지."""
        mock_ws = create_mock_websocket("wss://ws.example.com/secure")

        result = websocket_tracker.track(mock_ws)

        assert result.protocol == "wss"
        assert result.is_secure is True

    def test_websocket_ws_protocol(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """ws:// 프로토콜 탐지."""
        mock_ws = create_mock_websocket("ws://ws.example.com/insecure")

        result = websocket_tracker.track(mock_ws)

        assert result.protocol == "ws"
        assert result.is_secure is False

    def test_websocket_subprotocol_detection(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """WebSocket subprotocol 탐지."""
        mock_ws = create_mock_websocket("wss://ws.example.com/graphql")
        # Simulate subprotocol negotiation
        type(mock_ws).subprotocol = PropertyMock(return_value="graphql-ws")

        result = websocket_tracker.track(mock_ws)

        assert result.subprotocol == "graphql-ws"

    def test_websocket_common_subprotocols(
        self,
        websocket_tracker: WebSocketTracker,
    ) -> None:
        """공통 WebSocket subprotocol 탐지."""
        subprotocols = ["graphql-ws", "graphql-transport-ws", "stomp", "mqtt"]

        for subprotocol in subprotocols:
            mock_ws = create_mock_websocket("wss://ws.example.com/socket")
            type(mock_ws).subprotocol = PropertyMock(return_value=subprotocol)

            result = websocket_tracker.track(mock_ws)
            assert (
                result.subprotocol == subprotocol
            ), f"Failed for subprotocol {subprotocol}"


# ============================================================================
# Integration Tests
# ============================================================================


class TestNetworkCapturerModuleIntegration:
    """NetworkCapturerModule 통합 테스트."""

    def test_module_properties(
        self,
        network_capturer_module: NetworkCapturerModule,
    ) -> None:
        """모듈 속성 테스트."""
        assert network_capturer_module.name == "network_capturer"
        assert ScanProfile.STANDARD in network_capturer_module.profiles
        assert ScanProfile.FULL in network_capturer_module.profiles
        # QUICK profile should not include network capturer (too heavy)
        assert ScanProfile.QUICK not in network_capturer_module.profiles

    async def test_discover_with_network_data(
        self,
        network_capturer_module: NetworkCapturerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """crawl_data에서 네트워크 요청 분석."""
        import json

        crawl_data = {
            "network_requests": [
                {
                    "url": "https://api.example.com/users",
                    "method": "GET",
                    "headers": {"Accept": "application/json"},
                    "resource_type": "xhr",
                },
                {
                    "url": "https://api.example.com/graphql",
                    "method": "POST",
                    "headers": {"Content-Type": "application/json"},
                    "resource_type": "fetch",
                    "post_data": json.dumps({"query": "{ users { id } }"}),
                },
            ],
            "network_responses": [
                {
                    "url": "https://api.example.com/users",
                    "status": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                    },
                },
            ],
            "websockets": [
                {
                    "url": "wss://ws.example.com/live",
                },
            ],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in network_capturer_module.discover(context)]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

        # Should have discovered API endpoints
        api_assets = [a for a in assets if a.asset_type == "api_endpoint"]
        assert len(api_assets) > 0

        # Should have discovered GraphQL endpoint
        graphql_assets = [a for a in assets if a.asset_type == "graphql_endpoint"]
        assert len(graphql_assets) > 0

        # Should have discovered WebSocket
        ws_assets = [a for a in assets if a.asset_type == "websocket_endpoint"]
        assert len(ws_assets) > 0

    async def test_discover_cors_misconfiguration(
        self,
        network_capturer_module: NetworkCapturerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """CORS 잘못된 설정 탐지."""
        crawl_data = {
            "network_requests": [
                {
                    "url": "https://api.example.com/sensitive",
                    "method": "OPTIONS",
                    "headers": {
                        "Origin": "https://evil.com",
                        "Access-Control-Request-Method": "POST",
                    },
                    "resource_type": "xhr",
                },
            ],
            "network_responses": [
                {
                    "url": "https://api.example.com/sensitive",
                    "status": 200,
                    "headers": {
                        "Access-Control-Allow-Origin": "*",
                        "Access-Control-Allow-Credentials": "true",
                    },
                },
            ],
            "websockets": [],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in network_capturer_module.discover(context)]

        # Should detect CORS endpoint
        cors_assets = [a for a in assets if a.asset_type == "cors_endpoint"]
        assert len(cors_assets) > 0

        # Check metadata for permissive CORS
        cors_asset = cors_assets[0]
        assert cors_asset.metadata.get("is_preflight") is True
        assert cors_asset.metadata.get("is_overly_permissive") is True

    async def test_discover_with_empty_data(
        self,
        network_capturer_module: NetworkCapturerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 데이터 처리."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [asset async for asset in network_capturer_module.discover(context)]

        # Should handle empty data gracefully
        assert isinstance(assets, list)

    async def test_duplicate_request_filtering(
        self,
        network_capturer_module: NetworkCapturerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """중복 요청 필터링."""
        crawl_data = {
            "network_requests": [
                {
                    "url": "https://api.example.com/users",
                    "method": "GET",
                    "headers": {},
                    "resource_type": "xhr",
                },
                {
                    "url": "https://api.example.com/users",  # Duplicate
                    "method": "GET",
                    "headers": {},
                    "resource_type": "xhr",
                },
                {
                    "url": "https://api.example.com/users",  # Duplicate
                    "method": "GET",
                    "headers": {},
                    "resource_type": "fetch",
                },
            ],
            "network_responses": [],
            "websockets": [],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in network_capturer_module.discover(context)]

        # Should deduplicate (same URL and method)
        api_assets = [a for a in assets if a.asset_type == "api_endpoint"]
        unique_urls = set(a.url for a in api_assets)
        assert len(unique_urls) == len(api_assets)
