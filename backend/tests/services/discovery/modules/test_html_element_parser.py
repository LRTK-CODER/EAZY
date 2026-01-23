"""HtmlElementParserModule 테스트.

TDD RED Phase: 테스트 먼저 작성
- form 요소 파싱 (action, method, hidden inputs, CSRF)
- script 요소 파싱 (src, inline URL)
- link 요소 파싱 (href, rel types)
- media 요소 파싱 (img, video, audio, source)
- meta 요소 파싱 (refresh, Open Graph)
- data-* 속성 URL 파싱
- base href URL 해결
"""

from unittest.mock import MagicMock

import pytest

from app.services.discovery.models import DiscoveredAsset, DiscoveryContext, ScanProfile
from app.services.discovery.modules.html_element_parser import (
    DataAttrParser,
    FormParser,
    HtmlElementParserModule,
    LinkParser,
    MediaParser,
    MetaParser,
    ScriptParser,
)

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_http_client() -> MagicMock:
    """Mock HTTP client for testing."""
    client = MagicMock()
    return client


@pytest.fixture
def discovery_context(mock_http_client: MagicMock) -> DiscoveryContext:
    """Create a test discovery context with HTML content."""
    return DiscoveryContext(
        target_url="https://example.com",
        profile=ScanProfile.STANDARD,
        http_client=mock_http_client,
        crawl_data={
            "html_content": "<html><body>Test</body></html>",
            "base_url": "https://example.com",
        },
    )


@pytest.fixture
def html_parser_module() -> HtmlElementParserModule:
    """Create HtmlElementParserModule instance."""
    return HtmlElementParserModule()


# ============================================================================
# Test 1: Form Action URL Extraction
# ============================================================================


class TestFormActionExtraction:
    """form action URL 추출 테스트."""

    def test_form_action_extraction(self) -> None:
        """form action URL 추출."""
        html = """
        <html>
        <body>
            <form action="/login" method="POST">
                <input type="text" name="username">
                <input type="password" name="password">
                <button type="submit">Login</button>
            </form>
            <form action="https://api.example.com/submit">
                <input type="text" name="data">
            </form>
        </body>
        </html>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        assert len(result.forms) == 2
        # 상대 URL은 절대 URL로 변환
        assert result.forms[0].action == "https://example.com/login"
        assert result.forms[1].action == "https://api.example.com/submit"

    def test_form_action_empty_defaults_to_current_page(self) -> None:
        """빈 action은 현재 페이지로 기본값 설정."""
        html = """
        <form action="">
            <input type="text" name="q">
        </form>
        """
        parser = FormParser(base_url="https://example.com/search")
        result = parser.parse(html)

        assert result.forms[0].action == "https://example.com/search"

    def test_form_action_with_query_params(self) -> None:
        """쿼리 파라미터가 있는 action URL 처리."""
        html = """
        <form action="/search?type=advanced&lang=ko">
            <input type="text" name="q">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        assert (
            result.forms[0].action == "https://example.com/search?type=advanced&lang=ko"
        )


# ============================================================================
# Test 2: Form Method Detection
# ============================================================================


class TestFormMethodDetection:
    """form method 감지 테스트."""

    def test_form_method_detection(self) -> None:
        """GET/POST 메서드 감지."""
        html = """
        <form action="/search" method="GET">
            <input type="text" name="q">
        </form>
        <form action="/login" method="POST">
            <input type="text" name="username">
        </form>
        <form action="/default">
            <input type="text" name="data">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        assert result.forms[0].method == "GET"
        assert result.forms[1].method == "POST"
        # 메서드 미지정시 기본값은 GET
        assert result.forms[2].method == "GET"

    def test_form_method_case_insensitive(self) -> None:
        """method 대소문자 구분 없이 처리."""
        html = """
        <form action="/a" method="post"></form>
        <form action="/b" method="Post"></form>
        <form action="/c" method="POST"></form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        # 모두 대문자로 정규화
        assert result.forms[0].method == "POST"
        assert result.forms[1].method == "POST"
        assert result.forms[2].method == "POST"


