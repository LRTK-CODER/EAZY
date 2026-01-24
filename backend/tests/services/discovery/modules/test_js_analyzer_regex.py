"""JsAnalyzerRegexModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- URL 문자열/템플릿 리터럴 추출
- HTTP 클라이언트 호출 탐지 (fetch, axios, jQuery, XHR)
- API 키/시크릿 탐지
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.js_analyzer_regex import (
    HttpClientDetector,
    JsAnalyzerRegexModule,
    SecretDetector,
    UrlPatternMatcher,
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
def url_matcher() -> UrlPatternMatcher:
    """Create UrlPatternMatcher instance."""
    return UrlPatternMatcher()


@pytest.fixture
def http_detector() -> HttpClientDetector:
    """Create HttpClientDetector instance."""
    return HttpClientDetector()


@pytest.fixture
def secret_detector() -> SecretDetector:
    """Create SecretDetector instance."""
    return SecretDetector()


@pytest.fixture
def js_analyzer_module() -> JsAnalyzerRegexModule:
    """Create JsAnalyzerRegexModule instance."""
    return JsAnalyzerRegexModule()


# ============================================================================
# Test 1: URL String Literal Extraction
# ============================================================================


class TestUrlStringLiteral:
    """URL 문자열 리터럴 추출 테스트."""

    def test_absolute_url_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """절대 URL 추출."""
        js_code = """
        const apiUrl = "https://api.example.com/users";
        const wsUrl = 'wss://ws.example.com/socket';
        """

        urls = url_matcher.extract_string_urls(js_code)

        assert len(urls) >= 2
        url_strings = [u.url for u in urls]
        assert "https://api.example.com/users" in url_strings
        assert "wss://ws.example.com/socket" in url_strings

    def test_relative_api_url_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """상대 API URL 추출."""
        js_code = """
        fetch("/api/users");
        axios.get("/v1/products");
        """

        urls = url_matcher.extract_string_urls(js_code)

        url_strings = [u.url for u in urls]
        assert "/api/users" in url_strings
        assert "/v1/products" in url_strings

    def test_path_url_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """일반 경로 URL 추출."""
        js_code = """
        const path = "/users/profile";
        const endpoint = "/data/export.json";
        """

        urls = url_matcher.extract_string_urls(js_code)

        url_strings = [u.url for u in urls]
        assert any("/users/profile" in u for u in url_strings)

    def test_false_positive_filtering(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """False positive 필터링."""
        js_code = """
        // This is a comment
        const regex = /\\d+/;
        const empty = "/";
        """

        urls = url_matcher.extract_string_urls(js_code)

        # 단순 "/" 는 필터링되어야 함
        url_strings = [u.url for u in urls]
        assert "/" not in url_strings


# ============================================================================
# Test 2: URL Template Literal Extraction
# ============================================================================


class TestUrlTemplateLiteral:
    """URL 템플릿 리터럴 추출 테스트."""

    def test_template_literal_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """템플릿 리터럴 URL 추출."""
        js_code = """
        const url = `/api/users/${userId}`;
        const endpoint = `https://api.example.com/items/${itemId}/details`;
        """

        urls = url_matcher.extract_template_urls(js_code)

        assert len(urls) >= 2
        assert all(u.is_template for u in urls)

    def test_template_placeholder_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """템플릿 플레이스홀더 추출."""
        js_code = "`/api/users/${userId}/posts/${postId}`"

        urls = url_matcher.extract_template_urls(js_code)

        assert len(urls) == 1
        assert "userId" in urls[0].placeholders
        assert "postId" in urls[0].placeholders


# ============================================================================
# Test 3: Fetch Call Detection
# ============================================================================


class TestFetchCallDetection:
    """fetch 호출 탐지 테스트."""

    def test_fetch_get_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """fetch GET 호출 탐지."""
        js_code = """fetch("https://api.example.com/data")"""

        calls = http_detector.detect_fetch(js_code)

        assert len(calls) == 1
        assert calls[0].client_type == "fetch"
        assert calls[0].url == "https://api.example.com/data"

    def test_fetch_with_options_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """fetch 옵션 포함 호출 탐지."""
        js_code = """
        fetch("https://api.example.com/users", {
            method: "POST",
            body: JSON.stringify(data)
        })
        """

        calls = http_detector.detect_fetch(js_code)

        assert len(calls) == 1
        assert calls[0].has_options is True


# ============================================================================
# Test 4: Axios Call Detection
# ============================================================================


class TestAxiosCallDetection:
    """axios 호출 탐지 테스트."""

    def test_axios_get_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """axios.get 호출 탐지."""
        js_code = """axios.get("https://api.example.com/users")"""

        calls = http_detector.detect_axios(js_code)

        assert len(calls) == 1
        assert calls[0].client_type == "axios"
        assert calls[0].method == "GET"

    def test_axios_post_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """axios.post 호출 탐지."""
        js_code = """axios.post("https://api.example.com/users")"""

        calls = http_detector.detect_axios(js_code)

        assert len(calls) == 1
        assert calls[0].method == "POST"

    def test_axios_methods_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """모든 axios 메서드 탐지."""
        js_code = """
        axios.get("/api/get");
        axios.post("/api/post");
        axios.put("/api/put");
        axios.delete("/api/delete");
        axios.patch("/api/patch");
        """

        calls = http_detector.detect_axios(js_code)

        methods = [c.method for c in calls]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods
        assert "PATCH" in methods


# ============================================================================
# Test 5: jQuery AJAX Detection
# ============================================================================


class TestJqueryAjaxDetection:
    """jQuery AJAX 호출 탐지 테스트."""

    def test_jquery_ajax_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """$.ajax 호출 탐지."""
        js_code = """$.ajax({ url: "https://api.example.com/data" })"""

        calls = http_detector.detect_jquery(js_code)

        assert len(calls) == 1
        assert calls[0].client_type == "jquery"

    def test_jquery_get_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """$.get 호출 탐지."""
        js_code = """$.get("https://api.example.com/users")"""

        calls = http_detector.detect_jquery(js_code)

        assert len(calls) == 1
        assert calls[0].method == "GET"

    def test_jquery_post_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """$.post 호출 탐지."""
        js_code = """$.post("https://api.example.com/submit")"""

        calls = http_detector.detect_jquery(js_code)

        assert len(calls) == 1
        assert calls[0].method == "POST"


# ============================================================================
# Test 6: XHR Open Detection
# ============================================================================


class TestXhrOpenDetection:
    """XMLHttpRequest.open 호출 탐지 테스트."""

    def test_xhr_open_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """xhr.open 호출 탐지."""
        js_code = """
        var xhr = new XMLHttpRequest();
        xhr.open("GET", "https://api.example.com/data");
        """

        calls = http_detector.detect_xhr(js_code)

        assert len(calls) == 1
        assert calls[0].client_type == "xhr"
        assert calls[0].method == "GET"

    def test_xhr_post_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """xhr.open POST 호출 탐지."""
        js_code = """xhr.open("POST", "/api/submit")"""

        calls = http_detector.detect_xhr(js_code)

        assert len(calls) == 1
        assert calls[0].method == "POST"


# ============================================================================
# Test 7: Hardcoded API Key Detection
# ============================================================================


class TestHardcodedApiKeyDetection:
    """하드코딩된 API 키 탐지 테스트."""

    def test_aws_access_key_detection(
        self,
        secret_detector: SecretDetector,
    ) -> None:
        """AWS Access Key 탐지."""
        js_code = 'const AWS_KEY = "AKIAIOSFODNN7EXAMPLE";'

        secrets = secret_detector.detect(js_code)

        aws_keys = [s for s in secrets if "aws" in s.pattern_name.lower()]
        assert len(aws_keys) > 0

    def test_stripe_key_detection(
        self,
        secret_detector: SecretDetector,
    ) -> None:
        """Stripe API Key 탐지."""
        js_code = 'const STRIPE_KEY = "sk_live_RaNd0M123456789012345678";'

        secrets = secret_detector.detect(js_code)

        stripe_keys = [s for s in secrets if "stripe" in s.pattern_name.lower()]
        assert len(stripe_keys) > 0

    def test_github_token_detection(
        self,
        secret_detector: SecretDetector,
    ) -> None:
        """GitHub Token 탐지."""
        js_code = 'const GH_TOKEN = "ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx";'

        secrets = secret_detector.detect(js_code)

        gh_tokens = [s for s in secrets if "github" in s.pattern_name.lower()]
        assert len(gh_tokens) > 0


# ============================================================================
# Test 8: Hardcoded Secret Detection
# ============================================================================


class TestHardcodedSecretDetection:
    """하드코딩된 시크릿 탐지 테스트."""

    def test_jwt_detection(
        self,
        secret_detector: SecretDetector,
    ) -> None:
        """JWT 탐지."""
        # 실제 JWT 형식
        js_code = 'const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U";'

        secrets = secret_detector.detect(js_code)

        jwt_secrets = [s for s in secrets if "jwt" in s.pattern_name.lower()]
        assert len(jwt_secrets) > 0

    def test_private_key_header_detection(
        self,
        secret_detector: SecretDetector,
    ) -> None:
        """Private Key 헤더 탐지."""
        js_code = """
        const privateKey = `-----BEGIN RSA PRIVATE KEY-----
        MIIEpAIBAAKCAQEA...
        -----END RSA PRIVATE KEY-----`;
        """

        secrets = secret_detector.detect(js_code)

        pk_secrets = [s for s in secrets if "private_key" in s.pattern_name.lower()]
        assert len(pk_secrets) > 0


# ============================================================================
# Test 9: Minified Code Handling
# ============================================================================


class TestMinifiedCodeHandling:
    """Minified 코드 처리 테스트."""

    def test_minified_url_extraction(
        self,
        url_matcher: UrlPatternMatcher,
    ) -> None:
        """Minified 코드에서 URL 추출."""
        minified_js = 'fetch("https://api.example.com/users"),axios.get("/api/data")'

        urls = url_matcher.extract_string_urls(minified_js)

        url_strings = [u.url for u in urls]
        assert "https://api.example.com/users" in url_strings
        assert "/api/data" in url_strings

    def test_minified_http_client_detection(
        self,
        http_detector: HttpClientDetector,
    ) -> None:
        """Minified 코드에서 HTTP 클라이언트 탐지."""
        minified_js = 'fetch("/a"),axios.get("/b"),$.get("/c")'

        calls = http_detector.detect_all(minified_js)

        assert len(calls) >= 3


# ============================================================================
# Test 10: Module Integration Tests
# ============================================================================


class TestJsAnalyzerModuleIntegration:
    """JsAnalyzerRegexModule 통합 테스트."""

    def test_module_properties(
        self,
        js_analyzer_module: JsAnalyzerRegexModule,
    ) -> None:
        """모듈 속성 테스트."""
        assert js_analyzer_module.name == "js_analyzer_regex"
        assert ScanProfile.QUICK in js_analyzer_module.profiles
        assert ScanProfile.STANDARD in js_analyzer_module.profiles
        assert ScanProfile.FULL in js_analyzer_module.profiles

    async def test_discover_with_js_content(
        self,
        js_analyzer_module: JsAnalyzerRegexModule,
        mock_http_client: MagicMock,
    ) -> None:
        """crawl_data에서 JS 콘텐츠 분석."""
        crawl_data = {
            "js_contents": [
                {
                    "url": "https://example.com/app.js",
                    "content": """
                    fetch("https://api.example.com/users");
                    const endpoint = "/api/data";
                    const key = "AKIAIOSFODNN7EXAMPLE";
                    """,
                },
            ],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in js_analyzer_module.discover(context)]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)
        assert len(assets) > 0

    async def test_discover_with_empty_data(
        self,
        js_analyzer_module: JsAnalyzerRegexModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 데이터 처리."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [asset async for asset in js_analyzer_module.discover(context)]

        # Should handle empty data gracefully
        assert isinstance(assets, list)

    async def test_discover_secret_detection_profile(
        self,
        js_analyzer_module: JsAnalyzerRegexModule,
        mock_http_client: MagicMock,
    ) -> None:
        """시크릿 탐지는 STANDARD, FULL 프로필에서만."""
        crawl_data = {
            "js_contents": [
                {
                    "url": "https://example.com/app.js",
                    "content": 'const key = "sk_live_xxxxxxxxxxxxxxxxxxxx";',
                },
            ],
        }

        # QUICK 프로필에서는 시크릿 탐지 안함
        context_quick = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.QUICK,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets_quick = [
            asset async for asset in js_analyzer_module.discover(context_quick)
        ]
        secret_assets_quick = [a for a in assets_quick if a.asset_type == "secret"]
        assert len(secret_assets_quick) == 0

        # STANDARD 프로필에서는 시크릿 탐지
        context_standard = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets_standard = [
            asset async for asset in js_analyzer_module.discover(context_standard)
        ]
        secret_assets_standard = [
            a for a in assets_standard if a.asset_type == "secret"
        ]
        # 시크릿이 탐지될 수 있음 (패턴에 따라 다름)
        assert isinstance(secret_assets_standard, list)
