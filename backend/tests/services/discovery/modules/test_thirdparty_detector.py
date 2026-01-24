"""ThirdPartyDetectorModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- 외부 서비스 탐지 (Google Analytics, Firebase, Stripe 등)
- 스크립트 URL 패턴 매칭
- 글로벌 변수 탐지
- 쿠키 패턴 매칭
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.thirdparty_detector import (
    CookieMatcher,
    GlobalVariableMatcher,
    ScriptPatternMatcher,
    ThirdPartyDetectorModule,
    ThirdPartyService,
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
def thirdparty_detector_module() -> ThirdPartyDetectorModule:
    """Create ThirdPartyDetectorModule instance."""
    return ThirdPartyDetectorModule()


@pytest.fixture
def script_matcher() -> ScriptPatternMatcher:
    """Create ScriptPatternMatcher instance."""
    return ScriptPatternMatcher()


@pytest.fixture
def global_var_matcher() -> GlobalVariableMatcher:
    """Create GlobalVariableMatcher instance."""
    return GlobalVariableMatcher()


@pytest.fixture
def cookie_matcher() -> CookieMatcher:
    """Create CookieMatcher instance."""
    return CookieMatcher()


# ============================================================================
# Test 1: ThirdPartyService 데이터 클래스
# ============================================================================


class TestThirdPartyServiceDataClass:
    """ThirdPartyService 데이터 클래스 테스트."""

    def test_thirdparty_service_creation(self) -> None:
        """ThirdPartyService 인스턴스 생성."""
        service = ThirdPartyService(
            name="Google Analytics",
            category="analytics",
            confidence=0.95,
            version="GA4",
            detected_by="script_src",
            metadata={"tracking_id": "G-XXXXXX"},
        )

        assert service.name == "Google Analytics"
        assert service.category == "analytics"
        assert service.confidence == 0.95
        assert service.version == "GA4"
        assert service.detected_by == "script_src"
        assert service.metadata["tracking_id"] == "G-XXXXXX"

    def test_thirdparty_service_default_values(self) -> None:
        """기본값 테스트."""
        service = ThirdPartyService(
            name="Unknown Service",
            category="other",
            confidence=0.5,
            detected_by="script_src",
        )

        assert service.version is None
        assert service.metadata == {}


# ============================================================================
# Test 2: Google Analytics 탐지
# ============================================================================


class TestGoogleAnalyticsDetection:
    """Google Analytics 탐지 테스트."""

    def test_gtag_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """gtag.js 스크립트 탐지."""
        scripts = [
            "https://www.googletagmanager.com/gtag/js?id=G-XXXXXX",
            "https://example.com/main.js",
        ]

        results = script_matcher.match(scripts)

        ga_results = [r for r in results if r.name == "Google Analytics"]
        assert len(ga_results) == 1
        assert ga_results[0].category == "analytics"
        assert ga_results[0].version == "GA4"
        assert ga_results[0].metadata.get("tracking_id") == "G-XXXXXX"

    def test_analytics_js_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """analytics.js (Universal Analytics) 탐지."""
        scripts = [
            "https://www.google-analytics.com/analytics.js",
        ]

        results = script_matcher.match(scripts)

        ga_results = [r for r in results if r.name == "Google Analytics"]
        assert len(ga_results) == 1
        assert ga_results[0].version == "Universal"

    def test_gtag_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """gtag 글로벌 변수 탐지."""
        global_vars = ["gtag", "dataLayer", "jQuery"]

        results = global_var_matcher.match(global_vars)

        ga_results = [r for r in results if r.name == "Google Analytics"]
        assert len(ga_results) >= 1

    def test_ga_cookie_detection(
        self,
        cookie_matcher: CookieMatcher,
    ) -> None:
        """_ga 쿠키 탐지."""
        cookies = ["_ga=GA1.2.123456789.1234567890", "_gid=GA1.2.987654321"]

        results = cookie_matcher.match(cookies)

        ga_results = [r for r in results if r.name == "Google Analytics"]
        assert len(ga_results) >= 1


# ============================================================================
# Test 3: Firebase 탐지
# ============================================================================


class TestFirebaseDetection:
    """Firebase 탐지 테스트."""

    def test_firebase_sdk_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Firebase SDK 스크립트 탐지."""
        scripts = [
            "https://www.gstatic.com/firebasejs/9.0.0/firebase-app.js",
            "https://www.gstatic.com/firebasejs/9.0.0/firebase-auth.js",
        ]

        results = script_matcher.match(scripts)

        firebase_results = [r for r in results if r.name == "Firebase"]
        assert len(firebase_results) >= 1
        assert firebase_results[0].category == "backend_service"
        assert "9.0.0" in (firebase_results[0].version or "")

    def test_firebaseio_domain_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """firebaseio.com 도메인 탐지."""
        scripts = [
            "https://myapp.firebaseio.com/data.json",
        ]

        results = script_matcher.match(scripts)

        firebase_results = [r for r in results if r.name == "Firebase"]
        assert len(firebase_results) == 1
        assert firebase_results[0].metadata.get("project_id") == "myapp"

    def test_firebase_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Firebase 글로벌 변수 탐지."""
        global_vars = ["firebase", "firebaseApp"]

        results = global_var_matcher.match(global_vars)

        firebase_results = [r for r in results if r.name == "Firebase"]
        assert len(firebase_results) >= 1


# ============================================================================
# Test 4: Stripe 탐지
# ============================================================================


class TestStripeDetection:
    """Stripe 탐지 테스트."""

    def test_stripe_js_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Stripe.js 스크립트 탐지."""
        scripts = [
            "https://js.stripe.com/v3/",
        ]

        results = script_matcher.match(scripts)

        stripe_results = [r for r in results if r.name == "Stripe"]
        assert len(stripe_results) == 1
        assert stripe_results[0].category == "payment"
        assert stripe_results[0].version == "v3"

    def test_stripe_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Stripe 글로벌 변수 탐지."""
        global_vars = ["Stripe", "StripeCheckout"]

        results = global_var_matcher.match(global_vars)

        stripe_results = [r for r in results if r.name == "Stripe"]
        assert len(stripe_results) >= 1


# ============================================================================
# Test 5: Sentry 탐지
# ============================================================================


class TestSentryDetection:
    """Sentry 탐지 테스트."""

    def test_sentry_sdk_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Sentry SDK 스크립트 탐지."""
        scripts = [
            "https://browser.sentry-cdn.com/7.0.0/bundle.min.js",
        ]

        results = script_matcher.match(scripts)

        sentry_results = [r for r in results if r.name == "Sentry"]
        assert len(sentry_results) == 1
        assert sentry_results[0].category == "monitoring"
        assert "7.0.0" in (sentry_results[0].version or "")

    def test_sentry_dsn_in_html_detection(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """HTML 내 Sentry DSN 탐지."""
        html_content = """
        <script>
            Sentry.init({
                dsn: 'https://abc123@o123456.ingest.sentry.io/789',
            });
        </script>
        """

        services = thirdparty_detector_module._detect_from_html(html_content)

        sentry_results = [s for s in services if s.name == "Sentry"]
        assert len(sentry_results) >= 1

    def test_sentry_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Sentry 글로벌 변수 탐지."""
        global_vars = ["Sentry", "__SENTRY__"]

        results = global_var_matcher.match(global_vars)

        sentry_results = [r for r in results if r.name == "Sentry"]
        assert len(sentry_results) >= 1


# ============================================================================
# Test 6: Auth0 탐지
# ============================================================================


class TestAuth0Detection:
    """Auth0 탐지 테스트."""

    def test_auth0_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Auth0.js 스크립트 탐지."""
        scripts = [
            "https://cdn.auth0.com/js/auth0/9.18/auth0.min.js",
        ]

        results = script_matcher.match(scripts)

        auth0_results = [r for r in results if r.name == "Auth0"]
        assert len(auth0_results) == 1
        assert auth0_results[0].category == "authentication"
        assert "9.18" in (auth0_results[0].version or "")

    def test_auth0_spa_sdk_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Auth0 SPA SDK 탐지."""
        scripts = [
            "https://cdn.auth0.com/js/auth0-spa-js/2.0/auth0-spa-js.production.js",
        ]

        results = script_matcher.match(scripts)

        auth0_results = [r for r in results if r.name == "Auth0"]
        assert len(auth0_results) == 1

    def test_auth0_domain_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Auth0 도메인 탐지."""
        scripts = [
            "https://myapp.auth0.com/authorize",
        ]

        results = script_matcher.match(scripts)

        auth0_results = [r for r in results if r.name == "Auth0"]
        assert len(auth0_results) == 1
        assert auth0_results[0].metadata.get("domain") == "myapp.auth0.com"

    def test_auth0_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Auth0 글로벌 변수 탐지."""
        global_vars = ["auth0", "Auth0", "Auth0Lock"]

        results = global_var_matcher.match(global_vars)

        auth0_results = [r for r in results if r.name == "Auth0"]
        assert len(auth0_results) >= 1


# ============================================================================
# Test 7: Mixpanel 탐지
# ============================================================================


class TestMixpanelDetection:
    """Mixpanel 탐지 테스트."""

    def test_mixpanel_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Mixpanel 스크립트 탐지."""
        scripts = [
            "https://cdn.mxpnl.com/libs/mixpanel-2-latest.min.js",
        ]

        results = script_matcher.match(scripts)

        mixpanel_results = [r for r in results if r.name == "Mixpanel"]
        assert len(mixpanel_results) == 1
        assert mixpanel_results[0].category == "analytics"

    def test_mixpanel_init_in_html_detection(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """HTML 내 mixpanel.init 탐지."""
        html_content = """
        <script>
            mixpanel.init('your_token_here');
        </script>
        """

        services = thirdparty_detector_module._detect_from_html(html_content)

        mixpanel_results = [s for s in services if s.name == "Mixpanel"]
        assert len(mixpanel_results) >= 1

    def test_mixpanel_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Mixpanel 글로벌 변수 탐지."""
        global_vars = ["mixpanel"]

        results = global_var_matcher.match(global_vars)

        mixpanel_results = [r for r in results if r.name == "Mixpanel"]
        assert len(mixpanel_results) >= 1

    def test_mixpanel_cookie_detection(
        self,
        cookie_matcher: CookieMatcher,
    ) -> None:
        """Mixpanel 쿠키 탐지."""
        cookies = ["mp_token_mixpanel=xxx"]

        results = cookie_matcher.match(cookies)

        mixpanel_results = [r for r in results if r.name == "Mixpanel"]
        assert len(mixpanel_results) >= 1


# ============================================================================
# Test 8: Intercom 탐지
# ============================================================================


class TestIntercomDetection:
    """Intercom 탐지 테스트."""

    def test_intercom_script_detection(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """Intercom 스크립트 탐지."""
        scripts = [
            "https://widget.intercom.io/widget/abc123",
        ]

        results = script_matcher.match(scripts)

        intercom_results = [r for r in results if r.name == "Intercom"]
        assert len(intercom_results) == 1
        assert intercom_results[0].category == "customer_support"
        assert intercom_results[0].metadata.get("app_id") == "abc123"

    def test_intercom_messenger_in_html_detection(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """HTML 내 Intercom 메신저 탐지."""
        html_content = """
        <script>
            window.Intercom("boot", {
                app_id: "abc123",
            });
        </script>
        """

        services = thirdparty_detector_module._detect_from_html(html_content)

        intercom_results = [s for s in services if s.name == "Intercom"]
        assert len(intercom_results) >= 1

    def test_intercom_global_variable_detection(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """Intercom 글로벌 변수 탐지."""
        global_vars = ["Intercom", "intercomSettings"]

        results = global_var_matcher.match(global_vars)

        intercom_results = [r for r in results if r.name == "Intercom"]
        assert len(intercom_results) >= 1


# ============================================================================
# Test 9: 복합 서비스 탐지
# ============================================================================


class TestMultipleServicesDetection:
    """복합 서비스 탐지 테스트."""

    async def test_detect_multiple_services(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """여러 서비스 동시 탐지."""
        crawl_data = {
            "scripts": [
                "https://www.googletagmanager.com/gtag/js?id=G-XXXXXX",
                "https://js.stripe.com/v3/",
                "https://browser.sentry-cdn.com/7.0.0/bundle.min.js",
            ],
            "cookies": ["_ga=GA1.2.123456789"],
            "global_variables": ["gtag", "Stripe", "Sentry"],
            "html_content": "<html></html>",
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in thirdparty_detector_module.discover(context)]

        # 중복 제거 후에도 최소 3개 서비스 탐지
        service_names = {a.metadata.get("service_name") for a in assets}
        assert "Google Analytics" in service_names
        assert "Stripe" in service_names
        assert "Sentry" in service_names

    async def test_no_duplicate_assets(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """중복 자산 제거 테스트."""
        crawl_data = {
            "scripts": [
                "https://www.googletagmanager.com/gtag/js?id=G-XXXXXX",
            ],
            "cookies": ["_ga=GA1.2.123456789"],
            "global_variables": ["gtag", "dataLayer"],
            "html_content": "<script>window.gtag = function() {};</script>",
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in thirdparty_detector_module.discover(context)]

        # Google Analytics는 한 번만 나와야 함
        ga_assets = [
            a for a in assets if a.metadata.get("service_name") == "Google Analytics"
        ]
        assert len(ga_assets) == 1


# ============================================================================
# Test 10: 모듈 속성 및 프로필 테스트
# ============================================================================


class TestModulePropertiesAndProfiles:
    """모듈 속성 및 프로필 테스트."""

    def test_module_name(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """모듈 이름 테스트."""
        assert thirdparty_detector_module.name == "thirdparty_detector"

    def test_module_profiles(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """지원 프로필 테스트."""
        profiles = thirdparty_detector_module.profiles
        assert ScanProfile.STANDARD in profiles
        assert ScanProfile.FULL in profiles
        assert ScanProfile.QUICK not in profiles

    def test_is_active_for_standard_profile(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """STANDARD 프로필 활성화 테스트."""
        assert thirdparty_detector_module.is_active_for(ScanProfile.STANDARD) is True

    def test_is_not_active_for_quick_profile(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
    ) -> None:
        """QUICK 프로필 비활성화 테스트."""
        assert thirdparty_detector_module.is_active_for(ScanProfile.QUICK) is False


# ============================================================================
# Test 11: 빈 데이터 처리
# ============================================================================


class TestEmptyDataHandling:
    """빈 데이터 처리 테스트."""

    async def test_empty_crawl_data(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 crawl_data 처리."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={},
        )

        assets = [asset async for asset in thirdparty_detector_module.discover(context)]

        assert assets == []

    def test_empty_scripts_list(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """빈 스크립트 리스트 처리."""
        results = script_matcher.match([])
        assert results == []

    def test_empty_cookies_list(
        self,
        cookie_matcher: CookieMatcher,
    ) -> None:
        """빈 쿠키 리스트 처리."""
        results = cookie_matcher.match([])
        assert results == []

    def test_empty_global_vars_list(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """빈 글로벌 변수 리스트 처리."""
        results = global_var_matcher.match([])
        assert results == []


# ============================================================================
# Test 12: DiscoveredAsset 출력 형식 테스트
# ============================================================================


class TestDiscoveredAssetFormat:
    """DiscoveredAsset 출력 형식 테스트."""

    async def test_asset_format(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """DiscoveredAsset 형식 검증."""
        crawl_data = {
            "scripts": ["https://www.googletagmanager.com/gtag/js?id=G-XXXXXX"],
            "cookies": [],
            "global_variables": [],
            "html_content": "",
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in thirdparty_detector_module.discover(context)]

        assert len(assets) > 0
        asset = assets[0]

        # 필수 필드 검증
        assert isinstance(asset, DiscoveredAsset)
        assert asset.asset_type == "thirdparty_service"
        assert asset.source == "thirdparty_detector"
        assert "service_name" in asset.metadata
        assert "category" in asset.metadata
        assert "confidence" in asset.metadata
        assert "detected_by" in asset.metadata

    async def test_asset_url_format(
        self,
        thirdparty_detector_module: ThirdPartyDetectorModule,
        mock_http_client: MagicMock,
    ) -> None:
        """Asset URL 형식 검증."""
        crawl_data = {
            "scripts": ["https://js.stripe.com/v3/"],
            "cookies": [],
            "global_variables": [],
            "html_content": "",
        }

        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data=crawl_data,
        )

        assets = [asset async for asset in thirdparty_detector_module.discover(context)]

        stripe_asset = [
            a for a in assets if a.metadata.get("service_name") == "Stripe"
        ][0]
        assert stripe_asset.url == "https://js.stripe.com/v3/"


# ============================================================================
# Test 13: 신뢰도 레벨 테스트
# ============================================================================


class TestConfidenceLevels:
    """신뢰도 레벨 테스트."""

    def test_script_src_high_confidence(
        self,
        script_matcher: ScriptPatternMatcher,
    ) -> None:
        """스크립트 소스 탐지는 높은 신뢰도."""
        scripts = ["https://www.googletagmanager.com/gtag/js?id=G-XXXXXX"]
        results = script_matcher.match(scripts)

        assert len(results) > 0
        assert results[0].confidence >= 0.9

    def test_global_var_medium_confidence(
        self,
        global_var_matcher: GlobalVariableMatcher,
    ) -> None:
        """글로벌 변수 탐지는 중간 신뢰도."""
        global_vars = ["gtag"]
        results = global_var_matcher.match(global_vars)

        assert len(results) > 0
        assert 0.6 <= results[0].confidence <= 0.85

    def test_cookie_medium_confidence(
        self,
        cookie_matcher: CookieMatcher,
    ) -> None:
        """쿠키 탐지는 중간 신뢰도."""
        cookies = ["_ga=GA1.2.123456789"]
        results = cookie_matcher.match(cookies)

        assert len(results) > 0
        assert 0.6 <= results[0].confidence <= 0.85