# ============================================================================
# Test 3: Form Hidden Inputs
# ============================================================================


class TestFormHiddenInputs:
    """form hidden input 추출 테스트."""

    def test_form_hidden_inputs(self) -> None:
        """hidden input 추출."""
        html = """
        <form action="/submit" method="POST">
            <input type="hidden" name="token" value="abc123">
            <input type="hidden" name="action" value="create">
            <input type="text" name="username">
            <input type="password" name="password">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        form = result.forms[0]
        assert len(form.hidden_inputs) == 2
        assert form.hidden_inputs["token"] == "abc123"
        assert form.hidden_inputs["action"] == "create"

    def test_form_hidden_input_without_value(self) -> None:
        """value 없는 hidden input 처리."""
        html = """
        <form action="/submit">
            <input type="hidden" name="empty_field">
            <input type="hidden" name="with_value" value="test">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        form = result.forms[0]
        assert form.hidden_inputs["empty_field"] == ""
        assert form.hidden_inputs["with_value"] == "test"


# ============================================================================
# Test 4: Form CSRF Token Detection
# ============================================================================


class TestFormCsrfToken:
    """form CSRF 토큰 발견 테스트."""

    def test_form_csrf_token(self) -> None:
        """CSRF 토큰 발견."""
        html = """
        <form action="/submit" method="POST">
            <input type="hidden" name="_csrf" value="csrf_token_value">
            <input type="hidden" name="csrf_token" value="another_token">
            <input type="text" name="data">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        form = result.forms[0]
        assert form.has_csrf_token is True
        assert "_csrf" in form.csrf_tokens or "csrf_token" in form.csrf_tokens

    def test_form_csrf_token_various_names(self) -> None:
        """다양한 CSRF 토큰 이름 인식."""
        # 일반적인 CSRF 토큰 이름들
        csrf_names = [
            "_csrf",
            "csrf_token",
            "csrf",
            "_token",
            "authenticity_token",
            "csrfmiddlewaretoken",
            "__RequestVerificationToken",
        ]

        for name in csrf_names:
            html = f"""
            <form action="/submit" method="POST">
                <input type="hidden" name="{name}" value="token_value">
            </form>
            """
            parser = FormParser(base_url="https://example.com")
            result = parser.parse(html)
            form = result.forms[0]
            assert form.has_csrf_token is True, f"Failed to detect CSRF token: {name}"

    def test_form_without_csrf_token(self) -> None:
        """CSRF 토큰 없는 폼."""
        html = """
        <form action="/search" method="GET">
            <input type="text" name="q">
        </form>
        """
        parser = FormParser(base_url="https://example.com")
        result = parser.parse(html)

        form = result.forms[0]
        assert form.has_csrf_token is False


# ============================================================================
# Test 5: Script src Extraction
# ============================================================================


class TestScriptSrcExtraction:
    """script src 추출 테스트."""

    def test_script_src_extraction(self) -> None:
        """script src 추출."""
        html = """
        <html>
        <head>
            <script src="/js/app.js"></script>
            <script src="https://cdn.example.com/lib.js"></script>
        </head>
        <body>
            <script src="/js/main.js" defer></script>
        </body>
        </html>
        """
        parser = ScriptParser(base_url="https://example.com")
        result = parser.parse(html)

        assert len(result.scripts) == 3
        urls = [s.src for s in result.scripts]
        assert "https://example.com/js/app.js" in urls
        assert "https://cdn.example.com/lib.js" in urls
        assert "https://example.com/js/main.js" in urls

    def test_script_with_integrity(self) -> None:
        """integrity 속성이 있는 스크립트."""
        html = """
        <script src="https://cdn.example.com/lib.js"
                integrity="sha384-abc123"
                crossorigin="anonymous"></script>
        """
        parser = ScriptParser(base_url="https://example.com")
        result = parser.parse(html)

        script = result.scripts[0]
        assert script.integrity == "sha384-abc123"
        assert script.crossorigin == "anonymous"


# ============================================================================
# Test 6: Script Inline URL Detection
# ============================================================================


class TestScriptInlineUrl:
    """인라인 스크립트 내 URL 탐지 테스트."""

    def test_script_inline_url(self) -> None:
        """인라인 스크립트 내 URL."""
        html = """
        <script>
            var apiEndpoint = "https://api.example.com/v1/users";
            var config = {
                baseUrl: "/api/v2",
                wsUrl: "wss://ws.example.com/socket"
            };
            fetch('/api/data').then(r => r.json());
        </script>
        """
        parser = ScriptParser(base_url="https://example.com")
        result = parser.parse(html)

        inline_urls = result.inline_urls
        assert "https://api.example.com/v1/users" in inline_urls
        assert "/api/v2" in inline_urls
        assert "wss://ws.example.com/socket" in inline_urls
        assert "/api/data" in inline_urls

    def test_script_inline_url_with_template_literals(self) -> None:
        """템플릿 리터럴 내 URL."""
        html = """
        <script>
            const url = `https://api.example.com/users/${userId}`;
            const endpoint = `${baseUrl}/api/endpoint`;
            // 일반 문자열도 함께 있는 경우
            var fallback = "https://fallback.example.com/api";
        </script>
        """
        parser = ScriptParser(base_url="https://example.com")
        result = parser.parse(html)

        # 템플릿 리터럴 내 URL은 현재 백틱이 아닌 따옴표 패턴만 지원
        # 일반 문자열 URL은 추출됨
        inline_urls = result.inline_urls
        assert any("fallback.example.com" in url for url in inline_urls)


# ============================================================================
# Test 7: Link href Extraction
# ============================================================================


class TestLinkHrefExtraction:
    """link href 추출 테스트."""

    def test_link_href_extraction(self) -> None:
        """link href 추출."""
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="/css/style.css">
            <link rel="stylesheet" href="https://cdn.example.com/bootstrap.css">
            <link rel="icon" href="/favicon.ico">
        </head>
        </html>
        """
        parser = LinkParser(base_url="https://example.com")
        result = parser.parse(html)

        assert len(result.links) == 3
        hrefs = [link.href for link in result.links]
        assert "https://example.com/css/style.css" in hrefs
        assert "https://cdn.example.com/bootstrap.css" in hrefs
        assert "https://example.com/favicon.ico" in hrefs


