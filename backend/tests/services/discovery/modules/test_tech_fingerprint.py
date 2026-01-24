"""TechFingerprintModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- 기술 스택 시그니처 매칭
- 헤더 기반 탐지
- 스크립트 URL 기반 탐지
- 전역 변수 기반 탐지
- DOM 속성 기반 탐지
"""

from unittest.mock import MagicMock

import httpx
import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.tech_fingerprint import (
    DomSignatureMatcher,
    GlobalVariableMatcher,
    HeaderMatcher,
    ScriptMatcher,
    TechFingerprintModule,
    TechSignature,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    return MagicMock(spec=httpx.AsyncClient)


@pytest.fixture
def discovery_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Create a test discovery context."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.STANDARD,
        http_client=mock_http_client,
    )


@pytest.fixture
def tech_fingerprint_module() -> TechFingerprintModule:
    """Create TechFingerprintModule instance."""
    return TechFingerprintModule()


@pytest.fixture
def header_matcher() -> HeaderMatcher:
    """Create HeaderMatcher instance."""
    return HeaderMatcher()


@pytest.fixture
def script_matcher() -> ScriptMatcher:
    """Create ScriptMatcher instance."""
    return ScriptMatcher()


@pytest.fixture
def global_variable_matcher() -> GlobalVariableMatcher:
    """Create GlobalVariableMatcher instance."""
    return GlobalVariableMatcher()


@pytest.fixture
def dom_signature_matcher() -> DomSignatureMatcher:
    """Create DomSignatureMatcher instance."""
    return DomSignatureMatcher()


# ============================================================================
# Test 1: TechSignature 데이터 클래스
# ============================================================================


class TestTechSignature:
    """TechSignature 데이터 클래스 테스트."""

    def test_tech_signature_creation(self) -> None:
        """TechSignature 생성 테스트."""
        signature = TechSignature(
            name="React",
            category="frontend_framework",
            version="18.2.0",
            confidence=0.95,
            evidence=["script_url", "global_variable"],
        )

        assert signature.name == "React"
        assert signature.category == "frontend_framework"
        assert signature.version == "18.2.0"
        assert signature.confidence == 0.95
        assert "script_url" in signature.evidence

    def test_tech_signature_without_version(self) -> None:
        """버전 없는 TechSignature 생성 테스트."""
        signature = TechSignature(
            name="jQuery",
            category="library",
            confidence=0.8,
            evidence=["script_url"],
        )

        assert signature.name == "jQuery"
        assert signature.version is None
        assert signature.confidence == 0.8

    def test_tech_signature_default_values(self) -> None:
        """기본값 테스트."""
        signature = TechSignature(
            name="nginx",
            category="server",
        )

        assert signature.version is None
        assert signature.confidence == 0.0
        assert signature.evidence == []


# ============================================================================
# Test 2: HeaderMatcher - Server 헤더
# ============================================================================


class TestHeaderMatcherServer:
    """HeaderMatcher Server 헤더 테스트."""

    def test_nginx_detection(self, header_matcher: HeaderMatcher) -> None:
        """nginx 서버 탐지."""
        headers = {"Server": "nginx/1.21.0"}

        results = header_matcher.match(headers)

        nginx_sigs = [r for r in results if r.name == "nginx"]
        assert len(nginx_sigs) == 1
        assert nginx_sigs[0].category == "server"
        assert nginx_sigs[0].version == "1.21.0"
        assert nginx_sigs[0].confidence >= 0.9
        assert "header" in nginx_sigs[0].evidence

    def test_apache_detection(self, header_matcher: HeaderMatcher) -> None:
        """Apache 서버 탐지."""
        headers = {"Server": "Apache/2.4.41"}

        results = header_matcher.match(headers)

        apache_sigs = [r for r in results if r.name == "Apache"]
        assert len(apache_sigs) == 1
        assert apache_sigs[0].category == "server"
        assert apache_sigs[0].version == "2.4.41"

    def test_server_without_version(self, header_matcher: HeaderMatcher) -> None:
        """버전 없는 서버 탐지."""
        headers = {"Server": "nginx"}

        results = header_matcher.match(headers)

        nginx_sigs = [r for r in results if r.name == "nginx"]
        assert len(nginx_sigs) == 1
        assert nginx_sigs[0].version is None


