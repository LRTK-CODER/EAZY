"""ResponseAnalyzerModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- HTTP 응답 헤더 분석
- 쿠키 분석
- 에러 메시지 분석
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.response_analyzer import (
    CookieAnalyzer,
    CspParser,
    ErrorDetector,
    HeaderAnalyzer,
    ResponseAnalyzerModule,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    client = MagicMock(spec=httpx.AsyncClient)
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
def response_analyzer_module() -> ResponseAnalyzerModule:
    """Create ResponseAnalyzerModule instance."""
    return ResponseAnalyzerModule()


@pytest.fixture
def header_analyzer() -> HeaderAnalyzer:
    """Create HeaderAnalyzer instance."""
    return HeaderAnalyzer()


@pytest.fixture
def csp_parser() -> CspParser:
    """Create CspParser instance."""
    return CspParser()


@pytest.fixture
def cookie_analyzer() -> CookieAnalyzer:
    """Create CookieAnalyzer instance."""
    return CookieAnalyzer()


@pytest.fixture
def error_detector() -> ErrorDetector:
    """Create ErrorDetector instance."""
    return ErrorDetector()


# ============================================================================
# Test 1: Server 헤더 추출
# ============================================================================


class TestServerHeaderExtraction:
    """Server 헤더 추출 테스트."""

    def test_server_header_extraction(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Server 헤더에서 서버 정보 추출."""
        headers = {
            "Server": "nginx/1.21.0",
            "Content-Type": "text/html",
        }

        result = header_analyzer.analyze(headers)

        assert result.server is not None
        assert result.server.name == "nginx"
        assert result.server.version == "1.21.0"

    def test_server_header_without_version(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """버전 없는 Server 헤더 처리."""
        headers = {
            "Server": "Apache",
        }

        result = header_analyzer.analyze(headers)

        assert result.server is not None
        assert result.server.name == "Apache"
        assert result.server.version is None

    def test_server_header_complex_format(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """복잡한 Server 헤더 형식 처리."""
        headers = {
            "Server": "Apache/2.4.41 (Ubuntu) OpenSSL/1.1.1",
        }

        result = header_analyzer.analyze(headers)

        assert result.server is not None
        assert result.server.name == "Apache"
        assert result.server.version == "2.4.41"
        assert "Ubuntu" in result.server.extra_info
        assert "OpenSSL/1.1.1" in result.server.extra_info

    def test_missing_server_header(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Server 헤더 없을 때 처리."""
        headers = {
            "Content-Type": "text/html",
        }

        result = header_analyzer.analyze(headers)

        assert result.server is None


# ============================================================================
# Test 2: X-Powered-By 헤더 추출
# ============================================================================


class TestXPoweredByExtraction:
    """X-Powered-By 헤더 추출 테스트."""

    def test_x_powered_by_extraction(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """X-Powered-By 헤더에서 기술 스택 추출."""
        headers = {
            "X-Powered-By": "PHP/8.1.0",
        }

        result = header_analyzer.analyze(headers)

        assert result.powered_by is not None
        assert result.powered_by.name == "PHP"
        assert result.powered_by.version == "8.1.0"

    def test_x_powered_by_express(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Express.js X-Powered-By 처리."""
        headers = {
            "X-Powered-By": "Express",
        }

        result = header_analyzer.analyze(headers)

        assert result.powered_by is not None
        assert result.powered_by.name == "Express"
        assert result.powered_by.version is None

    def test_x_powered_by_aspnet(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """ASP.NET X-Powered-By 처리."""
        headers = {
            "X-Powered-By": "ASP.NET",
            "X-AspNet-Version": "4.0.30319",
        }

        result = header_analyzer.analyze(headers)

        assert result.powered_by is not None
        assert result.powered_by.name == "ASP.NET"
        assert result.aspnet_version == "4.0.30319"

    def test_multiple_x_powered_by_values(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """다중 X-Powered-By 값 처리 (comma-separated)."""
        headers = {
            "X-Powered-By": "PHP/7.4, PleskLin",
        }

        result = header_analyzer.analyze(headers)

        assert len(result.powered_by_list) == 2
        assert result.powered_by_list[0].name == "PHP"
        assert result.powered_by_list[1].name == "PleskLin"


# ============================================================================
# Test 3: CSP 허용 도메인 추출
# ============================================================================


class TestCspDomainExtraction:
    """CSP 허용 도메인 추출 테스트."""

    def test_csp_domain_extraction(
        self,
        csp_parser: CspParser,
    ) -> None:
        """Content-Security-Policy에서 허용 도메인 추출."""
        csp_header = (
            "default-src 'self'; "
            "script-src 'self' https://cdn.example.com https://analytics.example.com; "
            "img-src 'self' data: https://images.example.com"
        )

        result = csp_parser.parse(csp_header)

        assert "https://cdn.example.com" in result.allowed_domains
        assert "https://analytics.example.com" in result.allowed_domains
        assert "https://images.example.com" in result.allowed_domains

    def test_csp_script_src_extraction(
        self,
        csp_parser: CspParser,
    ) -> None:
        """script-src 디렉티브에서 도메인 추출."""
        csp_header = "script-src 'self' 'unsafe-inline' https://scripts.example.com"

        result = csp_parser.parse(csp_header)

        assert "https://scripts.example.com" in result.script_sources
        assert "'unsafe-inline'" in result.script_sources

    def test_csp_wildcard_domains(
        self,
        csp_parser: CspParser,
    ) -> None:
        """와일드카드 도메인 처리."""
        csp_header = "script-src *.example.com https://*.cdn.net"

        result = csp_parser.parse(csp_header)

        assert "*.example.com" in result.allowed_domains
        assert "https://*.cdn.net" in result.allowed_domains

    def test_csp_report_uri_extraction(
        self,
        csp_parser: CspParser,
    ) -> None:
        """report-uri 추출."""
        csp_header = "default-src 'self'; " "report-uri https://example.com/csp-report"

        result = csp_parser.parse(csp_header)

        assert result.report_uri == "https://example.com/csp-report"


# ============================================================================
# Test 4: CORS 허용 Origin 추출
# ============================================================================


class TestCorsOriginExtraction:
    """CORS 허용 Origin 추출 테스트."""

    def test_cors_origin_extraction(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Access-Control-Allow-Origin에서 허용 Origin 추출."""
        headers = {
            "Access-Control-Allow-Origin": "https://trusted.example.com",
        }

        result = header_analyzer.analyze(headers)

        assert result.cors is not None
        assert result.cors.allow_origin == "https://trusted.example.com"

    def test_cors_wildcard_origin(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """와일드카드 CORS Origin 감지."""
        headers = {
            "Access-Control-Allow-Origin": "*",
        }

        result = header_analyzer.analyze(headers)

        assert result.cors is not None
        assert result.cors.allow_origin == "*"
        assert result.cors.is_wildcard is True

    def test_cors_credentials_flag(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Access-Control-Allow-Credentials 플래그 감지."""
        headers = {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Credentials": "true",
        }

        result = header_analyzer.analyze(headers)

        assert result.cors is not None
        assert result.cors.allow_credentials is True

    def test_cors_allowed_methods(
        self,
        header_analyzer: HeaderAnalyzer,
    ) -> None:
        """Access-Control-Allow-Methods 추출."""
        headers = {
            "Access-Control-Allow-Origin": "https://example.com",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE",
        }

        result = header_analyzer.analyze(headers)

        assert result.cors is not None
        assert "GET" in result.cors.allowed_methods
        assert "POST" in result.cors.allowed_methods
        assert "DELETE" in result.cors.allowed_methods


# ============================================================================
# Test 5: Set-Cookie 도메인 추출
# ============================================================================


class TestCookieDomainExtraction:
    """Set-Cookie 도메인 추출 테스트."""

    def test_cookie_domain_extraction(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """Set-Cookie에서 도메인 속성 추출."""
        set_cookie = "session_id=abc123; Domain=.example.com; Path=/; HttpOnly"

        result = cookie_analyzer.parse(set_cookie)

        assert result.name == "session_id"
        assert result.domain == ".example.com"

    def test_cookie_without_domain(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """도메인 속성 없는 쿠키 처리."""
        set_cookie = "session_id=abc123; Path=/; HttpOnly"

        result = cookie_analyzer.parse(set_cookie)

        assert result.name == "session_id"
        assert result.domain is None

    def test_cookie_subdomain_scope(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """서브도메인 범위 쿠키 처리."""
        set_cookie = "tracking=xyz789; Domain=sub.example.com"

        result = cookie_analyzer.parse(set_cookie)

        assert result.domain == "sub.example.com"


# ============================================================================
# Test 6: Set-Cookie 경로 추출
# ============================================================================


class TestCookiePathExtraction:
    """Set-Cookie 경로 추출 테스트."""

    def test_cookie_path_extraction(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """Set-Cookie에서 경로 속성 추출."""
        set_cookie = "api_token=def456; Path=/api; Secure"

        result = cookie_analyzer.parse(set_cookie)

        assert result.name == "api_token"
        assert result.path == "/api"

    def test_cookie_root_path(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """루트 경로 쿠키 처리."""
        set_cookie = "global=value; Path=/"

        result = cookie_analyzer.parse(set_cookie)

        assert result.path == "/"

    def test_cookie_without_path(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """경로 속성 없는 쿠키 처리."""
        set_cookie = "simple=cookie"

        result = cookie_analyzer.parse(set_cookie)

        assert result.name == "simple"
        assert result.path is None


# ============================================================================
# Test 7: Cookie 보안 플래그 감지
# ============================================================================


class TestCookieSecurityFlags:
    """Cookie 보안 플래그 감지 테스트."""

    def test_cookie_security_flags(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """Secure, HttpOnly 플래그 감지."""
        set_cookie = "secure_session=value; Secure; HttpOnly; SameSite=Strict"

        result = cookie_analyzer.parse(set_cookie)

        assert result.secure is True
        assert result.http_only is True
        assert result.same_site == "Strict"

    def test_cookie_without_secure_flag(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """Secure 플래그 없는 쿠키 감지."""
        set_cookie = "insecure_session=value; HttpOnly"

        result = cookie_analyzer.parse(set_cookie)

        assert result.secure is False
        assert result.http_only is True

    def test_cookie_without_httponly_flag(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """HttpOnly 플래그 없는 쿠키 감지 (XSS 위험)."""
        set_cookie = "js_accessible=value; Secure"

        result = cookie_analyzer.parse(set_cookie)

        assert result.secure is True
        assert result.http_only is False

    def test_cookie_samesite_variations(
        self,
        cookie_analyzer: CookieAnalyzer,
    ) -> None:
        """SameSite 속성 변형 처리."""
        strict_cookie = "a=1; SameSite=Strict"
        lax_cookie = "b=2; SameSite=Lax"
        none_cookie = "c=3; SameSite=None; Secure"

        strict_result = cookie_analyzer.parse(strict_cookie)
        lax_result = cookie_analyzer.parse(lax_cookie)
        none_result = cookie_analyzer.parse(none_cookie)

        assert strict_result.same_site == "Strict"
        assert lax_result.same_site == "Lax"
        assert none_result.same_site == "None"


# ============================================================================
# Test 8: 에러 메시지 내 경로 탐지
# ============================================================================


class TestErrorMessagePathLeakage:
    """에러 메시지 내 경로 탐지 테스트."""

    def test_error_message_path_leakage(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """에러 메시지에서 서버 경로 탐지."""
        error_body = """
        <html>
        <body>
        <h1>Error 500</h1>
        <p>File not found: /var/www/html/app/config/database.php</p>
        </body>
        </html>
        """

        result = error_detector.detect(error_body)

        assert result.has_path_leakage is True
        assert "/var/www/html/app/config/database.php" in result.leaked_paths

    def test_windows_path_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """Windows 경로 탐지."""
        error_body = """
        Error: Cannot open file C:\\inetpub\\wwwroot\\web.config
        """

        result = error_detector.detect(error_body)

        assert result.has_path_leakage is True
        assert "C:\\inetpub\\wwwroot\\web.config" in result.leaked_paths

    def test_multiple_path_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """다중 경로 탐지."""
        error_body = """
        Error in /home/user/app/src/handler.py at line 42
        Called from /home/user/app/src/main.py at line 15
        """

        result = error_detector.detect(error_body)

        assert result.has_path_leakage is True
        assert len(result.leaked_paths) >= 2

    def test_no_path_leakage(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """경로 노출 없는 정상 에러 페이지."""
        error_body = """
        <html>
        <body>
        <h1>404 - Page Not Found</h1>
        <p>The requested resource could not be found.</p>
        </body>
        </html>
        """

        result = error_detector.detect(error_body)

        assert result.has_path_leakage is False
        assert len(result.leaked_paths) == 0


# ============================================================================
# Test 9: 스택 트레이스 탐지
# ============================================================================


class TestStackTraceDetection:
    """스택 트레이스 탐지 테스트."""

    def test_stack_trace_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """스택 트레이스 탐지."""
        error_body = """
        Traceback (most recent call last):
          File "/app/handler.py", line 42, in process
            result = database.query(sql)
          File "/app/database.py", line 15, in query
            cursor.execute(sql)
        psycopg2.errors.SyntaxError: syntax error at or near "SELECT"
        """

        result = error_detector.detect(error_body)

        assert result.has_stack_trace is True
        assert result.stack_trace_type == "python"

    def test_java_stack_trace_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """Java 스택 트레이스 탐지."""
        error_body = """
        java.lang.NullPointerException
            at com.example.app.UserService.getUser(UserService.java:42)
            at com.example.app.UserController.show(UserController.java:15)
            at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
        """

        result = error_detector.detect(error_body)

        assert result.has_stack_trace is True
        assert result.stack_trace_type == "java"

    def test_php_stack_trace_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """PHP 스택 트레이스 탐지."""
        error_body = """
        Fatal error: Uncaught Exception: Database connection failed in /var/www/html/db.php:15
        Stack trace:
        #0 /var/www/html/index.php(25): Database->connect()
        #1 {main}
        thrown in /var/www/html/db.php on line 15
        """

        result = error_detector.detect(error_body)

        assert result.has_stack_trace is True
        assert result.stack_trace_type == "php"

    def test_nodejs_stack_trace_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """Node.js 스택 트레이스 탐지."""
        error_body = """
        TypeError: Cannot read property 'id' of undefined
            at Object.<anonymous> (/app/routes/user.js:15:20)
            at Module._compile (internal/modules/cjs/loader.js:1063:30)
            at Object.Module._extensions..js (internal/modules/cjs/loader.js:1092:10)
        """

        result = error_detector.detect(error_body)

        assert result.has_stack_trace is True
        assert result.stack_trace_type == "nodejs"

    def test_dotnet_stack_trace_detection(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """.NET 스택 트레이스 탐지."""
        error_body = """
        System.NullReferenceException: Object reference not set to an instance of an object.
           at MyApp.Controllers.HomeController.Index() in C:\\Projects\\MyApp\\Controllers\\HomeController.cs:line 25
           at lambda_method(Closure , Object , Object[] )
        """

        result = error_detector.detect(error_body)

        assert result.has_stack_trace is True
        assert result.stack_trace_type == "dotnet"

    def test_no_stack_trace(
        self,
        error_detector: ErrorDetector,
    ) -> None:
        """스택 트레이스 없는 정상 응답."""
        body = """
        <html>
        <body>
        <h1>Welcome to our site</h1>
        <p>Normal content here.</p>
        </body>
        </html>
        """

        result = error_detector.detect(body)

        assert result.has_stack_trace is False


# ============================================================================
# Integration Tests
# ============================================================================


class TestResponseAnalyzerModuleIntegration:
    """ResponseAnalyzerModule 통합 테스트."""

    async def test_module_properties(
        self,
        response_analyzer_module: ResponseAnalyzerModule,
    ) -> None:
        """모듈 속성 테스트."""
        assert response_analyzer_module.name == "response_analyzer"
        assert ScanProfile.STANDARD in response_analyzer_module.profiles
        assert ScanProfile.FULL in response_analyzer_module.profiles

    async def test_discover_with_crawl_data(
        self,
        response_analyzer_module: ResponseAnalyzerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """crawl_data에서 응답 분석."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com/api/users",
                    "headers": {
                        "Server": "nginx/1.21.0",
                        "X-Powered-By": "Express",
                        "Set-Cookie": "session=abc123; HttpOnly; Secure",
                        "Content-Security-Policy": "default-src 'self'; script-src https://cdn.example.com",
                    },
                    "body": "<html><body>Normal page</body></html>",
                    "status_code": 200,
                },
            ],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in response_analyzer_module.discover(context)]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

        # Should have discovered server info
        server_assets = [a for a in assets if a.asset_type == "server_info"]
        assert len(server_assets) > 0

    async def test_discover_with_error_response(
        self,
        response_analyzer_module: ResponseAnalyzerModule,
        mock_http_client: MagicMock,
    ) -> None:
        """에러 응답에서 정보 추출."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com/error",
                    "headers": {"Server": "Apache/2.4.41"},
                    "body": """
                    <html>
                    <body>
                    <h1>500 Internal Server Error</h1>
                    <pre>
                    Traceback (most recent call last):
                      File "/var/www/app/views.py", line 42, in index
                        return render(request, "index.html")
                    FileNotFoundError: /var/www/app/templates/index.html
                    </pre>
                    </body>
                    </html>
                    """,
                    "status_code": 500,
                },
            ],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in response_analyzer_module.discover(context)]

        # Should detect information leakage
        leakage_assets = [a for a in assets if a.asset_type == "information_leakage"]
        assert len(leakage_assets) > 0

        # Check metadata contains path leakage info
        path_leakage = [
            a for a in leakage_assets if "path" in a.metadata.get("type", "")
        ]
        assert len(path_leakage) > 0