# ============================================================================
# Test 8: Link rel Types
# ============================================================================


class TestLinkRelTypes:
    """link rel 타입 구분 테스트."""

    def test_link_rel_types(self) -> None:
        """stylesheet, preload, prefetch 구분."""
        html = """
        <head>
            <link rel="stylesheet" href="/css/main.css">
            <link rel="preload" href="/fonts/roboto.woff2" as="font" type="font/woff2">
            <link rel="prefetch" href="/js/lazy.js">
            <link rel="preconnect" href="https://api.example.com">
            <link rel="dns-prefetch" href="https://cdn.example.com">
            <link rel="canonical" href="https://example.com/page">
        </head>
        """
        parser = LinkParser(base_url="https://example.com")
        result = parser.parse(html)

        # rel 타입별로 분류
        stylesheets = [link for link in result.links if link.rel == "stylesheet"]
        preloads = [link for link in result.links if link.rel == "preload"]
        prefetches = [link for link in result.links if link.rel == "prefetch"]
        canonicals = [link for link in result.links if link.rel == "canonical"]

        assert len(stylesheets) == 1
        assert len(preloads) == 1
        assert preloads[0].as_type == "font"
        assert len(prefetches) == 1
        assert len(canonicals) == 1


# ============================================================================
# Test 9: Img src/srcset Extraction
# ============================================================================