# ============================================================================
# Test 3: HeaderMatcher - X-Powered-By 헤더
# ============================================================================


class TestHeaderMatcherPoweredBy:
    """HeaderMatcher X-Powered-By 헤더 테스트."""

    def test_express_detection(self, header_matcher: HeaderMatcher) -> None:
        """Express.js 탐지."""
        headers = {"X-Powered-By": "Express"}

        results = header_matcher.match(headers)

        express_sigs = [r for r in results if r.name == "Express"]
        assert len(express_sigs) == 1
        assert express_sigs[0].confidence >= 0.85

    def test_php_detection(self, header_matcher: HeaderMatcher) -> None:
        """PHP 탐지."""
        headers = {"X-Powered-By": "PHP/8.1.0"}

        results = header_matcher.match(headers)

        php_sigs = [r for r in results if r.name == "PHP"]
        assert len(php_sigs) == 1
        assert php_sigs[0].version == "8.1.0"


# ============================================================================
# Test 4: HeaderMatcher - Cloudflare CDN
# ============================================================================


class TestHeaderMatcherCloudflare:
    """HeaderMatcher Cloudflare 탐지 테스트."""

    def test_cloudflare_cf_ray_header(self, header_matcher: HeaderMatcher) -> None:
        """cf-ray 헤더로 Cloudflare 탐지."""
        headers = {"cf-ray": "7a1234567890abcdef-IAD"}

        results = header_matcher.match(headers)

        cloudflare_sigs = [r for r in results if r.name == "Cloudflare"]
        assert len(cloudflare_sigs) == 1
        assert cloudflare_sigs[0].category == "cdn"
        assert cloudflare_sigs[0].confidence >= 0.95

    def test_cloudflare_server_header(self, header_matcher: HeaderMatcher) -> None:
        """Server 헤더로 Cloudflare 탐지."""
        headers = {"Server": "cloudflare"}

        results = header_matcher.match(headers)

        cloudflare_sigs = [r for r in results if r.name == "Cloudflare"]
        assert len(cloudflare_sigs) == 1


# ============================================================================
# Test 5: ScriptMatcher - React
# ============================================================================


class TestScriptMatcherReact:
    """ScriptMatcher React 탐지 테스트."""

    def test_react_cdn_detection(self, script_matcher: ScriptMatcher) -> None:
        """React CDN URL 탐지."""
        scripts = ["https://unpkg.com/react@18.2.0/umd/react.production.min.js"]

        results = script_matcher.match(scripts)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) == 1
        assert react_sigs[0].category == "frontend_framework"
        assert react_sigs[0].version == "18.2.0"
        assert "script_url" in react_sigs[0].evidence

    def test_react_dom_detection(self, script_matcher: ScriptMatcher) -> None:
        """ReactDOM URL 탐지."""
        scripts = [
            "https://cdn.jsdelivr.net/npm/react-dom@17.0.2/umd/react-dom.production.min.js"
        ]

        results = script_matcher.match(scripts)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1

    def test_react_local_path(self, script_matcher: ScriptMatcher) -> None:
        """로컬 React 스크립트 탐지."""
        scripts = ["/static/js/react.min.js"]

        results = script_matcher.match(scripts)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1


# ============================================================================
# Test 6: ScriptMatcher - Vue
# ============================================================================


class TestScriptMatcherVue:
    """ScriptMatcher Vue 탐지 테스트."""

    def test_vue_cdn_detection(self, script_matcher: ScriptMatcher) -> None:
        """Vue CDN URL 탐지."""
        scripts = ["https://cdn.jsdelivr.net/npm/vue@3.3.4/dist/vue.global.min.js"]

        results = script_matcher.match(scripts)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) == 1
        assert vue_sigs[0].category == "frontend_framework"
        assert vue_sigs[0].version == "3.3.4"

    def test_vue2_detection(self, script_matcher: ScriptMatcher) -> None:
        """Vue 2 탐지."""
        scripts = ["https://cdn.vuejs.org/vue/2.7.14/vue.min.js"]

        results = script_matcher.match(scripts)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) >= 1


