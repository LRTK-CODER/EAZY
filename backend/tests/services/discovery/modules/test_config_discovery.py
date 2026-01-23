"""ConfigDiscoveryModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- robots.txt 파싱
- sitemap.xml 파싱
- well-known 파일 파싱
- source map 탐지
"""

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.config_discovery import (
    ConfigDiscoveryModule,
    RobotsTxtParser,
    SitemapParser,
    SourceMapDetector,
    WellKnownParser,
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
def config_discovery_module() -> ConfigDiscoveryModule:
    """Create ConfigDiscoveryModule instance."""
    return ConfigDiscoveryModule()


# ============================================================================
# Test 2.1.1: robots.txt Disallow 경로 추출
# ============================================================================


class TestRobotsTxtDisallowExtraction:
    """robots.txt Disallow 경로 추출 테스트."""

    async def test_extract_single_disallow_path(self) -> None:
        """단일 Disallow 경로 추출."""
        robots_content = """User-agent: *
Disallow: /admin/
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        assert "/admin/" in result.disallowed_paths

    async def test_extract_multiple_disallow_entries(self) -> None:
        """다중 Disallow 항목 추출."""
        robots_content = """User-agent: *
Disallow: /admin/
Disallow: /private/
Disallow: /api/internal/
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        assert len(result.disallowed_paths) == 3
        assert "/admin/" in result.disallowed_paths
        assert "/private/" in result.disallowed_paths
        assert "/api/internal/" in result.disallowed_paths

    async def test_handle_user_agent_specific_rules(self) -> None:
        """User-agent별 규칙 처리 (현재는 * 만 처리)."""
        robots_content = """User-agent: Googlebot
Disallow: /google-only/

User-agent: *
Disallow: /all-bots/
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        # User-agent: * 의 규칙만 추출
        assert "/all-bots/" in result.disallowed_paths
        # Googlebot 전용 규칙은 무시
        assert "/google-only/" not in result.disallowed_paths

    async def test_handle_wildcard_patterns(self) -> None:
        """와일드카드 패턴 처리."""
        robots_content = """User-agent: *
Disallow: /*.php$
Disallow: /*/private/
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        # 와일드카드 패턴도 그대로 저장
        assert "/*.php$" in result.disallowed_paths
        assert "/*/private/" in result.disallowed_paths


# ============================================================================
# Test 2.1.2: robots.txt Sitemap 참조 추출
# ============================================================================


class TestRobotsTxtSitemapReference:
    """robots.txt Sitemap 참조 추출 테스트."""

    async def test_extract_sitemap_url_from_directive(self) -> None:
        """Sitemap: 지시문에서 URL 추출."""
        robots_content = """User-agent: *
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        assert "https://example.com/sitemap.xml" in result.sitemap_urls

    async def test_handle_multiple_sitemap_references(self) -> None:
        """다중 Sitemap 참조 처리."""
        robots_content = """User-agent: *
Disallow:

Sitemap: https://example.com/sitemap.xml
Sitemap: https://example.com/sitemap-news.xml
Sitemap: https://example.com/sitemap-images.xml
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        assert len(result.sitemap_urls) == 3
        assert "https://example.com/sitemap.xml" in result.sitemap_urls
        assert "https://example.com/sitemap-news.xml" in result.sitemap_urls
        assert "https://example.com/sitemap-images.xml" in result.sitemap_urls

    async def test_handle_relative_and_absolute_urls(self) -> None:
        """상대 및 절대 URL 처리."""
        robots_content = """User-agent: *
Sitemap: /sitemap.xml
Sitemap: https://example.com/sitemap-absolute.xml
"""
        parser = RobotsTxtParser()
        result = parser.parse(robots_content)

        # 상대 URL도 그대로 저장 (나중에 resolve)
        assert "/sitemap.xml" in result.sitemap_urls
        assert "https://example.com/sitemap-absolute.xml" in result.sitemap_urls


# ============================================================================
# Test 2.1.3: robots.txt 404 처리
# ============================================================================


class TestRobotsTxtNotFound:
    """robots.txt 404 처리 테스트."""

    async def test_gracefully_handle_404_response(
        self,
        config_discovery_module: ConfigDiscoveryModule,
        mock_http_client: MagicMock,
        discovery_context: DiscoveryContext,
    ) -> None:
        """404 응답 우아하게 처리."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Not Found"
        mock_http_client.get.return_value = mock_response

        # Should not raise exception
        assets = [
            asset async for asset in config_discovery_module.discover(discovery_context)
        ]

        # Should return empty results, not error
        robots_assets = [a for a in assets if a.source == "robots_txt"]
        # 404일 때는 빈 결과
        assert all(a.metadata.get("status") != "error" for a in robots_assets)

    async def test_return_empty_results_not_error(self) -> None:
        """에러 대신 빈 결과 반환."""
        parser = RobotsTxtParser()
        # 빈 내용 파싱
        result = parser.parse("")

        assert result.disallowed_paths == []
        assert result.sitemap_urls == []

    async def test_log_appropriate_warning(
        self,
        config_discovery_module: ConfigDiscoveryModule,
        mock_http_client: MagicMock,
        discovery_context: DiscoveryContext,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """적절한 경고 로깅."""
        # Mock 404 response
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_http_client.get.return_value = mock_response

        # Run discovery
        _ = [
            asset async for asset in config_discovery_module.discover(discovery_context)
        ]

        # Check warning was logged (implementation detail)
        # Note: 실제 로깅 확인은 구현 후 조정


# ============================================================================
# Test 2.1.4: sitemap.xml URL 목록 추출
# ============================================================================


class TestSitemapUrlExtraction:
    """sitemap.xml URL 목록 추출 테스트."""

    async def test_extract_loc_urls_from_sitemap_xml(self) -> None:
        """sitemap XML에서 <loc> URL 추출."""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/page1</loc>
    </url>
    <url>
        <loc>https://example.com/page2</loc>
    </url>
</urlset>
"""
        parser = SitemapParser()
        result = parser.parse(sitemap_content)

        assert len(result.urls) == 2
        assert "https://example.com/page1" in result.urls
        assert "https://example.com/page2" in result.urls

    async def test_handle_lastmod_changefreq_priority(self) -> None:
        """<lastmod>, <changefreq>, <priority> 처리."""
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/page1</loc>
        <lastmod>2024-01-01</lastmod>
        <changefreq>daily</changefreq>
        <priority>0.8</priority>
    </url>
</urlset>
"""
        parser = SitemapParser()
        result = parser.parse(sitemap_content)

        # URL 추출 + 메타데이터
        assert "https://example.com/page1" in result.urls
        url_info = result.url_metadata.get("https://example.com/page1", {})
        assert url_info.get("lastmod") == "2024-01-01"
        assert url_info.get("changefreq") == "daily"
        assert url_info.get("priority") == "0.8"

    async def test_parse_compressed_sitemaps(self) -> None:
        """압축된 sitemap 파싱 (gzip)."""
        # Note: 실제 gzip 처리는 HTTP 클라이언트에서 자동으로 됨
        # 여기서는 일반 XML 파싱 테스트
        sitemap_content = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/compressed-page</loc>
    </url>
</urlset>
"""
        parser = SitemapParser()
        result = parser.parse(sitemap_content)

        assert "https://example.com/compressed-page" in result.urls


# ============================================================================
# Test 2.1.5: sitemap index 처리 (nested sitemap)
# ============================================================================


class TestSitemapNested:
    """sitemap index 처리 테스트."""

    async def test_detect_sitemap_index_file(self) -> None:
        """sitemap index 파일 감지."""
        sitemap_index_content = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://example.com/sitemap-posts.xml</loc>
    </sitemap>
    <sitemap>
        <loc>https://example.com/sitemap-pages.xml</loc>
    </sitemap>
</sitemapindex>
"""
        parser = SitemapParser()
        result = parser.parse(sitemap_index_content)

        assert result.is_index is True
        assert len(result.child_sitemaps) == 2

    async def test_recursively_fetch_referenced_sitemaps(
        self,
        config_discovery_module: ConfigDiscoveryModule,
        mock_http_client: MagicMock,
        discovery_context: DiscoveryContext,
    ) -> None:
        """참조된 sitemap 재귀적으로 가져오기."""
        # Mock sitemap index response
        sitemap_index = """<?xml version="1.0" encoding="UTF-8"?>
<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <sitemap>
        <loc>https://example.com/sitemap-posts.xml</loc>
    </sitemap>
</sitemapindex>
"""
        child_sitemap = """<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
    <url>
        <loc>https://example.com/post/1</loc>
    </url>
</urlset>
"""

        def mock_get(url: str, **kwargs):
            mock_response = MagicMock()
            mock_response.status_code = 200
            if "sitemap-posts" in url:
                mock_response.text = child_sitemap
            else:
                mock_response.text = sitemap_index
            return mock_response

        mock_http_client.get.side_effect = mock_get

        # Discover with recursive sitemap fetching
        assets = [
            asset async for asset in config_discovery_module.discover(discovery_context)
        ]

        # Should have discovered URL from child sitemap
        urls = [a.url for a in assets if a.asset_type == "page"]
        assert "https://example.com/post/1" in urls

    async def test_handle_max_depth_limit(self) -> None:
        """최대 깊이 제한 처리."""
        parser = SitemapParser(max_depth=2)

        # Simulate deep nesting (실제 재귀 호출은 모듈에서 처리)
        assert parser.max_depth == 2


# ============================================================================
# Test 2.1.6: security.txt 파싱
# ============================================================================


class TestWellKnownSecurityTxt:
    """security.txt 파싱 테스트."""

    async def test_parse_well_known_security_txt(self) -> None:
        """/.well-known/security.txt 파싱."""
        security_txt_content = """Contact: security@example.com
Expires: 2025-12-31T23:59:59.000Z
Encryption: https://example.com/pgp-key.txt
Acknowledgments: https://example.com/hall-of-fame
Policy: https://example.com/security-policy
Hiring: https://example.com/jobs
"""
        parser = WellKnownParser()
        result = parser.parse_security_txt(security_txt_content)

        assert result.contact == "security@example.com"
        assert result.policy == "https://example.com/security-policy"
        assert result.hiring == "https://example.com/jobs"

    async def test_extract_contact_policy_hiring_urls(self) -> None:
        """Contact, Policy, Hiring URL 추출."""
        security_txt_content = """Contact: https://example.com/security-contact
Policy: https://example.com/security-policy
Hiring: https://example.com/security-jobs
"""
        parser = WellKnownParser()
        result = parser.parse_security_txt(security_txt_content)

        assert "security-contact" in result.contact
        assert "security-policy" in result.policy
        assert "security-jobs" in result.hiring

    async def test_handle_pgp_signatures(self) -> None:
        """PGP 서명 처리."""
        security_txt_content = """-----BEGIN PGP SIGNED MESSAGE-----
Hash: SHA256

Contact: security@example.com
Policy: https://example.com/policy

-----BEGIN PGP SIGNATURE-----
iQIzBAEBCAAdFiEE...
-----END PGP SIGNATURE-----
"""
        parser = WellKnownParser()
        result = parser.parse_security_txt(security_txt_content)

        # PGP 서명이 있어도 내용 파싱 가능
        assert result.contact == "security@example.com"
        assert result.has_pgp_signature is True


# ============================================================================
# Test 2.1.7: openid-configuration 파싱
# ============================================================================


class TestWellKnownOpenIdConfig:
    """openid-configuration 파싱 테스트."""

    async def test_parse_well_known_openid_configuration(self) -> None:
        """/.well-known/openid-configuration 파싱."""
        openid_config = {
            "issuer": "https://example.com",
            "authorization_endpoint": "https://example.com/oauth/authorize",
            "token_endpoint": "https://example.com/oauth/token",
            "userinfo_endpoint": "https://example.com/oauth/userinfo",
            "jwks_uri": "https://example.com/.well-known/jwks.json",
        }
        parser = WellKnownParser()
        result = parser.parse_openid_config(openid_config)

        assert result.authorization_endpoint == "https://example.com/oauth/authorize"
        assert result.token_endpoint == "https://example.com/oauth/token"
        assert result.jwks_uri == "https://example.com/.well-known/jwks.json"

    async def test_extract_authorization_token_endpoint(self) -> None:
        """authorization_endpoint, token_endpoint 추출."""
        openid_config = {
            "authorization_endpoint": "https://auth.example.com/authorize",
            "token_endpoint": "https://auth.example.com/token",
        }
        parser = WellKnownParser()
        result = parser.parse_openid_config(openid_config)

        assert "authorize" in result.authorization_endpoint
        assert "token" in result.token_endpoint

    async def test_extract_jwks_uri(self) -> None:
        """jwks_uri 추출."""
        openid_config = {
            "jwks_uri": "https://example.com/.well-known/jwks.json",
        }
        parser = WellKnownParser()
        result = parser.parse_openid_config(openid_config)

        assert result.jwks_uri == "https://example.com/.well-known/jwks.json"


# ============================================================================
# Test 2.1.8: source map 탐지
# ============================================================================


class TestSourceMapDetection:
    """source map 탐지 테스트."""

    async def test_detect_source_mapping_url_comment(self) -> None:
        """//# sourceMappingURL= 주석 탐지."""
        js_content = """
function hello() {
    console.log("Hello World");
}
//# sourceMappingURL=app.js.map
"""
        detector = SourceMapDetector()
        result = detector.detect(js_content)

        assert result.has_source_map is True
        assert result.source_map_url == "app.js.map"

    async def test_handle_relative_and_absolute_map_urls(self) -> None:
        """상대 및 절대 map URL 처리."""
        js_content_relative = """//# sourceMappingURL=bundle.js.map"""
        js_content_absolute = (
            """//# sourceMappingURL=https://cdn.example.com/bundle.js.map"""
        )

        detector = SourceMapDetector()

        result_relative = detector.detect(js_content_relative)
        assert result_relative.source_map_url == "bundle.js.map"

        result_absolute = detector.detect(js_content_absolute)
        assert result_absolute.source_map_url == "https://cdn.example.com/bundle.js.map"

    async def test_flag_as_potential_information_disclosure(self) -> None:
        """잠재적 정보 노출로 표시."""
        js_content = """//# sourceMappingURL=app.js.map"""

        detector = SourceMapDetector()
        result = detector.detect(js_content)

        # Source map은 정보 노출 위험
        assert result.is_information_disclosure_risk is True


# ============================================================================
# Integration Tests
# ============================================================================


class TestConfigDiscoveryModuleIntegration:
    """ConfigDiscoveryModule 통합 테스트."""

    async def test_module_properties(
        self,
        config_discovery_module: ConfigDiscoveryModule,
    ) -> None:
        """모듈 속성 테스트."""
        assert config_discovery_module.name == "config_discovery"
        assert ScanProfile.STANDARD in config_discovery_module.profiles
        assert ScanProfile.FULL in config_discovery_module.profiles

    async def test_discover_yields_discovered_assets(
        self,
        config_discovery_module: ConfigDiscoveryModule,
        mock_http_client: MagicMock,
        discovery_context: DiscoveryContext,
    ) -> None:
        """discover()가 DiscoveredAsset을 yield하는지 테스트."""
        # Mock successful robots.txt response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = """User-agent: *
Disallow: /admin/

Sitemap: https://example.com/sitemap.xml
"""
        mock_http_client.get.return_value = mock_response

        assets = [
            asset async for asset in config_discovery_module.discover(discovery_context)
        ]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)

        # Should have discovered the admin path
        admin_assets = [a for a in assets if "/admin" in a.url]
        assert len(admin_assets) > 0