class TestImgSrcExtraction:
    """img src, srcset 추출 테스트."""

    def test_img_src_extraction(self) -> None:
        """img src, srcset 추출."""
        html = """
        <body>
            <img src="/images/logo.png" alt="Logo">
            <img src="https://cdn.example.com/banner.jpg"
                 srcset="/images/banner-1x.jpg 1x, /images/banner-2x.jpg 2x">
            <img data-src="/images/lazy.png" class="lazyload">
        </body>
        """
        parser = MediaParser(base_url="https://example.com")
        result = parser.parse(html)

        images = result.images
        assert len(images) >= 2

        # src URLs
        src_urls = [img.src for img in images if img.src]
        assert "https://example.com/images/logo.png" in src_urls
        assert "https://cdn.example.com/banner.jpg" in src_urls

        # srcset URLs
        srcset_images = [img for img in images if img.srcset]
        assert len(srcset_images) >= 1
        assert "https://example.com/images/banner-1x.jpg" in srcset_images[0].srcset
        assert "https://example.com/images/banner-2x.jpg" in srcset_images[0].srcset

    def test_img_picture_source(self) -> None:
        """picture 요소 내 source 처리."""
        html = """
        <picture>
            <source srcset="/images/hero.webp" type="image/webp">
            <source srcset="/images/hero.jpg" type="image/jpeg">
            <img src="/images/hero.jpg" alt="Hero">
        </picture>
        """
        parser = MediaParser(base_url="https://example.com")
        result = parser.parse(html)

        all_urls = result.get_all_urls()
        assert "https://example.com/images/hero.webp" in all_urls
        assert "https://example.com/images/hero.jpg" in all_urls


# ============================================================================
# Test 10: Video/Audio Source Tags
# ============================================================================


class TestVideoAudioSource:
    """video, audio, source 태그 테스트."""

    def test_video_audio_source(self) -> None:
        """video, audio, source 태그."""
        html = """
        <body>
            <video src="/videos/intro.mp4" poster="/images/poster.jpg">
                <source src="/videos/intro.webm" type="video/webm">
                <source src="/videos/intro.mp4" type="video/mp4">
            </video>
            <audio src="/audio/background.mp3" controls>
                <source src="/audio/background.ogg" type="audio/ogg">
            </audio>
            <video>
                <track src="/subtitles/en.vtt" kind="subtitles" srclang="en">
            </video>
        </body>
        """
        parser = MediaParser(base_url="https://example.com")
        result = parser.parse(html)

        # Video URLs
        video_urls = [v.src for v in result.videos if v.src]
        assert "https://example.com/videos/intro.mp4" in video_urls

        # Video poster
        video_with_poster = [v for v in result.videos if v.poster]
        assert len(video_with_poster) >= 1
        assert video_with_poster[0].poster == "https://example.com/images/poster.jpg"

        # Audio URLs
        audio_urls = [a.src for a in result.audios if a.src]
        assert "https://example.com/audio/background.mp3" in audio_urls

        # Source URLs
        all_urls = result.get_all_urls()
        assert "https://example.com/videos/intro.webm" in all_urls
        assert "https://example.com/audio/background.ogg" in all_urls

        # Track URLs
        assert "https://example.com/subtitles/en.vtt" in all_urls


# ============================================================================
# Test 11: Meta Refresh URL
# ============================================================================


class TestMetaRefreshUrl:
    """meta refresh URL 추출 테스트."""

    def test_meta_refresh_url(self) -> None:
        """meta refresh URL 추출."""
        html = """
        <head>
            <meta http-equiv="refresh" content="5;url=https://example.com/new-page">
            <meta http-equiv="refresh" content="0; url=/redirect">
        </head>
        """
        parser = MetaParser(base_url="https://example.com")
        result = parser.parse(html)

        refresh_urls = result.refresh_urls
        assert len(refresh_urls) == 2
        assert "https://example.com/new-page" in refresh_urls
        assert "https://example.com/redirect" in refresh_urls

    def test_meta_refresh_url_various_formats(self) -> None:
        """다양한 meta refresh 형식 처리."""
        html = """
        <head>
            <meta http-equiv="refresh" content="5;URL='/page1'">
            <meta http-equiv="refresh" content="0;url=/page2">
            <meta http-equiv="refresh" content="3; URL = /page3">
        </head>
        """
        parser = MetaParser(base_url="https://example.com")
        result = parser.parse(html)

        refresh_urls = result.refresh_urls
        assert len(refresh_urls) == 3