# ============================================================================
# Test 7: ScriptMatcher - Angular
# ============================================================================


class TestScriptMatcherAngular:
    """ScriptMatcher Angular 탐지 테스트."""

    def test_angular_detection(self, script_matcher: ScriptMatcher) -> None:
        """Angular 스크립트 탐지."""
        scripts = [
            "https://example.com/runtime.js",
            "https://example.com/polyfills.js",
            "https://example.com/main.js",
        ]

        # Angular is typically detected via DOM/global, but some patterns exist
        # This test may yield empty results as Angular detection is primarily DOM-based
        _results = script_matcher.match(scripts)

        # Angular detection via script URL is less common
        # The main detection happens via DOM attributes
        assert isinstance(_results, list)

    def test_angularjs_detection(self, script_matcher: ScriptMatcher) -> None:
        """AngularJS (1.x) 스크립트 탐지."""
        scripts = [
            "https://ajax.googleapis.com/ajax/libs/angularjs/1.8.2/angular.min.js"
        ]

        results = script_matcher.match(scripts)

        angular_sigs = [r for r in results if r.name == "AngularJS"]
        assert len(angular_sigs) == 1
        assert angular_sigs[0].version == "1.8.2"


# ============================================================================
# Test 8: ScriptMatcher - jQuery
# ============================================================================


class TestScriptMatcherJQuery:
    """ScriptMatcher jQuery 탐지 테스트."""

    def test_jquery_cdn_detection(self, script_matcher: ScriptMatcher) -> None:
        """jQuery CDN URL 탐지."""
        scripts = ["https://code.jquery.com/jquery-3.7.1.min.js"]

        results = script_matcher.match(scripts)

        jquery_sigs = [r for r in results if r.name == "jQuery"]
        assert len(jquery_sigs) == 1
        assert jquery_sigs[0].category == "library"
        assert jquery_sigs[0].version == "3.7.1"

    def test_jquery_google_cdn(self, script_matcher: ScriptMatcher) -> None:
        """jQuery Google CDN 탐지."""
        scripts = ["https://ajax.googleapis.com/ajax/libs/jquery/3.6.0/jquery.min.js"]

        results = script_matcher.match(scripts)

        jquery_sigs = [r for r in results if r.name == "jQuery"]
        assert len(jquery_sigs) >= 1


# ============================================================================
# Test 9: GlobalVariableMatcher - React
# ============================================================================


