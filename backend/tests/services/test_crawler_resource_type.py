"""
Phase 1: CrawlerService resource_type 캡처 테스트.

TDD RED Phase: resource_type 캡처를 검증하는 테스트.
Playwright Request.resource_type이 http_data에 포함되는지 확인.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.crawler_service import CrawlerService


def create_mock_playwright_context(
    mock_requests: list[dict] | None = None,
) -> MagicMock:
    """Playwright context mock 생성 헬퍼.

    Args:
        mock_requests: Mock request 정보 리스트.
            각 dict는 {url, method, resource_type, headers, post_data} 포함.

    Returns:
        async_playwright() mock 객체.
    """
    if mock_requests is None:
        mock_requests = []

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

    # page.locator("a").all() - 빈 링크 반환
    mock_locator = AsyncMock()
    mock_locator.all.return_value = []
    mock_page.locator = MagicMock(return_value=mock_locator)

    # page.on() 핸들러 캡처
    captured_handlers: dict[str, callable] = {}

    def capture_handler(event_name: str, handler: callable) -> None:
        captured_handlers[event_name] = handler

    mock_page.on = MagicMock(side_effect=capture_handler)

    # page.goto() 시 request 이벤트 트리거
    async def trigger_requests(*args, **kwargs) -> None:
        if "request" in captured_handlers:
            for req_info in mock_requests:
                mock_request = MagicMock()
                mock_request.url = req_info.get("url", "http://example.com/api")
                mock_request.method = req_info.get("method", "GET")
                mock_request.resource_type = req_info.get("resource_type", "document")
                mock_request.headers = req_info.get("headers", {})
                mock_request.post_data = req_info.get("post_data", None)
                await captured_handlers["request"](mock_request)

    mock_page.goto = AsyncMock(side_effect=trigger_requests)

    return mock_playwright_ctx


@pytest.mark.asyncio
async def test_crawl_captures_resource_type():
    """CrawlerService가 request의 resource_type을 캡처하는지 확인.

    TDD RED: 현재 구현에서는 resource_type이 캡처되지 않아 실패해야 함.
    """
    # Given
    mock_requests = [
        {
            "url": "http://example.com/",
            "method": "GET",
            "resource_type": "document",
            "headers": {"accept": "text/html"},
        }
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context(mock_requests),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, _ = await crawler.crawl("http://example.com")

        # Then
        assert "http://example.com/" in http_data
        request_data = http_data["http://example.com/"].get("request", {})

        # RED: 이 assertion은 현재 실패해야 함
        assert (
            "resource_type" in request_data
        ), "resource_type이 http_data에 캡처되어야 함"
        assert request_data["resource_type"] == "document"


@pytest.mark.asyncio
async def test_xhr_request_has_correct_resource_type():
    """XHR 요청의 resource_type이 'xhr'로 캡처되는지 확인.

    TDD RED: XHR 요청이 resource_type="xhr"로 캡처되어야 함.
    """
    # Given
    mock_requests = [
        {
            "url": "http://example.com/api/users",
            "method": "POST",
            "resource_type": "xhr",
            "headers": {"content-type": "application/json"},
            "post_data": '{"name": "test"}',
        }
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context(mock_requests),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, _ = await crawler.crawl("http://example.com")

        # Then
        assert "http://example.com/api/users" in http_data
        request_data = http_data["http://example.com/api/users"].get("request", {})

        # RED: 이 assertion은 현재 실패해야 함
        assert (
            "resource_type" in request_data
        ), "XHR 요청의 resource_type이 캡처되어야 함"
        assert (
            request_data["resource_type"] == "xhr"
        ), "XHR 요청은 resource_type='xhr'이어야 함"


@pytest.mark.asyncio
async def test_fetch_request_has_correct_resource_type():
    """Fetch 요청의 resource_type이 'fetch'로 캡처되는지 확인.

    TDD RED: Fetch 요청이 resource_type="fetch"로 캡처되어야 함.
    """
    # Given
    mock_requests = [
        {
            "url": "http://example.com/api/data",
            "method": "GET",
            "resource_type": "fetch",
            "headers": {"accept": "application/json"},
        }
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context(mock_requests),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, _ = await crawler.crawl("http://example.com")

        # Then
        assert "http://example.com/api/data" in http_data
        request_data = http_data["http://example.com/api/data"].get("request", {})

        # RED: 이 assertion은 현재 실패해야 함
        assert (
            "resource_type" in request_data
        ), "Fetch 요청의 resource_type이 캡처되어야 함"
        assert (
            request_data["resource_type"] == "fetch"
        ), "Fetch 요청은 resource_type='fetch'이어야 함"


@pytest.mark.asyncio
async def test_multiple_requests_with_different_resource_types():
    """여러 요청이 각각의 resource_type으로 캡처되는지 확인.

    TDD RED: 다양한 resource_type이 각각 올바르게 캡처되어야 함.
    """
    # Given
    mock_requests = [
        {
            "url": "http://example.com/",
            "method": "GET",
            "resource_type": "document",
        },
        {
            "url": "http://example.com/api/users",
            "method": "POST",
            "resource_type": "xhr",
        },
        {
            "url": "http://example.com/api/config",
            "method": "GET",
            "resource_type": "fetch",
        },
        {
            "url": "http://example.com/script.js",
            "method": "GET",
            "resource_type": "script",
        },
    ]

    with patch(
        "app.services.crawler_service.async_playwright",
        create_mock_playwright_context(mock_requests),
    ):
        crawler = CrawlerService()

        # When
        links, http_data, _ = await crawler.crawl("http://example.com")

        # Then
        expected_types = {
            "http://example.com/": "document",
            "http://example.com/api/users": "xhr",
            "http://example.com/api/config": "fetch",
            "http://example.com/script.js": "script",
        }

        for url, expected_type in expected_types.items():
            assert url in http_data, f"{url}이 http_data에 있어야 함"
            request_data = http_data[url].get("request", {})

            # RED: 이 assertion은 현재 실패해야 함
            assert (
                "resource_type" in request_data
            ), f"{url}의 resource_type이 캡처되어야 함"
            assert (
                request_data["resource_type"] == expected_type
            ), f"{url}의 resource_type이 '{expected_type}'이어야 함"


@pytest.mark.asyncio
async def test_resource_type_with_missing_attribute():
    """resource_type 속성이 없는 경우 안전하게 처리되는지 확인.

    TDD RED: resource_type이 없어도 에러 없이 처리되어야 함.
    """
    # Given - resource_type 속성이 없는 Mock request
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

    async def trigger_requests(*args, **kwargs) -> None:
        if "request" in captured_handlers:
            # resource_type 속성이 없는 Mock
            mock_request = MagicMock(spec=["url", "method", "headers", "post_data"])
            mock_request.url = "http://example.com/legacy"
            mock_request.method = "GET"
            mock_request.headers = {}
            mock_request.post_data = None
            await captured_handlers["request"](mock_request)

    mock_page.goto = AsyncMock(side_effect=trigger_requests)

    with patch(
        "app.services.crawler_service.async_playwright",
        mock_playwright_ctx,
    ):
        crawler = CrawlerService()

        # When - 에러 없이 실행되어야 함
        links, http_data, _ = await crawler.crawl("http://example.com")

        # Then - 데이터가 캡처되어야 함 (resource_type은 빈 문자열 또는 기본값)
        assert "http://example.com/legacy" in http_data
        request_data = http_data["http://example.com/legacy"].get("request", {})
        assert "method" in request_data
        # resource_type은 빈 문자열 또는 기본값으로 처리
        resource_type = request_data.get("resource_type", "")
        assert resource_type == "" or resource_type is not None