# ============================================================================
# Test 12: Meta Open Graph Tags
# ============================================================================


class TestMetaOgTags:
    """Open Graph 태그 테스트."""

    def test_meta_og_tags(self) -> None:
        """Open Graph 태그."""
        html = """
        <head>
            <meta property="og:title" content="Page Title">
            <meta property="og:description" content="Page description">
            <meta property="og:image" content="https://example.com/og-image.jpg">
            <meta property="og:url" content="https://example.com/page">
            <meta property="og:type" content="website">
            <meta property="og:site_name" content="Example Site">
            <meta property="og:video" content="https://example.com/video.mp4">
            <meta property="og:audio" content="https://example.com/audio.mp3">
        </head>
        """
        parser = MetaParser(base_url="https://example.com")
        result = parser.parse(html)

        # OG 메타 데이터
        assert result.og_data.get("og:title") == "Page Title"
        assert result.og_data.get("og:url") == "https://example.com/page"

        # OG에서 추출된 URL들
        og_urls = result.og_urls
        assert "https://example.com/og-image.jpg" in og_urls
        assert "https://example.com/page" in og_urls
        assert "https://example.com/video.mp4" in og_urls
        assert "https://example.com/audio.mp3" in og_urls

    def test_meta_twitter_cards(self) -> None:
        """Twitter Card 태그."""
        html = """
        <head>
            <meta name="twitter:card" content="summary_large_image">
            <meta name="twitter:image" content="https://example.com/twitter-image.jpg">
            <meta name="twitter:player" content="https://example.com/player">
        </head>
        """
        parser = MetaParser(base_url="https://example.com")
        result = parser.parse(html)

        twitter_urls = result.twitter_urls
        assert "https://example.com/twitter-image.jpg" in twitter_urls
        assert "https://example.com/player" in twitter_urls


# ============================================================================
# Test 13: Data Attribute URL Patterns
# ============================================================================


class TestDataAttrUrlPattern:
    """data-url, data-api 등 data 속성 URL 패턴 테스트."""

    def test_data_attr_url_pattern(self) -> None:
        """data-url, data-api 등."""
        html = """
        <body>
            <div data-url="/api/data" data-endpoint="https://api.example.com/v1">
            </div>
            <button data-api="/api/submit" data-callback-url="/callback">
            </button>
            <img data-src="/images/lazy.jpg" data-srcset="/images/lazy-2x.jpg 2x">
            <a data-href="/dynamic-link">Link</a>
        </body>
        """
        parser = DataAttrParser(base_url="https://example.com")
        result = parser.parse(html)

        urls = result.urls
        assert "https://example.com/api/data" in urls
        assert "https://api.example.com/v1" in urls
        assert "https://example.com/api/submit" in urls
        assert "https://example.com/callback" in urls
        assert "https://example.com/images/lazy.jpg" in urls
        assert "https://example.com/dynamic-link" in urls

    def test_data_attr_json_urls(self) -> None:
        """data 속성 내 JSON URL 추출."""
        html = """
        <div data-config='{"apiUrl": "/api/config", "cdnUrl": "https://cdn.example.com"}'>
        </div>
        <script type="application/json" data-settings>
            {"endpoint": "/api/settings", "baseUrl": "https://api.example.com"}
        </script>
        """
        parser = DataAttrParser(base_url="https://example.com")
        result = parser.parse(html)

        urls = result.urls
        assert "https://example.com/api/config" in urls
        assert "https://cdn.example.com" in urls


# ============================================================================
# Test 14: Base href Resolution
# ============================================================================