class TestGlobalVariableMatcherReact:
    """GlobalVariableMatcher React 탐지 테스트."""

    def test_react_global_detection(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """React 전역 변수 탐지."""
        variables = ["React", "__REACT_DEVTOOLS_GLOBAL_HOOK__"]

        results = global_variable_matcher.match(variables)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1
        assert "global_variable" in react_sigs[0].evidence

    def test_react_devtools_hook(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """React DevTools Hook 탐지."""
        variables = ["__REACT_DEVTOOLS_GLOBAL_HOOK__"]

        results = global_variable_matcher.match(variables)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1


# ============================================================================
# Test 10: GlobalVariableMatcher - Vue
# ============================================================================


class TestGlobalVariableMatcherVue:
    """GlobalVariableMatcher Vue 탐지 테스트."""

    def test_vue_global_detection(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """Vue 전역 변수 탐지."""
        variables = ["Vue", "__VUE__"]

        results = global_variable_matcher.match(variables)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) >= 1

    def test_vue_devtools_detection(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """Vue DevTools 탐지."""
        variables = ["__VUE_DEVTOOLS_GLOBAL_HOOK__"]

        results = global_variable_matcher.match(variables)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) >= 1


# ============================================================================
# Test 11: GlobalVariableMatcher - Angular & jQuery
# ============================================================================


class TestGlobalVariableMatcherOther:
    """GlobalVariableMatcher 기타 프레임워크 탐지 테스트."""

    def test_angular_global_detection(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """Angular 전역 변수 탐지."""
        variables = ["ng", "angular"]

        results = global_variable_matcher.match(variables)

        # AngularJS uses 'angular' global
        angular_sigs = [r for r in results if "Angular" in r.name]
        assert len(angular_sigs) >= 1

    def test_jquery_global_detection(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """jQuery 전역 변수 탐지."""
        variables = ["jQuery", "$"]

        results = global_variable_matcher.match(variables)

        jquery_sigs = [r for r in results if r.name == "jQuery"]
        assert len(jquery_sigs) >= 1


# ============================================================================
# Test 12: DomSignatureMatcher - React
# ============================================================================


class TestDomSignatureMatcherReact:
    """DomSignatureMatcher React 탐지 테스트."""

    def test_react_root_attribute(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """data-reactroot 속성 탐지."""
        html_content = '<div id="root" data-reactroot><div>App</div></div>'

        results = dom_signature_matcher.match(html_content)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1
        assert "dom_attribute" in react_sigs[0].evidence

    def test_react_reactid_attribute(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """data-reactid 속성 탐지 (React 15 이전)."""
        html_content = (
            '<div data-reactid=".0"><span data-reactid=".0.0">Text</span></div>'
        )

        results = dom_signature_matcher.match(html_content)

        react_sigs = [r for r in results if r.name == "React"]
        assert len(react_sigs) >= 1


# ============================================================================
# Test 13: DomSignatureMatcher - Vue
# ============================================================================


class TestDomSignatureMatcherVue:
    """DomSignatureMatcher Vue 탐지 테스트."""

    def test_vue_cloak_attribute(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """v-cloak 속성 탐지."""
        html_content = '<div id="app" v-cloak>{{ message }}</div>'

        results = dom_signature_matcher.match(html_content)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) >= 1

    def test_vue_directive_attributes(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """Vue 디렉티브 속성 탐지."""
        html_content = '<ul><li v-for="item in items">{{ item }}</li></ul>'

        results = dom_signature_matcher.match(html_content)

        vue_sigs = [r for r in results if r.name == "Vue"]
        assert len(vue_sigs) >= 1


# ============================================================================
# Test 14: DomSignatureMatcher - Angular
# ============================================================================


class TestDomSignatureMatcherAngular:
    """DomSignatureMatcher Angular 탐지 테스트."""

    def test_angular_ng_app_attribute(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """ng-app 속성 탐지 (AngularJS)."""
        html_content = (
            '<html ng-app="myApp"><body ng-controller="MainCtrl"></body></html>'
        )

        results = dom_signature_matcher.match(html_content)

        angular_sigs = [r for r in results if "Angular" in r.name]
        assert len(angular_sigs) >= 1

    def test_angular_ng_version_attribute(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """ng-version 속성 탐지 (Angular 2+)."""
        html_content = (
            '<app-root ng-version="16.2.0"><router-outlet></router-outlet></app-root>'
        )

        results = dom_signature_matcher.match(html_content)

        angular_sigs = [r for r in results if r.name == "Angular"]
        assert len(angular_sigs) >= 1
        # Should extract version from ng-version
        assert angular_sigs[0].version == "16.2.0"


# ============================================================================
# Test 15: DomSignatureMatcher - WordPress
# ============================================================================


class TestDomSignatureMatcherWordPress:
    """DomSignatureMatcher WordPress 탐지 테스트."""

    def test_wordpress_content_url(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """WordPress wp-content 경로 탐지."""
        html_content = """
        <link rel="stylesheet" href="https://example.com/wp-content/themes/theme/style.css">
        <script src="https://example.com/wp-includes/js/jquery/jquery.min.js"></script>
        """

        results = dom_signature_matcher.match(html_content)

        wp_sigs = [r for r in results if r.name == "WordPress"]
        assert len(wp_sigs) >= 1
        assert wp_sigs[0].category == "cms"

    def test_wordpress_meta_generator(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """WordPress 메타 태그 탐지."""
        html_content = '<meta name="generator" content="WordPress 6.4.2">'

        results = dom_signature_matcher.match(html_content)

        wp_sigs = [r for r in results if r.name == "WordPress"]
        assert len(wp_sigs) >= 1
        assert wp_sigs[0].version == "6.4.2"


# ============================================================================
# Test 16: TechFingerprintModule - 속성 테스트
# ============================================================================


class TestTechFingerprintModuleProperties:
    """TechFingerprintModule 속성 테스트."""

    def test_module_name(self, tech_fingerprint_module: TechFingerprintModule) -> None:
        """모듈 이름 테스트."""
        assert tech_fingerprint_module.name == "tech_fingerprint"

    def test_module_profiles(
        self, tech_fingerprint_module: TechFingerprintModule
    ) -> None:
        """지원 프로필 테스트."""
        assert ScanProfile.STANDARD in tech_fingerprint_module.profiles
        assert ScanProfile.FULL in tech_fingerprint_module.profiles
        assert ScanProfile.QUICK not in tech_fingerprint_module.profiles

    def test_is_active_for_standard(
        self, tech_fingerprint_module: TechFingerprintModule
    ) -> None:
        """STANDARD 프로필 활성화 테스트."""
        assert tech_fingerprint_module.is_active_for(ScanProfile.STANDARD) is True

    def test_is_active_for_quick(
        self, tech_fingerprint_module: TechFingerprintModule
    ) -> None:
        """QUICK 프로필 비활성화 테스트."""
        assert tech_fingerprint_module.is_active_for(ScanProfile.QUICK) is False


# ============================================================================
# Test 17: TechFingerprintModule - 통합 테스트
# ============================================================================


class TestTechFingerprintModuleIntegration:
    """TechFingerprintModule 통합 테스트."""

    @pytest.mark.asyncio
    async def test_discover_react_application(
        self,
        tech_fingerprint_module: TechFingerprintModule,
        mock_http_client: MagicMock,
    ) -> None:
        """React 애플리케이션 탐지 통합 테스트."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com",
                    "headers": {
                        "Server": "nginx/1.21.0",
                        "X-Powered-By": "Express",
                    },
                },
            ],
            "scripts": ["https://unpkg.com/react@18.2.0/umd/react.production.min.js"],
            "html_content": '<html><div id="root" data-reactroot></div></html>',
            "global_variables": ["React", "__REACT_DEVTOOLS_GLOBAL_HOOK__"],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in tech_fingerprint_module.discover(context)]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

        # Should detect React
        react_assets = [
            a for a in assets if a.metadata.get("technology_name") == "React"
        ]
        assert len(react_assets) >= 1

        # Check asset structure
        react_asset = react_assets[0]
        assert react_asset.asset_type == "technology"
        assert react_asset.source == "tech_fingerprint"
        assert "category" in react_asset.metadata
        assert "confidence" in react_asset.metadata

    @pytest.mark.asyncio
    async def test_discover_wordpress_site(
        self,
        tech_fingerprint_module: TechFingerprintModule,
        mock_http_client: MagicMock,
    ) -> None:
        """WordPress 사이트 탐지 통합 테스트."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com",
                    "headers": {
                        "Server": "Apache/2.4.41",
                        "X-Powered-By": "PHP/8.1.0",
                    },
                },
            ],
            "scripts": [],
            "html_content": """
            <html>
            <head>
            <meta name="generator" content="WordPress 6.4.2">
            <link rel="stylesheet" href="/wp-content/themes/theme/style.css">
            </head>
            <body></body>
            </html>
            """,
            "global_variables": [],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in tech_fingerprint_module.discover(context)]

        # Should detect WordPress
        wp_assets = [
            a for a in assets if a.metadata.get("technology_name") == "WordPress"
        ]
        assert len(wp_assets) >= 1
        assert wp_assets[0].metadata.get("category") == "cms"

    @pytest.mark.asyncio
    async def test_discover_multiple_technologies(
        self,
        tech_fingerprint_module: TechFingerprintModule,
        mock_http_client: MagicMock,
    ) -> None:
        """다중 기술 스택 탐지 통합 테스트."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com",
                    "headers": {
                        "Server": "nginx/1.21.0",
                        "cf-ray": "7a1234567890abcdef-IAD",
                    },
                },
            ],
            "scripts": [
                "https://code.jquery.com/jquery-3.7.1.min.js",
                "https://cdn.jsdelivr.net/npm/vue@3.3.4/dist/vue.global.min.js",
            ],
            "html_content": '<div id="app" v-cloak>{{ message }}</div>',
            "global_variables": ["Vue", "jQuery", "$"],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in tech_fingerprint_module.discover(context)]

        tech_names = [a.metadata.get("technology_name") for a in assets]

        # Should detect multiple technologies
        assert "nginx" in tech_names
        assert "Cloudflare" in tech_names
        assert "Vue" in tech_names
        assert "jQuery" in tech_names

    @pytest.mark.asyncio
    async def test_discover_empty_crawl_data(
        self,
        tech_fingerprint_module: TechFingerprintModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 crawl_data 처리 테스트."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [asset async for asset in tech_fingerprint_module.discover(context)]

        # Should not raise error, may return empty or minimal results
        assert isinstance(assets, list)

    @pytest.mark.asyncio
    async def test_discover_confidence_aggregation(
        self,
        tech_fingerprint_module: TechFingerprintModule,
        mock_http_client: MagicMock,
    ) -> None:
        """신뢰도 집계 테스트 - 다중 증거 시 높은 신뢰도."""
        crawl_data = {
            "responses": [
                {
                    "url": "https://example.com",
                    "headers": {},
                },
            ],
            "scripts": ["https://unpkg.com/react@18.2.0/umd/react.production.min.js"],
            "html_content": "<div data-reactroot></div>",
            "global_variables": ["React", "__REACT_DEVTOOLS_GLOBAL_HOOK__"],
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in tech_fingerprint_module.discover(context)]

        react_assets = [
            a for a in assets if a.metadata.get("technology_name") == "React"
        ]

        # React should be detected with high confidence (multiple evidence sources)
        assert len(react_assets) >= 1
        # When multiple evidence sources, confidence should be higher
        assert react_assets[0].metadata.get("confidence", 0) >= 0.9


# ============================================================================
# Test 18: 에지 케이스 테스트
# ============================================================================


class TestEdgeCases:
    """에지 케이스 테스트."""

    def test_script_matcher_with_empty_list(
        self, script_matcher: ScriptMatcher
    ) -> None:
        """빈 스크립트 리스트 처리."""
        results = script_matcher.match([])
        assert results == []

    def test_global_variable_matcher_with_empty_list(
        self, global_variable_matcher: GlobalVariableMatcher
    ) -> None:
        """빈 변수 리스트 처리."""
        results = global_variable_matcher.match([])
        assert results == []

    def test_dom_signature_matcher_with_empty_html(
        self, dom_signature_matcher: DomSignatureMatcher
    ) -> None:
        """빈 HTML 처리."""
        results = dom_signature_matcher.match("")
        assert results == []

    def test_header_matcher_with_empty_headers(
        self, header_matcher: HeaderMatcher
    ) -> None:
        """빈 헤더 처리."""
        results = header_matcher.match({})
        assert results == []

    def test_case_insensitive_header_matching(
        self, header_matcher: HeaderMatcher
    ) -> None:
        """헤더 대소문자 무관 매칭."""
        headers = {"server": "NGINX/1.21.0", "x-powered-by": "express"}

        results = header_matcher.match(headers)

        # Should still detect technologies despite case differences
        names = [r.name.lower() for r in results]
        assert "nginx" in names or "express" in names
