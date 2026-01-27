"""
Phase 2: CrawlerService JavaScript Content 수집 테스트.

TDD RED Phase: JS 파일 content 수집을 검증하는 테스트.
외부 JS 파일과 인라인 스크립트의 content가 수집되는지 확인.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.crawler_service import CrawlerService


def create_mock_playwright_context_with_js(
    mock_requests: list[dict] | None = None,
    mock_responses: list[dict] | None = None,
    inline_scripts: list[str] | None = None,
) -> MagicMock:
    """Playwright context mock 생성 헬퍼 (JS content 수집용).

    Args:
        mock_requests: Mock request 정보 리스트.
            각 dict는 {url, method, resource_type, headers, post_data} 포함.
        mock_responses: Mock response 정보 리스트.
            각 dict는 {url, status, headers, body} 포함.
        inline_scripts: 인라인 스크립트 content 리스트.

    Returns:
        async_playwright() mock 객체.
    """
    if mock_requests is None:
        mock_requests = []
    if mock_responses is None:
        mock_responses = []
    if inline_scripts is None:
        inline_scripts = []

    mock_playwright_ctx = MagicMock()
    mock_context_manager = AsyncMock()
    mock_playwright_ctx.return_value = mock_context_manager

    mock_p = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_p

    mock_browser = AsyncMock()
    mock_p.chromium.launch.return_value = mock_browser

    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page

    # page.locator() 설정
    def create_locator(selector: str) -> MagicMock:
        mock_locator = AsyncMock()
        if selector == "a":
            # 링크 locator - 빈 반환
            mock_locator.all.return_value = []
        elif selector == "script:not([src])":
            # 인라인 스크립트 locator
            script_elements = []
            for content in inline_scripts:
                script_elem = AsyncMock()
                script_elem.text_content = AsyncMock(return_value=content)
                script_elements.append(script_elem)
            mock_locator.all.return_value = script_elements
        else:
            mock_locator.all.return_value = []
        return mock_locator

    mock_page.locator = MagicMock(side_effect=create_locator)

    # page.on() 핸들러 캡처
    captured_handlers: dict[str, callable] = {}

    def capture_handler(event_name: str, handler: callable) -> None:
        captured_handlers[event_name] = handler

    mock_page.on = MagicMock(side_effect=capture_handler)

    # page.goto() 시 request/response 이벤트 트리거
    async def trigger_events(*args, **kwargs) -> None:
        # Request 이벤트 트리거
        if "request" in captured_handlers:
            for req_info in mock_requests:
                mock_request = MagicMock()
                mock_request.url = req_info.get("url", "http://example.com/")
                mock_request.method = req_info.get("method", "GET")
                mock_request.resource_type = req_info.get("resource_type", "document")
                mock_request.headers = req_info.get("headers", {})
                mock_request.post_data = req_info.get("post_data", None)
                await captured_handlers["request"](mock_request)

        # Response 이벤트 트리거
        if "response" in captured_handlers:
            for resp_info in mock_responses:
                mock_response = MagicMock()
                mock_response.url = resp_info.get("url", "http://example.com/")
                mock_response.status = resp_info.get("status", 200)
                mock_response.headers = resp_info.get("headers", {})
                body_bytes = resp_info.get("body", b"")
                if isinstance(body_bytes, str):
                    body_bytes = body_bytes.encode("utf-8")
                mock_response.body = AsyncMock(return_value=body_bytes)
                await captured_handlers["response"](mock_response)

    mock_page.goto = AsyncMock(side_effect=trigger_events)

    return mock_playwright_ctx


# ============================================================================
# 기본 테스트 4개 (Phase 2 문서 명시)
# ============================================================================


@pytest.mark.asyncio
async def test_crawl_returns_js_contents():
    """CrawlerService.crawl()이 js_contents를 반환하는지 확인.

    TDD RED: crawl() 반환값이 3개여야 함.
    """
    # Given
    mock_requests = [
        {"url": "http://example.com/", "method": "GET", "resource_type": "document"}
    ]
    mock_responses = [
        {
            "url": "http://example.com/",
            "status": 200,
            "headers": {"content-type": "text/html"},
            "body": b"<html></html>",
        }
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js(mock_requests, mock_responses),
    ):
        crawler = CrawlerService()

        # When
        result = await crawler.crawl("http://example.com")

        # Then
        assert (
            len(result) == 3
        ), "crawl() should return 3 values (links, http_data, js_contents)"
        links, http_data, js_contents = result
        assert isinstance(links, list), "links should be a list"
        assert isinstance(http_data, dict), "http_data should be a dict"
        assert isinstance(js_contents, list), "js_contents should be a list"


@pytest.mark.asyncio
async def test_crawl_collects_js_file_content():
    """JavaScript 파일의 URL과 content가 수집되는지 확인.

    TDD RED: .js 파일의 content가 js_contents에 포함되어야 함.
    """
    # Given
    js_code = "function hello() { console.log('Hello'); }"
    mock_requests = [
        {"url": "http://example.com/", "method": "GET", "resource_type": "document"},
        {
            "url": "http://example.com/app.js",
            "method": "GET",
            "resource_type": "script",
        },
    ]
    mock_responses = [
        {
            "url": "http://example.com/",
            "status": 200,
            "headers": {"content-type": "text/html"},
            "body": b"<html></html>",
        },
        {
            "url": "http://example.com/app.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": js_code.encode("utf-8"),
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js(mock_requests, mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        assert len(js_contents) > 0, "No JS contents collected"
        js_urls = [js["url"] for js in js_contents]
        assert "http://example.com/app.js" in js_urls, "app.js not in js_contents"

        app_js = next(
            js for js in js_contents if js["url"] == "http://example.com/app.js"
        )
        assert "content" in app_js, "JS content missing 'content'"
        assert app_js["content"] == js_code, "JS content mismatch"
        assert (
            app_js.get("is_inline") is False
        ), "External JS should have is_inline=False"


@pytest.mark.asyncio
async def test_crawl_collects_inline_script_content():
    """인라인 <script> 태그의 content가 수집되는지 확인.

    TDD RED: 인라인 스크립트가 js_contents에 포함되어야 함.
    """
    # Given
    inline_js = "fetch('/api/users', { method: 'POST' });"
    mock_requests = [
        {"url": "http://example.com/", "method": "GET", "resource_type": "document"}
    ]
    mock_responses = [
        {
            "url": "http://example.com/",
            "status": 200,
            "headers": {"content-type": "text/html"},
            "body": b"<html></html>",
        }
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js(
            mock_requests, mock_responses, inline_scripts=[inline_js]
        ),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        inline_scripts = [js for js in js_contents if js.get("is_inline") is True]
        assert len(inline_scripts) > 0, "No inline scripts collected"
        assert (
            inline_scripts[0]["content"] == inline_js
        ), "Inline script content mismatch"
        assert "source_url" in inline_scripts[0], "Inline script missing source_url"


@pytest.mark.asyncio
async def test_crawl_identifies_js_by_content_type():
    """Content-Type이 application/javascript인 파일이 수집되는지 확인.

    TDD RED: .js 확장자가 없어도 Content-Type으로 JS 파일 식별.
    """
    # Given - .js 확장자 없지만 Content-Type이 javascript인 URL
    js_code = "var config = { api: '/api/v1' };"
    mock_requests = [
        {"url": "http://example.com/", "method": "GET", "resource_type": "document"},
        {
            "url": "http://example.com/config",
            "method": "GET",
            "resource_type": "script",
        },
    ]
    mock_responses = [
        {
            "url": "http://example.com/",
            "status": 200,
            "headers": {"content-type": "text/html"},
            "body": b"<html></html>",
        },
        {
            "url": "http://example.com/config",
            "status": 200,
            "headers": {"content-type": "application/javascript; charset=utf-8"},
            "body": js_code.encode("utf-8"),
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js(mock_requests, mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        js_urls = [js["url"] for js in js_contents]
        assert (
            "http://example.com/config" in js_urls
        ), "JS file not identified by Content-Type"

        config_js = next(
            js for js in js_contents if js["url"] == "http://example.com/config"
        )
        assert "javascript" in config_js.get("content_type", "").lower()


# ============================================================================
# 엣지 케이스 테스트 8개 (추가 권장)
# ============================================================================


@pytest.mark.asyncio
async def test_crawl_deduplicates_js_contents():
    """동일 URL의 JS 파일이 중복 수집되지 않는지 확인.

    TDD RED: 같은 URL의 JS가 여러 번 응답되어도 1번만 수집.
    """
    # Given - 동일 URL 2번 응답
    js_code = "console.log('test');"
    mock_requests = [
        {
            "url": "http://example.com/app.js",
            "method": "GET",
            "resource_type": "script",
        },
        {
            "url": "http://example.com/app.js",
            "method": "GET",
            "resource_type": "script",
        },
    ]
    mock_responses = [
        {
            "url": "http://example.com/app.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": js_code,
        },
        {
            "url": "http://example.com/app.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": js_code,
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js(mock_requests, mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        js_urls = [js["url"] for js in js_contents]
        assert (
            js_urls.count("http://example.com/app.js") == 1
        ), "Duplicate JS URL collected"


@pytest.mark.asyncio
async def test_crawl_handles_empty_js_file():
    """빈 JS 파일이 올바르게 처리되는지 확인.

    TDD RED: 빈 JS 파일도 수집되어야 함 (content가 빈 문자열).
    """
    # Given
    mock_responses = [
        {
            "url": "http://example.com/empty.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": b"",
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        empty_js = [
            js for js in js_contents if js["url"] == "http://example.com/empty.js"
        ]
        assert len(empty_js) == 1, "Empty JS file not collected"
        assert empty_js[0]["content"] == "", "Empty JS content should be empty string"


@pytest.mark.asyncio
async def test_crawl_truncates_large_js_content():
    """대용량 JS 파일이 크기 제한으로 잘리는지 확인.

    TDD RED: MAX_JS_CONTENT_SIZE 초과 시 truncate.
    """
    # Given - 6MB JS 파일 (MAX_JS_CONTENT_SIZE = 5MB)
    large_js = "x" * (6 * 1024 * 1024)
    mock_responses = [
        {
            "url": "http://example.com/large.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": large_js.encode("utf-8"),
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        large_js_content = next(
            (js for js in js_contents if js["url"] == "http://example.com/large.js"),
            None,
        )
        assert large_js_content is not None, "Large JS file not collected"
        # 5MB 제한 확인
        assert (
            len(large_js_content["content"]) <= 5 * 1024 * 1024
        ), "JS content not truncated"


@pytest.mark.asyncio
async def test_crawl_handles_invalid_utf8_js():
    """UTF-8이 아닌 인코딩의 JS 파일이 처리되는지 확인.

    TDD RED: 잘못된 인코딩도 에러 없이 처리 (errors='ignore').
    """
    # Given - 잘못된 UTF-8 바이트
    invalid_utf8 = b"var x = '\xff\xfe invalid';"
    mock_responses = [
        {
            "url": "http://example.com/invalid.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": invalid_utf8,
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], mock_responses),
    ):
        crawler = CrawlerService()

        # When - 에러 없이 실행되어야 함
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        invalid_js = next(
            (js for js in js_contents if js["url"] == "http://example.com/invalid.js"),
            None,
        )
        assert invalid_js is not None, "Invalid UTF-8 JS file not collected"
        assert isinstance(invalid_js["content"], str), "Content should be string"


@pytest.mark.asyncio
async def test_crawl_skips_empty_inline_scripts():
    """빈 인라인 스크립트가 스킵되는지 확인.

    TDD RED: 공백만 있는 인라인 스크립트는 수집하지 않음.
    """
    # Given - 빈 스크립트와 공백 스크립트
    inline_scripts = [
        "",  # 빈 스크립트
        "   ",  # 공백만 있는 스크립트
        "\n\t\n",  # 개행/탭만 있는 스크립트
        "console.log('valid');",  # 유효한 스크립트
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], [], inline_scripts),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        inline_contents = [js for js in js_contents if js.get("is_inline") is True]
        assert len(inline_contents) == 1, "Only valid inline script should be collected"
        assert "console.log" in inline_contents[0]["content"]


@pytest.mark.asyncio
async def test_crawl_handles_response_body_error():
    """response.body() 호출 실패 시 에러 처리 확인.

    TDD RED: body() 예외 발생 시 해당 JS만 스킵하고 계속 진행.
    """
    # Given - body() 호출 시 예외 발생
    mock_playwright_ctx = MagicMock()
    mock_context_manager = AsyncMock()
    mock_playwright_ctx.return_value = mock_context_manager

    mock_p = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_p

    mock_browser = AsyncMock()
    mock_p.chromium.launch.return_value = mock_browser

    mock_context = AsyncMock()
    mock_browser.new_context.return_value = mock_context

    mock_page = AsyncMock()
    mock_context.new_page.return_value = mock_page

    mock_locator = AsyncMock()
    mock_locator.all.return_value = []
    mock_page.locator = MagicMock(return_value=mock_locator)

    captured_handlers: dict[str, callable] = {}

    def capture_handler(event_name: str, handler: callable) -> None:
        captured_handlers[event_name] = handler

    mock_page.on = MagicMock(side_effect=capture_handler)

    async def trigger_events(*args, **kwargs) -> None:
        if "response" in captured_handlers:
            # 첫 번째 응답: body() 실패
            mock_response1 = MagicMock()
            mock_response1.url = "http://example.com/error.js"
            mock_response1.status = 200
            mock_response1.headers = {"content-type": "application/javascript"}
            mock_response1.body = AsyncMock(side_effect=Exception("Network error"))
            await captured_handlers["response"](mock_response1)

            # 두 번째 응답: 정상
            mock_response2 = MagicMock()
            mock_response2.url = "http://example.com/ok.js"
            mock_response2.status = 200
            mock_response2.headers = {"content-type": "application/javascript"}
            mock_response2.body = AsyncMock(return_value=b"console.log('ok');")
            await captured_handlers["response"](mock_response2)

    mock_page.goto = AsyncMock(side_effect=trigger_events)

    with patch("app.services.crawler_service.async_playwright", mock_playwright_ctx):
        crawler = CrawlerService()

        # When - 에러 없이 실행되어야 함
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then - ok.js만 수집되어야 함
        js_urls = [js["url"] for js in js_contents]
        assert (
            "http://example.com/error.js" not in js_urls
        ), "Failed JS should be skipped"
        assert (
            "http://example.com/ok.js" in js_urls
        ), "Successful JS should be collected"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "content_type",
    [
        "application/javascript",
        "text/javascript",
        "application/x-javascript",
        "application/javascript; charset=utf-8",
        "text/javascript; charset=UTF-8",
    ],
)
async def test_crawl_js_content_type_variations(content_type: str):
    """다양한 JavaScript Content-Type이 인식되는지 확인.

    TDD RED: 여러 Content-Type 변형 모두 JS로 인식.
    """
    # Given
    js_code = "var x = 1;"
    mock_responses = [
        {
            "url": "http://example.com/script",
            "status": 200,
            "headers": {"content-type": content_type},
            "body": js_code.encode("utf-8"),
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        js_urls = [js["url"] for js in js_contents]
        assert (
            "http://example.com/script" in js_urls
        ), f"JS with Content-Type '{content_type}' not collected"


@pytest.mark.asyncio
async def test_crawl_js_content_with_sourcemap():
    """Sourcemap URL을 포함한 JS 파일 처리 확인.

    TDD RED: //# sourceMappingURL이 있는 JS도 정상 수집.
    """
    # Given
    js_code = """
function hello() {
    console.log('Hello');
}
//# sourceMappingURL=app.js.map
"""
    mock_responses = [
        {
            "url": "http://example.com/app.js",
            "status": 200,
            "headers": {"content-type": "application/javascript"},
            "body": js_code.encode("utf-8"),
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context_with_js([], mock_responses),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, js_contents = await crawler.crawl("http://example.com")

        # Then
        app_js = next(
            (js for js in js_contents if js["url"] == "http://example.com/app.js"),
            None,
        )
        assert app_js is not None, "JS with sourcemap not collected"
        assert "sourceMappingURL" in app_js["content"], "Sourcemap should be preserved"