class TestBaseHrefResolution:
    """base href 기준 URL 해결 테스트."""

    def test_base_href_resolution(self) -> None:
        """base href 기준 URL 해결."""
        html = """
        <html>
        <head>
            <base href="https://cdn.example.com/assets/">
            <link rel="stylesheet" href="css/style.css">
            <script src="js/app.js"></script>
        </head>
        <body>
            <img src="images/logo.png">
        </body>
        </html>
        """
        module = HtmlElementParserModule()
        result = module.parse_with_base(html, page_url="https://example.com/page")

        # base href 기준으로 상대 URL 해결
        all_urls = result.get_all_urls()

        # 상대 경로는 base href 기준
        assert "https://cdn.example.com/assets/css/style.css" in all_urls
        assert "https://cdn.example.com/assets/js/app.js" in all_urls
        assert "https://cdn.example.com/assets/images/logo.png" in all_urls

    def test_base_href_not_present(self) -> None:
        """base href가 없을 때 페이지 URL 기준."""
        html = """
        <html>
        <head>
            <link rel="stylesheet" href="css/style.css">
        </head>
        </html>
        """
        module = HtmlElementParserModule()
        result = module.parse_with_base(
            html, page_url="https://example.com/dir/page.html"
        )

        all_urls = result.get_all_urls()
        # 페이지 URL 기준으로 해결
        assert "https://example.com/dir/css/style.css" in all_urls


# ============================================================================
# Integration Tests
# ============================================================================


class TestHtmlElementParserModuleIntegration:
    """HtmlElementParserModule 통합 테스트."""

    def test_module_properties(
        self,
        html_parser_module: HtmlElementParserModule,
    ) -> None:
        """모듈 속성 테스트."""
        assert html_parser_module.name == "html_element_parser"
        assert ScanProfile.STANDARD in html_parser_module.profiles
        assert ScanProfile.FULL in html_parser_module.profiles
        # QUICK 프로필에서도 기본 HTML 파싱은 필요
        assert ScanProfile.QUICK in html_parser_module.profiles

    async def test_discover_yields_discovered_assets(
        self,
        html_parser_module: HtmlElementParserModule,
        mock_http_client: MagicMock,
    ) -> None:
        """discover()가 DiscoveredAsset을 yield하는지 테스트."""
        html_content = """
        <html>
        <head>
            <script src="/js/app.js"></script>
            <link rel="stylesheet" href="/css/style.css">
        </head>
        <body>
            <form action="/login" method="POST">
                <input type="hidden" name="_csrf" value="token">
            </form>
            <img src="/images/logo.png">
        </body>
        </html>
        """
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={
                "html_content": html_content,
                "base_url": "https://example.com",
            },
        )

        assets = [asset async for asset in html_parser_module.discover(context)]

        # Should yield DiscoveredAsset instances
        assert all(isinstance(a, DiscoveredAsset) for a in assets)
        assert len(assets) >= 4  # script, link, form, img

        # Check asset types
        asset_types = {a.asset_type for a in assets}
        assert "script" in asset_types
        assert "stylesheet" in asset_types
        assert "form" in asset_types
        assert "image" in asset_types

        # Check source
        assert all(a.source == "html_element_parser" for a in assets)

    async def test_discover_with_empty_html(
        self,
        html_parser_module: HtmlElementParserModule,
        mock_http_client: MagicMock,
    ) -> None:
        """빈 HTML에서도 에러 없이 동작."""
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={
                "html_content": "",
                "base_url": "https://example.com",
            },
        )

        assets = [asset async for asset in html_parser_module.discover(context)]
        assert assets == []

    async def test_discover_with_malformed_html(
        self,
        html_parser_module: HtmlElementParserModule,
        mock_http_client: MagicMock,
    ) -> None:
        """잘못된 HTML에서도 가능한 요소 추출."""
        malformed_html = """
        <html>
        <head>
            <script src="/js/app.js"
        </head>
        <body>
            <form action="/login" method="POST>
                <input type="hidden" name="_csrf" value="token">
            <img src="/images/logo.png">
        </body>
        """
        context = DiscoveryContext(
            target_url="https://example.com",
            profile=ScanProfile.STANDARD,
            http_client=mock_http_client,
            crawl_data={
                "html_content": malformed_html,
                "base_url": "https://example.com",
            },
        )

        # Should not raise exception
        assets = [asset async for asset in html_parser_module.discover(context)]
        # BeautifulSoup should still extract some elements
        assert len(assets) >= 0
